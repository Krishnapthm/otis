"""
Concept Extraction Service
===========================

Extracts key concepts from document markdown at embedding time
using a cheap LLM (gpt-4.1-nano), then:
  1. Tags each chunk with its matching concept names (metadata["concepts"])
  2. Stores concept rows with vector embeddings in `document_concepts`

This service is called from the embedding worker (`src/tasks/embedding_tasks.py`)
and is intentionally synchronous — the worker runs in an RQ job outside asyncio.

Extraction failure is **non-fatal**: if it fails, chunks are embedded without
concept tags and retrieval falls back to pure similarity search.
"""

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.api.db.models import DocumentConcept

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models for structured LLM output
# ---------------------------------------------------------------------------


class ExtractedConcept(BaseModel):
    """A single concept extracted from a document."""

    name: str = Field(description="Short concept name (2-5 words)")
    summary: str = Field(description="One-sentence summary, max 15 words")


class ExtractedConcepts(BaseModel):
    """Container returned by the concept-extraction LLM call."""

    concepts: List[ExtractedConcept] = Field(
        description="Key concepts from the document (max 10)"
    )


class ChunkConceptMapping(BaseModel):
    """Maps a chunk index to its relevant concept names."""

    chunk_index: int
    concept_names: List[str]


class ChunkConceptMappings(BaseModel):
    """Container returned by the chunk-classification LLM call."""

    mappings: List[ChunkConceptMapping]


# ---------------------------------------------------------------------------
# LLM setup  (cheap model — gpt-4.1-nano or gpt-4o-mini)
# ---------------------------------------------------------------------------


def _get_concept_llm() -> ChatOpenAI:
    """
    Returns a low-cost OpenAI model for concept extraction.
    Uses gpt-4.1-nano by default; falls back to gpt-4o-mini via env var.
    """
    return ChatOpenAI(
        model=os.getenv("CONCEPT_LLM_DEPLOYMENT", "gpt-4.1-nano"),
        temperature=0.0,
        max_completion_tokens=1000,
    )


# ---------------------------------------------------------------------------
# 1. Extract concepts from full markdown
# ---------------------------------------------------------------------------

_EXTRACT_PROMPT = (
    "Extract key concepts from this document.\n"
    "For each concept, provide:\n"
    "- name: a short concept name (2-5 words)\n"
    "- summary: one sentence, max 15 words\n\n"
    "Be concise. Return between 3 and 10 concepts.\n"
    "Focus on distinct, non-overlapping topics.\n\n"
    "Document:\n{document}"
)


def extract_concepts(
    markdown_text: str,
    doc_name: str = "",
) -> List[Dict[str, str]]:
    """
    Extract key concepts from a document's full markdown text.

    Args:
        markdown_text: The complete markdown content of the document.
        doc_name:      Filename (for logging only).

    Returns:
        List of dicts with keys ``name`` and ``summary``.
        Returns empty list on failure (non-fatal).
    """
    if not markdown_text or not markdown_text.strip():
        logger.warning("extract_concepts: empty markdown for %s", doc_name)
        return []

    try:
        llm = _get_concept_llm()
        structured_llm = llm.with_structured_output(ExtractedConcepts)

        # Truncate extremely large documents to avoid token limits
        # ~200k chars ≈ ~50k tokens, well within gpt-4.1-nano context
        truncated = markdown_text[:200_000]

        prompt = _EXTRACT_PROMPT.format(document=truncated)
        result: ExtractedConcepts = structured_llm.invoke(prompt)

        concepts = [
            {"name": c.name.strip(), "summary": c.summary.strip()}
            for c in result.concepts
            if c.name.strip()
        ]
        logger.info(
            "Extracted %d concepts from '%s': %s",
            len(concepts),
            doc_name,
            [c["name"] for c in concepts],
        )
        return concepts

    except Exception:
        logger.exception("Concept extraction failed for '%s'", doc_name)
        return []


# ---------------------------------------------------------------------------
# 2. Classify chunks → concepts
# ---------------------------------------------------------------------------

_CLASSIFY_PROMPT = (
    "You are given a list of concepts and numbered text chunks from the same document.\n"
    "For each chunk, return which concept names apply.\n"
    'A chunk may match 1-3 concepts. If a chunk matches none, assign it ["general"].\n\n'
    "Concepts:\n{concepts_text}\n\n"
    "Chunks:\n{chunks_text}\n\n"
    "Return the mapping for every chunk index."
)

# Maximum characters of chunk text to send in a single classify call
_CLASSIFY_CHUNK_CHAR_LIMIT = 120_000


