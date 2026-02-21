"""
Embedding Tasks - Refactored for One Vectorstore Per User

Key changes:
- Process embeddings at user level, not project level
- Track individual document embedding status
- Collection name: user_{user_id}
- Idempotent: marks documents as embedded after processing
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from src.api.db.models import Documents, LangchainPgCollection, UserVectorstore


# Document processing configuration
headers_to_split = [("#", "heading"), ("##", "section"), ("###", "subsection")]

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = False

converter = DocumentConverter(
    format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
)

recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100, add_start_index=True
)

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split, strip_headers=False
)


def process_user_embeddings(
    user_id: str,
    collection_name: str,
    document_ids: List[str],
    file_paths: List[str],
):
    """
    Process embeddings for a user's vectorstore.
    
    Idempotent behavior:
    - Only processes documents with provided IDs
    - Marks each document as is_embedded=True after successful processing
    - Updates document_count in UserVectorstore
    - If called again with same documents, they won't be re-processed
      (because is_embedded=True filter happens at CRUD level)
    
    Args:
        user_id: The user's UUID as string
        collection_name: Collection name (format: user_{user_id})
        document_ids: List of document UUIDs to process
        file_paths: List of file paths corresponding to document_ids
    """
    # Get sync database URL (worker runs synchronously, can't use asyncpg)
    db_url = os.getenv("DATABASE_URL", "")
    # Convert async URL to sync: replace asyncpg/psycopg with psycopg2
    sync_db_url = db_url.replace("+asyncpg", "").replace("+psycopg", "")
    
    engine = create_engine(sync_db_url)
    db = Session(engine)

    try:
        # Get or create user's vectorstore
        vectorstore_record = (
            db.query(UserVectorstore)
            .filter(UserVectorstore.user_id == uuid.UUID(user_id))
            .first()
        )

        if not vectorstore_record:
            vectorstore_record = UserVectorstore(
                user_id=uuid.UUID(user_id),
                status="processing",
            )
            db.add(vectorstore_record)
            db.commit()

        vectorstore_record.status = "processing"
        db.commit()

        # Process documents
        docling_docs: List[Document] = []
        processed_doc_ids: List[str] = []

        for doc_id, file_path in zip(document_ids, file_paths):
            try:
                # Get document record
                document = (
                    db.query(Documents)
                    .filter(Documents.doc_id == uuid.UUID(doc_id))
                    .first()
                )

                if not document:
                    print(f"Document {doc_id} not found, skipping")
                    continue

                # Skip if already embedded or ready (idempotency check)
                if document.is_embedded or document.status == "ready":
                    print(f"Document {doc_id} already processed, skipping")
                    continue

                # Convert document to markdown
                result = converter.convert(file_path)
                md = result.document.export_to_markdown()

                # Compute content hash using normalized text
                from src.core.hashing import compute_content_hash
                content_hash = compute_content_hash(md)

                # Store markdown content and content_hash
                document.content_md = md
                document.content_hash = content_hash

                # Content-level dedup: check for existing canonical document
                canonical = (
                    db.query(Documents)
                    .filter(
                        Documents.user_id == uuid.UUID(user_id),
                        Documents.content_hash == content_hash,
                        Documents.doc_id != uuid.UUID(doc_id),
                        Documents.is_embedded == True,
                    )
                    .first()
                )

                if canonical:
                    # Same content exists - link to canonical, skip embedding
                    document.canonical_document_id = canonical.doc_id
                    document.status = "ready"
                    document.is_embedded = True  # Inherits canonical's embeddings
                    db.commit()
                    print(f"Doc {doc_id} linked to canonical {canonical.doc_id} (same content)")
                    continue

                # New content - mark as processing
                document.status = "processing"
                db.commit()

                # Split into chunks
                header_docs = markdown_splitter.split_text(md)

                for doc in header_docs:
                    if len(doc.page_content) > 800:
                        split_docs = recursive_splitter.split_text(doc.page_content)
                        for sdoc in split_docs:
                            docling_docs.append(
                                Document(
                                    page_content=sdoc,
                                    metadata={
                                        "user_id": user_id,
                                        "document_id": doc_id,
                                        "source": str(file_path),
                                        "file_name": Path(file_path).name,
                                    },
                                )
                            )
                    else:
                        docling_docs.append(
                            Document(
                                page_content=doc.page_content,
                                metadata={
                                    "user_id": user_id,
                                    "document_id": doc_id,
                                    "source": str(file_path),
                                    "file_name": Path(file_path).name,
                                },
                            )
                        )

                processed_doc_ids.append(doc_id)

            except Exception as e:
                print(f"Error processing document {doc_id}: {e}")
                # Mark document as failed
                try:
                    document.status = "failed"
                    db.commit()
                except:
                    pass
                # Continue with other documents

        if not docling_docs:
            # Nothing to embed
            vectorstore_record.status = "ready"
            vectorstore_record.last_synced_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "status": "completed",
                "message": "No new documents to embed",
                "document_count": 0,
            }

        # Create/update vector store
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        )

        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=os.getenv("REDIS_DATABASE_URL"),
        )

        # Add documents to vector store
        vector_store.add_documents(documents=docling_docs)

        # Get collection ID
        collection = (
            db.query(LangchainPgCollection)
            .filter(LangchainPgCollection.name == collection_name)
            .first()
        )

        if not collection:
            raise Exception(f"Collection {collection_name} was not created")

        # Mark processed documents as embedded and ready
        for doc_id in processed_doc_ids:
            document = (
                db.query(Documents)
                .filter(Documents.doc_id == uuid.UUID(doc_id))
                .first()
            )
            if document:
                document.is_embedded = True
                document.embedded_at = datetime.now(timezone.utc)
                document.status = "ready"

        # Update vectorstore record
        vectorstore_record.collection_id = collection.id
        vectorstore_record.document_count = len(processed_doc_ids)
        vectorstore_record.status = "ready"
        vectorstore_record.last_synced_at = datetime.now(timezone.utc)
        vectorstore_record.error_message = None

        db.commit()

        return {
            "status": "completed",
            "document_count": len(processed_doc_ids),
            "chunk_count": len(docling_docs),
            "collection_id": str(collection.id),
        }

    except Exception as e:
        # Update vectorstore status on failure
        try:
            vectorstore_record = (
                db.query(UserVectorstore)
                .filter(UserVectorstore.user_id == uuid.UUID(user_id))
                .first()
            )

            if vectorstore_record:
                vectorstore_record.status = "failed"
                vectorstore_record.error_message = str(e)
                db.commit()
        except Exception:
            pass

        raise

    finally:
        db.close()
