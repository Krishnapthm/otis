"""Backward-compat shim — imports moved to src.rag.embedding."""
from src.rag.embedding import *  # noqa: F401,F403
from src.rag.embedding import (
    embed_docs,
    create_vector_store,
    extract_pdf_markdown,
    embeddings,
    vector_store,
    retriever,
    retriever_tool,
    recursive_splitter,
    markdown_splitter,
    headers_to_split,
    source,
)
