from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
import uuid
from datetime import datetime
from src.api.crud import delete_doc, download_doc, get_doc, upload_new_doc, get_all_docs
from src.api.db.models import Documents
from src.api.db.schema import DocResponse, DocBase
from src.api.db.models.session import get_db
import os

from src.file_handling import store_file

ALLOWED_EXTENSIONS = {
    "pdf":"application/pdf",
    "txt":"text/plain",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}

MAX_FILE_SIZE = 10 * 1024 * 1024

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")


router = APIRouter()

@router.post("/{project_id}/", name='upload documents', response_model=List[DocResponse], status_code = status.HTTP_201_CREATED)
async def upload_document_endpoint(project_id: uuid.UUID, files: List[UploadFile] = File(...), db: AsyncSession = Depends(get_db)):
    """Upload and Store documents in the database"""

    return await upload_new_doc(project_id, db, await store_file(files))


@router.get("/", name='list all documents', status_code = status.HTTP_200_OK, response_model=List[DocResponse])
async def get_documents_endpoint(db: AsyncSession = Depends(get_db)):
    
    return await get_all_docs(db)


@router.get("/{doc_id}", name='list document with id', status_code = status.HTTP_201_CREATED)
async def get_document_endpoint( doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    
    return await get_doc(db, doc_id)


@router.delete("/{doc_id}", name='delete document with id', status_code = status.HTTP_200_OK)
async def delete_document_endpoint( doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    
    return await delete_doc(db, doc_id)


@router.get("/{project_id}/download", name='download documents with id', status_code = status.HTTP_200_OK)
async def download_doc_endpoint(project_id:uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await download_doc(db, project_id)

# @router.post("/{project_id}", name="upload project documents", response_model = DocResponse, status_code=status.HTTP_201_CREATED)
# async def upload_project_document_endpoint(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
