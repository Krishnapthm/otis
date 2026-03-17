"""
Two-Layer Retrieval Service
============================

Implements concept-aware document retrieval for RAG in the chat endpoint.

**Layer 1 — Concept Matching:**
  Embeds the user query, then searches ``document_concepts`` by cosine
  similarity to find the top-K most relevant concepts among the mentioned
  documents.  This narrows the search scope from "all chunks" to "chunks
  belonging to matched concepts".

**Layer 2 — Chunk Retrieval:**
  Runs PGVector similarity search on the user's chunk collection, filtered
  by ``document_id`` (from mentions).  Matched concept summaries are used to
  augment the search query so that chunk retrieval is topically focused.
  Results are deduplicated and returned.

**Fallback:**
  If no concepts score above the threshold (or ``document_concepts`` is empty
  for the given docs), retrieval falls back to plain similarity search
  filtered only by ``document_id``.

Usage::

    from src.services.retrieval_service import retrieve_with_concepts

    docs = await retrieve_with_concepts(
        query="Explain eigenvalues",
        doc_ids=[uuid.UUID("...")],
        user_id="abc-123",
        db=async_session,
        embedding_model=OllamaEmbeddings(model="nomic-embed-text"),
    )
"""

import asyncio
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_postgres import PGVector
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Number of top concepts to match in Layer 1
CONCEPT_TOP_K = 3

# Minimum cosine similarity score (0–1) to accept a concept match.
# Below this threshold, retrieval falls back to unscoped similarity.
CONCEPT_SCORE_THRESHOLD = 0.3

# Total cap on returned chunks (after dedup)
MAX_CHUNKS = settings.max_retrieved_chunks

# PGVector connection string (sync driver — retrieval runs in executor)
_PG_CONNECTION = os.getenv(
    "RETRIEVAL_DATABASE_URL",
    os.getenv(
        "REDIS_DATABASE_URL",
        "postgresql+psycopg://user:password@db:5432/otis",
    ),
)


# ---------------------------------------------------------------------------
# Layer 1 — Concept matching via SQL + pgvector
# ---------------------------------------------------------------------------


