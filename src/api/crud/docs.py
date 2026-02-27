"""
Documents CRUD - Refactored for User-Owned Documents

Key changes:
- Documents now have user_id (owned by user, not project)
- Documents can be linked to multiple projects
- Added link_docs_to_project for reusing documents
- Updated responses to include is_embedded status
"""

from typing import List, Optional
from fastapi.responses import FileResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Documents, Projects, t_project_docs
from src.api.db.schema import AuthResponse, DocBase, DocResponse
import uuid
import shutil
import os
from fastapi import HTTPException
from src.services.file_handling import (
    delete_file,
    download_file,
    pdf_thumbnail,
    zip_files,
)
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, insert, exists, delete
from src.api.db.models import UserVectorstore, LangchainPgEmbedding


async def upload_new_doc(
    project_id: Optional[uuid.UUID],
    db: AsyncSession,
    docs: List[DocBase],
    current_user: AuthResponse,
) -> List[DocResponse]:
    """
    Upload documents for a user with file-hash deduplication.

    Dedup Logic:
    1. Check file_hash - if exists, return existing doc (exact duplicate)
    2. Check filename - if exists, return 409 Conflict
    3. Create new document with status='pending'
    """
    results = []
    docs_to_link = []  # For project linking

    for doc in docs:
        # Level 1: Exact file duplicate check via file_hash
        if doc.file_hash:
            existing_by_hash = await db.execute(
                select(Documents).where(
                    and_(
                        Documents.user_id == current_user.user_id,
                        Documents.file_hash == doc.file_hash,
                    )
                )
            )
            if existing_doc := existing_by_hash.scalar_one_or_none():
                # Exact duplicate found - delete staging file and return error
                if os.path.exists(doc.file_path):
                    os.unlink(doc.file_path)

                # Return 409 with existing document info so UI can show it
                raise HTTPException(
                    status_code=409,
                    detail={
                        "type": "content_duplicate",
                        "message": "This file has already been uploaded",
                        "uploaded_filename": doc.filename,
                        "existing_document": {
                            "doc_id": str(existing_doc.doc_id),
                            "filename": existing_doc.filename,
                            "created_at": existing_doc.created_at.isoformat(),
                            "is_embedded": existing_doc.is_embedded,
                        },
                        "hint": "The content of this file matches an existing document",
                    },
                )

        # Level 2: Filename duplicate check (user experience - avoid confusion)
        filename_check = await db.execute(
            select(Documents.filename).where(
                and_(
                    Documents.user_id == current_user.user_id,
                    Documents.filename == doc.filename,
                )
            )
        )
        if filename_check.scalar_one_or_none():
            # Filename exists but different content - reject to avoid confusion
            if os.path.exists(doc.file_path):
                os.unlink(doc.file_path)
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "filename_duplicate",
                    "message": "A file with this name already exists",
                    "filename": doc.filename,
                    "hint": "Rename the file or delete the existing document",
                },
            )

        # Move file from staging to final location
        # doc.file_path is staging path, we move to UPLOAD_DIR/filename
        upload_dir = os.environ.get("UPLOAD_DIR", "/app/uploads")
        final_path = os.path.join(upload_dir, doc.filename)
        shutil.move(doc.file_path, final_path)

        # Create new document with pending status
        new_doc = Documents(
            user_id=current_user.user_id,
            filename=doc.filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            file_path=final_path,  # Use final path, not staging
            file_hash=doc.file_hash,
            status="pending",
            is_embedded=False,
        )
        db.add(new_doc)
        await db.flush()

        results.append(
            DocResponse(
                doc_id=new_doc.doc_id,
                user_id=new_doc.user_id,
                filename=new_doc.filename,
                file_type=new_doc.file_type,
                file_size=new_doc.file_size,
                created_at=new_doc.created_at,
                updated_at=new_doc.updated_at,
                file_path=new_doc.file_path,
                file_hash=new_doc.file_hash,
                project_id=project_id,
                is_embedded=new_doc.is_embedded,
                embedded_at=new_doc.embedded_at,
                status=new_doc.status,
                canonical_document_id=new_doc.canonical_document_id,
            )
        )
        if project_id:
            docs_to_link.append(new_doc.doc_id)

    # Verify project ownership and link documents
    if project_id and docs_to_link:
        result = await db.execute(
            select(Projects).where(
                and_(
                    Projects.project_id == project_id,
                    Projects.created_by == current_user.user_id,
                )
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project does not exist or you do not have access",
            )

        # Link docs to project (skip if already linked)
        for doc_id in docs_to_link:
            existing_link = await db.execute(
                select(t_project_docs).where(
                    and_(
                        t_project_docs.c.project_id == project_id,
                        t_project_docs.c.doc_id == doc_id,
                    )
                )
            )
            if not existing_link.first():
                await db.execute(
                    insert(t_project_docs).values(project_id=project_id, doc_id=doc_id)
                )

    await db.commit()
    return results


async def link_docs_to_project(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_ids: List[uuid.UUID],
    db: AsyncSession,
) -> dict:
    """
    Link existing documents to a project.

    Idempotent: if a document is already linked, it won't be re-linked.
    Only links documents that belong to the user.
    """
    # Verify project ownership
    result = await db.execute(
        select(Projects).where(
            and_(
                Projects.project_id == project_id,
                Projects.created_by == user_id,
            )
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404, detail="Project does not exist or you do not have access"
        )

    # Get documents that belong to the user
    result = await db.execute(
        select(Documents).where(
            and_(
                Documents.doc_id.in_(doc_ids),
                Documents.user_id == user_id,
            )
        )
    )
    user_docs = result.scalars().all()

    if not user_docs:
        raise HTTPException(
            status_code=404, detail="No documents found or you do not own them"
        )

    # Check which documents are already linked (idempotency)
    linked_count = 0
    skipped_count = 0

    for doc in user_docs:
        # Check if already linked
        existing = await db.execute(
            select(
                exists().where(
                    and_(
                        t_project_docs.c.project_id == project_id,
                        t_project_docs.c.doc_id == doc.doc_id,
                    )
                )
            )
        )
        already_linked = existing.scalar()

        if not already_linked:
            await db.execute(
                insert(t_project_docs).values(
                    project_id=project_id,
                    doc_id=doc.doc_id,
                )
            )
            linked_count += 1
        else:
            skipped_count += 1

    await db.commit()

    return {
        "message": f"Linked {linked_count} documents to project",
        "linked": linked_count,
        "skipped": skipped_count,
    }


async def get_user_docs(
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 50,
    skip: int = 0,
) -> List[DocResponse]:
    """
    Get all documents owned by a user (regardless of project).
    """
    result = await db.execute(
        select(Documents).where(Documents.user_id == user_id).offset(skip).limit(limit)
    )
    docs = result.scalars().all()

    return [
        DocResponse(
            doc_id=doc.doc_id,
            user_id=doc.user_id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            file_path=doc.file_path,
            file_hash=doc.file_hash,
            project_id=None,  # User-level view, no specific project
            is_embedded=doc.is_embedded,
            embedded_at=doc.embedded_at,
            status=doc.status,
            canonical_document_id=doc.canonical_document_id,
        )
        for doc in docs
    ]


async def get_user_doc_by_id(
    user_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession,
) -> DocResponse:
    """
    Get a specific document by ID (user-level, no project required).
    Verifies user owns the document.
    """
    result = await db.execute(
        select(Documents).where(
            and_(
                Documents.doc_id == doc_id,
                Documents.user_id == user_id,
            )
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=404, detail="Document not found or you do not have access"
        )

    return DocResponse(
        doc_id=document.doc_id,
        user_id=document.user_id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        created_at=document.created_at,
        updated_at=document.updated_at,
        file_path=document.file_path,
        file_hash=document.file_hash,
        project_id=None,
        is_embedded=document.is_embedded,
        embedded_at=document.embedded_at,
        status=document.status,
        canonical_document_id=document.canonical_document_id,
    )


async def get_doc(
    db: AsyncSession, did: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID
) -> DocResponse:
    """Get a specific document from a project."""
    result = await db.execute(
        select(Documents)
        .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
        .join(Projects, t_project_docs.c.project_id == Projects.project_id)
        .where(
            and_(
                Documents.doc_id == did,
                t_project_docs.c.project_id == project_id,
                Projects.created_by == user_id,
            )
        )
    )

    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404)

    return DocResponse(
        file_size=document.file_size,
        file_type=document.file_type,
        filename=document.filename,
        doc_id=document.doc_id,
        user_id=document.user_id,
        created_at=document.created_at,
        updated_at=document.updated_at,
        file_path=document.file_path,
        file_hash=document.file_hash,
        project_id=project_id,
        is_embedded=document.is_embedded,
        embedded_at=document.embedded_at,
        status=document.status,
        canonical_document_id=document.canonical_document_id,
    )


async def get_all_docs(
    project_id: uuid.UUID,
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
    skip: int = 0,
) -> List[DocResponse]:
    """Get all documents in a specific project."""
    result = await db.execute(
        select(Documents)
        .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
        .join(Projects, t_project_docs.c.project_id == Projects.project_id)
        .where(and_(Projects.project_id == project_id, Projects.created_by == user_id))
        .offset(skip)
        .limit(limit)
    )
    docs = result.scalars().all()

    return [
        DocResponse(
            doc_id=doc.doc_id,
            user_id=doc.user_id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            file_path=doc.file_path,
            file_hash=doc.file_hash,
            project_id=project_id,
            is_embedded=doc.is_embedded,
            embedded_at=doc.embedded_at,
            status=doc.status,
            canonical_document_id=doc.canonical_document_id,
        )
        for doc in docs
    ]


async def delete_doc(
    db: AsyncSession, did: List[uuid.UUID], user_id: uuid.UUID
) -> dict:
    """
    Delete documents owned by the user.

    Note: This deletes the document entirely, including from all projects
    and the vectorstore metadata. The actual embeddings will be orphaned
    but can be cleaned up separately.
    """
    del_docs: List[Documents] = []

    for di in did:
        # Verify document belongs to user
        result = await db.execute(
            select(Documents).where(
                and_(
                    Documents.doc_id == di,
                    Documents.user_id == user_id,
                )
            )
        )
        doc = result.scalar_one_or_none()

        if doc:
            del_docs.append(doc)

    if not del_docs:
        raise HTTPException(
            status_code=404,
            detail="Documents do not exist or you do not have permission",
        )

    vectorstore = (
        await db.execute(
            select(UserVectorstore).where(UserVectorstore.user_id == user_id)
        )
    ).scalar_one_or_none()

    deleted_names = []
    for del_doc in del_docs:
        del_doc_name = del_doc.filename

        if await delete_file(del_doc_name):
            if vectorstore and vectorstore.collection_id:
                await db.execute(
                    delete(LangchainPgEmbedding).where(
                        and_(
                            LangchainPgEmbedding.collection_id
                            == vectorstore.collection_id,
                            LangchainPgEmbedding.cmetadata["document_id"].astext
                            == str(del_doc.doc_id),
                        )
                    )
                )
            await db.delete(del_doc)
            deleted_names.append(del_doc_name)

    await db.commit()

    return {
        "message": f"Deleted {len(deleted_names)} documents",
        "deleted": deleted_names,
    }


async def download_user_doc(
    db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID
) -> FileResponse:
    """
    Download a single document by ID (user-level, no project required).
    Verifies user owns the document.
    """
    result = await db.execute(
        select(Documents).where(
            and_(
                Documents.doc_id == doc_id,
                Documents.user_id == user_id,
            )
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=404, detail="Document not found or access denied"
        )

    return download_file(document.filename)


async def download_project_docs(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> FileResponse:
    """Download all documents from a project as zip."""
    result = await db.execute(
        select(Documents.filename)
        .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
        .join(Projects, t_project_docs.c.project_id == Projects.project_id)
        .where(
            and_(
                t_project_docs.c.project_id == project_id,
                Projects.created_by == user_id,
            )
        )
    )
    down_docs = result.scalars().all()

    if not down_docs:
        raise HTTPException(
            status_code=404, detail="No documents found or access denied"
        )

    if len(down_docs) == 1:
        return download_file(down_docs[0])

    return await zip_files(down_docs)


# Keep old function name for backward compatibility
async def download_doc(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> FileResponse:
    """Alias for download_project_docs for backward compatibility."""
    return await download_project_docs(db, project_id, user_id)


async def doc_thumbnail(
    doc_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> FileResponse:
    """
    Get thumbnail for a document.
    Verifies user owns the document.
    """
    result = await db.execute(
        select(Documents).where(
            and_(
                Documents.doc_id == doc_id,
                Documents.user_id == user_id,
            )
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=404, detail="Document not found or access denied"
        )

    return pdf_thumbnail(document.file_path)
