"""
Embeddings Router - Refactored for One Vectorstore Per User

New endpoints:
- POST /embeddings/sync - Sync all pending documents to vectorstore
- GET /embeddings/status - Get vectorstore status
- DELETE /embeddings/clear - Clear vectorstore and reset documents
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud.embeddings import (
    clear_user_vectorstore,
    get_vectorstore_status,
    sync_user_embeddings,
)
from src.api.db.models.session import get_db
from src.api.db.schema import (
    AuthResponse,
    VectorstoreStatus,
    VectorstoreSyncRequest,
    VectorstoreSyncResponse,
)
from src.core.security import get_current_user


router = APIRouter(prefix="/embeddings")


@router.post("/sync", response_model=VectorstoreSyncResponse)
async def sync_embeddings(
    request: VectorstoreSyncRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Sync documents to user's vectorstore.
    
    Idempotent: Only embeds documents that haven't been embedded yet.
    If all documents are already synced, returns immediately.
    
    Optionally provide doc_ids to sync specific documents only.
    """
    doc_ids = request.doc_ids if request else None
    return await sync_user_embeddings(current_user.user_id, db, doc_ids)


@router.get("/status", response_model=VectorstoreStatus)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Get status of user's vectorstore.
    
    Returns:
    - total_documents: All documents owned by user
    - embedded_documents: Documents that have been embedded
    - pending_documents: Documents waiting to be embedded
    - status: Current vectorstore status (pending, processing, ready, failed)
    - last_synced_at: When the last successful sync completed
    """
    return await get_vectorstore_status(current_user.user_id, db)


@router.delete("/clear", response_model=dict)
async def clear_embeddings(
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Clear user's vectorstore and reset all documents.
    
    Idempotent: Safe to call multiple times.
    
    This will:
    - Delete all embeddings from the vectorstore
    - Reset is_embedded=False on all user's documents
    - Reset vectorstore status to 'pending'
    
    Documents themselves are NOT deleted.
    """
    return await clear_user_vectorstore(current_user.user_id, db)