async def _match_concepts(
    query_embedding: List[float],
    doc_ids: List[uuid.UUID],
    db: AsyncSession,
    top_k: int = CONCEPT_TOP_K,
    threshold: float = CONCEPT_SCORE_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Find the top-K concepts whose embeddings are most similar to the query.

    Args:
        query_embedding: The embedded query vector.
        doc_ids:         Document UUIDs to scope the search.
        db:              Async SQLAlchemy session.
        top_k:           Max concepts to return.
        threshold:       Minimum similarity (1 - cosine distance).

    Returns:
        List of dicts: ``{"concept_name", "concept_summary", "score"}``.
        Empty list if no concepts exist or none exceed threshold.
    """
    if not doc_ids:
        return []

    # Cast the query vector to a pgvector-compatible literal
    vec_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"
    doc_id_literals = ", ".join(f"'{str(d)}'" for d in doc_ids)

    query = sa_text(
        f"""
        SELECT
            concept_name,
            concept_summary,
            1 - (concept_embedding <=> :vec ::vector) AS score
        FROM document_concepts
        WHERE document_id IN ({doc_id_literals})
          AND concept_embedding IS NOT NULL
        ORDER BY concept_embedding <=> :vec ::vector
        LIMIT :top_k
    """
    )

    result = await db.execute(
        query,
        {"vec": vec_literal, "top_k": top_k},
    )
    rows = result.fetchall()

    matches = [
        {
            "concept_name": row.concept_name,
            "concept_summary": row.concept_summary,
            "score": float(row.score),
        }
        for row in rows
        if row.score >= threshold
    ]

    logger.info(
        "Layer 1: matched %d concepts (top score: %.3f) for %d docs",
        len(matches),
        matches[0]["score"] if matches else 0.0,
        len(doc_ids),
    )
    return matches


# ---------------------------------------------------------------------------
# Layer 2 — Chunk retrieval via PGVector with metadata filters
# ---------------------------------------------------------------------------


def _retrieve_chunks_sync(
    query: str,
    doc_ids: List[uuid.UUID],
    concept_summaries: Optional[List[str]],
    collection_name: str,
    embedding_model: Any,
    k: int = MAX_CHUNKS,
) -> List[Document]:
    """
    Synchronous PGVector retrieval filtered by document_id.

    When concept summaries are available from Layer 1, they are appended
    to the query to steer the embedding search toward the matched topics.
    Runs in a thread executor from the async context.

    Args:
        query:             The raw query text.
        doc_ids:           Document IDs to filter by.
        concept_summaries: Matched concept summaries to augment the query
                           (None = use query as-is).
        collection_name:   PGVector collection (e.g. ``user_{user_id}``).
        embedding_model:   Langchain embeddings instance.
        k:                 Number of chunks to retrieve.

    Returns:
        List of langchain Document objects.
    """
    vector_store = PGVector(
        embeddings=embedding_model,
        collection_name=collection_name,
        connection=_PG_CONNECTION,
    )

    # Build metadata filter — scope to mentioned documents only
    doc_id_strs = [str(d) for d in doc_ids]
    metadata_filter: Dict[str, Any] = {
        "document_id": {"$in": doc_id_strs},
    }

    # Augment the query with concept summaries for better semantic targeting
    search_query = query
    if concept_summaries:
        context_hint = "; ".join(concept_summaries)
        search_query = f"{query}\n\nRelevant topics: {context_hint}"

    retriever = vector_store.as_retriever(
        search_kwargs={"filter": metadata_filter, "k": k}
    )
    return retriever.invoke(search_query)


def _deduplicate_chunks(
    docs: List[Document], max_chunks: int = MAX_CHUNKS
) -> List[Document]:
    """Remove duplicate chunks by content hash, keeping highest-ranked first."""
    seen = set()
    unique = []
    for doc in docs:
        content_key = doc.page_content[:200]  # Use first 200 chars as dedup key
        if content_key not in seen:
            seen.add(content_key)
            unique.append(doc)
        if len(unique) >= max_chunks:
            break
    return unique


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def retrieve_with_concepts(
    query: str,
    doc_ids: List[uuid.UUID],
    user_id: str,
    db: AsyncSession,
    embedding_model: Any,
) -> List[Document]:
    """
    Two-layer concept-aware retrieval.

    1. Embed the query and find matching concepts in ``document_concepts``.
    2. Retrieve chunks from PGVector filtered by document IDs, using
       matched concept summaries to augment the search query.
    3. Deduplicate and return.

    Falls back to plain similarity search if no concepts match.

    Args:
        query:           User's message text.
        doc_ids:         Document UUIDs from the user's mentions.
        user_id:         The user's UUID string (for collection name derivation).
        db:              Async SQLAlchemy session.
        embedding_model: Langchain embeddings instance (e.g. OllamaEmbeddings).

    Returns:
        List of retrieved langchain Document objects, deduplicated, capped
        at :data:`MAX_CHUNKS`.
    """
    if not doc_ids:
        return []

    collection_name = f"user_{user_id}"
    loop = asyncio.get_running_loop()

    # --- Layer 1: Concept matching ---
    concept_summaries: List[str] = []
    try:
        query_embedding = await loop.run_in_executor(
            None, embedding_model.embed_query, query
        )
        concept_matches = await _match_concepts(query_embedding, doc_ids, db)
        concept_summaries = [m["concept_summary"] for m in concept_matches]
        matched_names = [m["concept_name"] for m in concept_matches]
    except Exception:
        logger.exception(
            "Layer 1 concept matching failed, falling back to direct retrieval"
        )
        matched_names = []

    if matched_names:
        logger.info("Layer 1 matched concepts: %s", matched_names)
    else:
        logger.info("No concept matches — using plain similarity retrieval")

    # --- Layer 2: Chunk retrieval (doc_id filter + concept-augmented query) ---
    try:
        docs = await loop.run_in_executor(
            None,
            _retrieve_chunks_sync,
            query,
            doc_ids,
            concept_summaries or None,
            collection_name,
            embedding_model,
        )
    except Exception:
        logger.exception("Layer 2 chunk retrieval failed")
        return []

    # Deduplicate and cap
    unique_docs = _deduplicate_chunks(docs)

    logger.info(
        "Retrieved %d chunks (%d before dedup) for query: %.80s...",
        len(unique_docs),
        len(docs),
        query,
    )
    return unique_docs


def format_retrieved_context(docs: List[Document]) -> str:
    """
    Format retrieved chunks into a context string for injection
    into the chat system message.

    Each chunk is separated by a divider and prefixed with its source filename.
    """
    if not docs:
        return ""

    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("file_name", "unknown")
        parts.append(f"--- Source: {source} (chunk {i}) ---\n{doc.page_content}")

    return "\n\n".join(parts)
