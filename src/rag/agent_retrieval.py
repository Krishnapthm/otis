"""Vector-store retrieval logic extracted from agent nodes."""

from __future__ import annotations

import asyncio
import hashlib
import os
from typing import Any, Dict, List

from langchain_postgres import PGVector

from src.agents.utils.llm_config import embeddings
from src.core.config import settings
from src.rag.retrieval import _PG_CONNECTION


async def retrieve_chunks(
    *,
    doc_ids: List[str],
    search_queries: List[str],
    user_id: str,
) -> List[Dict[str, Any]]:
    """Run similarity search across *search_queries* and return deduplicated chunks.

    Parameters
    ----------
    doc_ids:
        Document IDs (as strings) to filter on.
    search_queries:
        Semantic queries to run against the vector store.
    user_id:
        Used to resolve the per-user collection name.

    Returns
    -------
    A list of chunk dicts sorted by descending relevance score,
    deduplicated by ``chunk_id`` (or content hash).
    """
    collection_name = f"user_{user_id}"
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=os.getenv("RETRIEVAL_DATABASE_URL", _PG_CONNECTION),
    )

    loop = asyncio.get_running_loop()
    merged_results: List[Dict[str, Any]] = []
    metadata_filter = {"document_id": {"$in": doc_ids}}

    for query in search_queries:
        try:
            results = await loop.run_in_executor(
                None,
                lambda q=query: vector_store.similarity_search_with_relevance_scores(
                    q,
                    k=settings.max_retrieved_chunks,
                    filter=metadata_filter,
                ),
            )
        except Exception:
            results = []

        for doc, score in results:
            metadata = dict(doc.metadata or {})
            did = str(metadata.get("document_id", ""))
            if did not in doc_ids:
                continue

            chunk_id = str(metadata.get("chunk_id") or metadata.get("id") or "")
            merged_results.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": did,
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": metadata,
                }
            )

    return _deduplicate(merged_results, max_chunks=settings.max_retrieved_chunks)


def _deduplicate(
    chunks: List[Dict[str, Any]], *, max_chunks: int
) -> List[Dict[str, Any]]:
    """Sort by score descending and remove duplicates by stable id."""
    chunks.sort(key=lambda c: c["score"], reverse=True)
    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for chunk in chunks:
        stable_id = (
            chunk["chunk_id"]
            or hashlib.sha256(
                chunk["content"].encode("utf-8", errors="ignore")
            ).hexdigest()
        )
        if stable_id in seen:
            continue
        seen.add(stable_id)
        if not chunk["chunk_id"]:
            chunk["chunk_id"] = stable_id
        deduped.append(chunk)
        if len(deduped) >= max_chunks:
            break
    return deduped