def classify_chunks_to_concepts(
    chunks: List[Document],
    concepts: List[Dict[str, str]],
) -> List[Document]:
    """
    Tag each chunk's ``metadata["concepts"]`` with relevant concept names.

    Uses a batched LLM call to classify all chunks against the concept list.
    Modifies chunks **in-place** and also returns them.

    Args:
        chunks:   List of langchain Document objects (with page_content + metadata).
        concepts: Output of :func:`extract_concepts`.

    Returns:
        The same list of chunks, with ``metadata["concepts"]`` populated.
    """
    if not concepts:
        # No concepts extracted — tag everything as "general"
        for chunk in chunks:
            chunk.metadata["concepts"] = ["general"]
        return chunks

    if not chunks:
        return chunks

    try:
        llm = _get_concept_llm()
        structured_llm = llm.with_structured_output(ChunkConceptMappings)

        concept_names = [c["name"] for c in concepts]
        concepts_text = "\n".join(f"- {c['name']}: {c['summary']}" for c in concepts)

        # Build numbered chunk listing, truncating each chunk for token budget
        chunks_text_parts = []
        total_chars = 0
        for i, chunk in enumerate(chunks):
            snippet = chunk.page_content[:500]  # first 500 chars per chunk
            entry = f"[{i}] {snippet}"
            total_chars += len(entry)
            if total_chars > _CLASSIFY_CHUNK_CHAR_LIMIT:
                break
            chunks_text_parts.append(entry)

        chunks_text = "\n\n".join(chunks_text_parts)
        classified_count = len(chunks_text_parts)

        prompt = _CLASSIFY_PROMPT.format(
            concepts_text=concepts_text,
            chunks_text=chunks_text,
        )
        result: ChunkConceptMappings = structured_llm.invoke(prompt)

        # Build index → concept names mapping
        index_map: Dict[int, List[str]] = {}
        for m in result.mappings:
            # Validate concept names against known list
            valid = [n for n in m.concept_names if n in concept_names or n == "general"]
            index_map[m.chunk_index] = valid if valid else ["general"]

        # Apply to chunks
        for i, chunk in enumerate(chunks):
            if i < classified_count and i in index_map:
                chunk.metadata["concepts"] = index_map[i]
            else:
                # Chunks beyond the classified window get all concepts
                chunk.metadata["concepts"] = concept_names

        logger.info(
            "Classified %d/%d chunks across %d concepts",
            classified_count,
            len(chunks),
            len(concepts),
        )
        return chunks

    except Exception:
        logger.exception(
            "Chunk-concept classification failed, tagging all as 'general'"
        )
        for chunk in chunks:
            chunk.metadata["concepts"] = ["general"]
        return chunks


# ---------------------------------------------------------------------------
# 3. Store concepts with embeddings in document_concepts table
# ---------------------------------------------------------------------------


def store_concepts(
    document_id: uuid.UUID,
    concepts: List[Dict[str, str]],
    embedding_model: Any,
    db: Session,
    extractor_version: str = "v1",
) -> None:
    """
    Persist extracted concepts with their vector embeddings.

    Embeds each concept summary using the provided embedding model
    (same model used for chunk embeddings — currently nomic-embed-text)
    and upserts rows into ``document_concepts``.

    Args:
        document_id:       UUID of the parent document.
        concepts:          Output of :func:`extract_concepts`.
        embedding_model:   A langchain embeddings instance (e.g. OllamaEmbeddings).
        db:                Synchronous SQLAlchemy session.
        extractor_version: Version tag for cache invalidation.
    """
    if not concepts:
        return

    try:
        # Embed all concept summaries in one batch call
        summaries = [c["summary"] for c in concepts]
        vectors = embedding_model.embed_documents(summaries)

        for concept, vector in zip(concepts, vectors):
            stmt = pg_insert(DocumentConcept).values(
                document_id=document_id,
                concept_name=concept["name"],
                concept_summary=concept["summary"],
                concept_embedding=vector,
                extractor_version=extractor_version,
            )
            # Upsert: on conflict update summary + embedding
            stmt = stmt.on_conflict_do_update(
                constraint="uq_document_concept",
                set_={
                    "concept_summary": stmt.excluded.concept_summary,
                    "concept_embedding": stmt.excluded.concept_embedding,
                    "extractor_version": stmt.excluded.extractor_version,
                },
            )
            db.execute(stmt)

        db.commit()
        logger.info(
            "Stored %d concepts for document %s",
            len(concepts),
            document_id,
        )

    except Exception:
        logger.exception("Failed to store concepts for document %s", document_id)
        db.rollback()
