"""Backward-compat shim — imports moved to src.rag.retrieval."""
from src.rag.retrieval import *  # noqa: F401,F403
from src.rag.retrieval import (
    retrieve_with_concepts,
    format_retrieved_context,
    _PG_CONNECTION,
    _match_concepts,
    _retrieve_chunks_sync,
    _deduplicate_chunks,
    CONCEPT_TOP_K,
    CONCEPT_SCORE_THRESHOLD,
    MAX_CHUNKS,
)
