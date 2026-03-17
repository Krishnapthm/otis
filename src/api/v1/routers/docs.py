"""
Documents Router - Supports User-Owned Documents

Documents belong to users and can be linked to multiple projects.
User-level endpoints don't require project_id.
"""

from fastapi import APIRouter, UploadFile, File, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import os

from src.api.crud import delete_doc, get_doc, upload_new_doc, get_all_docs
from src.api.crud.docs import (
    doc_thumbnail,
    download_project_docs,
    download_user_doc,
    get_user_doc_by_id,
    link_docs_to_project,
    get_user_docs,
)
from src.api.db.schema import AuthResponse, DocDelete, DocResponse, DocLinkRequest
from src.api.db.models.session import get_db
from src.core.security import get_current_user
from src.services.file_handling import store_file


ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}

MAX_FILE_SIZE = 60 * 1024 * 1024

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")


# =============================================================================
# Project-scoped document routes
# =============================================================================
router = APIRouter(prefix="/project/{project_id}/documents")


@router.post("/", name="upload documents", response_model=List[DocResponse], status_code=status.HTTP_201_CREATED)
async def upload_document_endpoint(
    project_id: uuid.UUID,
    current_user: AuthResponse = Depends(get_current_user),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload documents to a project.
    
    Documents are owned by the user and linked to the specified project.
    The same document can later be linked to other projects.
    """
    return await upload_new_doc(project_id, db, await store_file(files), current_user)


@router.post("/link", name="link documents", response_model=dict, status_code=status.HTTP_200_OK)
async def link_documents_endpoint(
    project_id: uuid.UUID,
    request: DocLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Link existing documents to a project.
    
    Idempotent: Documents already linked to the project are skipped.
    Only documents owned by the current user can be linked.
    """
    return await link_docs_to_project(
        current_user.user_id, project_id, request.doc_ids, db
    )


@router.get("/", name="list project documents", status_code=status.HTTP_200_OK, response_model=List[DocResponse])
async def get_documents_endpoint(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """Get all documents in a project."""
    return await get_all_docs(project_id, db, current_user.user_id)


@router.get("/download", name="download project documents", status_code=status.HTTP_200_OK)
async def download_project_docs_endpoint(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """Download all documents from a project (as zip if multiple)."""
    return await download_project_docs(db, project_id, current_user.user_id)


@router.get("/{doc_id}", name="get project document", status_code=status.HTTP_200_OK, response_model=DocResponse)
async def get_document_endpoint(
    doc_id: uuid.UUID,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """Get a specific document from a project."""
    return await get_doc(db, doc_id, project_id, current_user.user_id)


@router.delete("/", name="delete documents", status_code=status.HTTP_200_OK)
async def delete_document_endpoint(
    request: DocDelete,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Delete documents.
    
    Note: This deletes the document entirely (from all projects).
    """
    return await delete_doc(db, request.doc_id, current_user.user_id)


# =============================================================================
# User-level document routes (no project_id required)
# =============================================================================
user_docs_router = APIRouter(prefix="/documents")


@user_docs_router.get("/", name="list user documents", response_model=List[DocResponse], status_code=status.HTTP_200_OK)
async def get_user_documents_endpoint(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Get all documents owned by the current user.
    
    This returns documents regardless of which projects they're linked to.
    """
    return await get_user_docs(current_user.user_id, db, limit, skip)


@user_docs_router.post("/", name="upload user documents", response_model=List[DocResponse], status_code=status.HTTP_201_CREATED)
async def upload_user_document_endpoint(
    current_user: AuthResponse = Depends(get_current_user),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload documents without linking to a specific project.
    
    Documents can be linked to projects later using the link endpoint.
    """
    return await upload_new_doc(None, db, await store_file(files), current_user)


@user_docs_router.get("/{doc_id}", name="get user document", response_model=DocResponse, status_code=status.HTTP_200_OK)
async def get_user_document_endpoint(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Get a specific document by ID.
    
    No project_id required - works at user level.
    """
    return await get_user_doc_by_id(current_user.user_id, doc_id, db)


@user_docs_router.get("/{doc_id}/download", name="download document", status_code=status.HTTP_200_OK)
async def download_user_document_endpoint(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Download a single document.
    
    No project_id required - works at user level.
    """
    return await download_user_doc(db, doc_id, current_user.user_id)


@user_docs_router.get("/{doc_id}/thumbnail", name="document thumbnail", status_code=status.HTTP_200_OK)
async def get_document_thumbnail_endpoint(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Get thumbnail for a document.
    
    No project_id required - works at user level.
    Verifies user owns the document.
    """
    return await doc_thumbnail(doc_id, current_user.user_id, db)


@user_docs_router.delete("/", name="delete user documents", status_code=status.HTTP_200_OK)
async def delete_user_document_endpoint(
    request: DocDelete,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """Delete documents owned by the current user."""
    return await delete_doc(db, request.doc_id, current_user.user_id)