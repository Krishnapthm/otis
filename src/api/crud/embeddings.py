"""
Embeddings CRUD - Refactored for One Vectorstore Per User

Key changes:
- User has a single vectorstore (collection)
- Documents track their own embedding status (is_embedded)
- Idempotent sync: only embeds documents where is_embedded=False
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import HTTPException
from redis import Redis
from rq import Queue
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import (
    Documents,
    LangchainPgCollection,
    LangchainPgEmbedding,
    UserVectorstore,
)
from src.api.db.schema import VectorstoreStatus, VectorstoreSyncResponse


IST = timezone(timedelta(hours=5, minutes=30))

redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
queue = Queue("default", connection=redis_conn)


async def get_or_create_vectorstore(
    user_id: uuid.UUID, db: AsyncSession
) -> UserVectorstore:
    """
    Get user's vectorstore or create one if it doesn't exist.
    Idempotent: calling multiple times returns the same vectorstore.
    """
    result = await db.execute(
        select(UserVectorstore).where(UserVectorstore.user_id == user_id)
    )
    vectorstore = result.scalar_one_or_none()

    if not vectorstore:
        vectorstore = UserVectorstore(
            user_id=user_id,
            status="pending",
            document_count=0,
        )
        db.add(vectorstore)
        await db.commit()
        await db.refresh(vectorstore)

    return vectorstore


async def sync_user_embeddings(
    user_id: uuid.UUID,
    db: AsyncSession,
    doc_ids: Optional[List[uuid.UUID]] = None,
) -> VectorstoreSyncResponse:
    """
    Sync documents to user's vectorstore.
    
    Idempotent behavior:
    - Only processes documents where is_embedded=False
    - If specific doc_ids provided, filters to those
    - If all documents already embedded, returns early
    
    Args:
        user_id: The user's ID
        db: Database session
        doc_ids: Optional list of specific document IDs to sync
        
    Returns:
        VectorstoreSyncResponse with sync status and job info
    """
    # Get or create user's vectorstore
    vectorstore = await get_or_create_vectorstore(user_id, db)

    # Build query for un-embedded documents
    query = select(Documents).where(
        Documents.user_id == user_id,
        Documents.is_embedded == False,  # noqa: E712 - SQLAlchemy requires ==
    )

    # If specific doc_ids provided, filter to those
    if doc_ids:
        query = query.where(Documents.doc_id.in_(doc_ids))

    result = await db.execute(query)
    docs_to_embed = result.scalars().all()

    # Idempotent: if nothing to embed, return early
    if not docs_to_embed:
        return VectorstoreSyncResponse(
            status="complete",
            message="All documents are already synced",
            documents_queued=0,
            job_id=None,
        )

    # Check if there's already a processing job
    if vectorstore.status == "processing" and vectorstore.job_id:
        return VectorstoreSyncResponse(
            status="processing",
            message="A sync is already in progress",
            documents_queued=0,
            job_id=vectorstore.job_id,
        )

    # Prepare data for the worker
    collection_name = f"user_{user_id}"
    file_paths = [doc.file_path for doc in docs_to_embed]
    document_ids = [str(doc.doc_id) for doc in docs_to_embed]

    # Update vectorstore status
    vectorstore.status = "processing"
    await db.commit()

    # Queue the embedding task
    from src.rag.tasks import process_user_embeddings

    job = queue.enqueue(
        process_user_embeddings,
        args=(
            str(user_id),
            collection_name,
            document_ids,
            file_paths,
        ),
        job_timeout="2h",
        failure_ttl=86400,
        result_ttl=3600,
    )

    # Store job ID
    vectorstore.job_id = job.id
    await db.commit()

    return VectorstoreSyncResponse(
        status="queued",
        message=f"Queued {len(docs_to_embed)} documents for embedding",
        documents_queued=len(docs_to_embed),
        job_id=job.id,
    )


async def get_vectorstore_status(
    user_id: uuid.UUID, db: AsyncSession
) -> VectorstoreStatus:
    """
    Get status of user's vectorstore including document counts.
    """
    # Get vectorstore (may not exist yet)
    result = await db.execute(
        select(UserVectorstore).where(UserVectorstore.user_id == user_id)
    )
    vectorstore = result.scalar_one_or_none()

    # Count documents
    total_result = await db.execute(
        select(func.count(Documents.doc_id)).where(Documents.user_id == user_id)
    )
    total_documents = total_result.scalar() or 0

    embedded_result = await db.execute(
        select(func.count(Documents.doc_id)).where(
            Documents.user_id == user_id,
            Documents.is_embedded == True,  # noqa: E712
        )
    )
    embedded_documents = embedded_result.scalar() or 0

    pending_documents = total_documents - embedded_documents

    return VectorstoreStatus(
        user_id=user_id,
        collection_id=vectorstore.collection_id if vectorstore else None,
        status=vectorstore.status if vectorstore else "pending",
        total_documents=total_documents,
        embedded_documents=embedded_documents,
        pending_documents=pending_documents,
        last_synced_at=vectorstore.last_synced_at if vectorstore else None,
        error_message=vectorstore.error_message if vectorstore else None,
    )


async def clear_user_vectorstore(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """
    Clear user's vectorstore and reset all document embedding status.
    
    Idempotent: safe to call multiple times.
    
    Steps:
    1. Delete embeddings from langchain_pg_embedding
    2. Delete collection from langchain_pg_collection
    3. Reset is_embedded=False on all user's documents
    4. Reset vectorstore status
    """
    # Get user's vectorstore
    result = await db.execute(
        select(UserVectorstore).where(UserVectorstore.user_id == user_id)
    )
    vectorstore = result.scalar_one_or_none()

    collection_name = f"user_{user_id}"
    deleted_embeddings = 0

    if vectorstore and vectorstore.collection_id:
        # Delete all embeddings in this collection
        embedding_result = await db.execute(
            select(func.count(LangchainPgEmbedding.id)).where(
                LangchainPgEmbedding.collection_id == vectorstore.collection_id
            )
        )
        deleted_embeddings = embedding_result.scalar() or 0

        # Delete the collection (cascade will delete embeddings)
        collection_result = await db.execute(
            select(LangchainPgCollection).where(
                LangchainPgCollection.id == vectorstore.collection_id
            )
        )
        collection = collection_result.scalar_one_or_none()
        if collection:
            await db.delete(collection)

    # Reset all user's documents to is_embedded=False
    docs_result = await db.execute(
        select(Documents).where(
            Documents.user_id == user_id,
            Documents.is_embedded == True,  # noqa: E712
        )
    )
    docs_to_reset = docs_result.scalars().all()

    for doc in docs_to_reset:
        doc.is_embedded = False
        doc.embedded_at = None

    # Reset vectorstore status
    if vectorstore:
        vectorstore.collection_id = None
        vectorstore.document_count = 0
        vectorstore.status = "pending"
        vectorstore.job_id = None
        vectorstore.error_message = None
        vectorstore.last_synced_at = None

    await db.commit()

    return {
        "message": "Vectorstore cleared successfully",
        "embeddings_deleted": deleted_embeddings,
        "documents_reset": len(docs_to_reset),
    }
