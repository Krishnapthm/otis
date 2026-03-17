"""
RAG Module
==========

Consolidated RAG pipeline: embedding, retrieval, concept extraction, and tasks.
"""

from src.rag.retrieval import (
    retrieve_with_concepts,
    format_retrieved_context,
    _PG_CONNECTION,
)
from src.rag.concepts import extract_concepts, classify_chunks_to_concepts, store_concepts
from src.rag.embedding import embed_docs, create_vector_store, extract_pdf_markdown
from src.rag.tasks import process_user_embeddings
from src.rag.agent_retrieval import retrieve_chunks

__all__ = [
    "retrieve_with_concepts",
    "format_retrieved_context",
    "_PG_CONNECTION",
    "extract_concepts",
    "classify_chunks_to_concepts",
    "store_concepts",
    "embed_docs",
    "create_vector_store",
    "extract_pdf_markdown",
    "process_user_embeddings",
    "retrieve_chunks",
]
