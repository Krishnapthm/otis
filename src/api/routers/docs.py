from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
import uuid
from datetime import datetime
from src.api.db.crud import upload_new_doc
from src.api.db.models import Documents
from src.api.db.schema import DocResponse, DocBase
from src.api.db.session import get_db

ALLOWED_EXTENSIONS = {
    "pdf":"application/pdf",
    "txt":"text/plain",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


router = APIRouter(prefix="/docs", tags=["Documents"])

@router.post("/upload", name='upload documents', response_model=DocResponse, status_code = status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload and Store documents in the database"""

    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types:{', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    
    content = await file.read()

    if len(content)> MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
        )

    document = DocBase(
        filename= file.filename,
        file_type= file.content_type,
        file_size= len(content),
    )

    return await upload_new_doc(db, document)


@router.post("/upload-multiple", name='upload multiple documents', status_code = status.HTTP_201_CREATED)
async def create_mcq_endpoint():
    new_mcq = "upload-multiple"
    return new_mcq

@router.get("/", name='list all documents', status_code = status.HTTP_201_CREATED)
async def create_mcq_endpoint():
    new_mcq = "documents list"
    return new_mcq


@router.get("/{document_id}", name='list all documents', status_code = status.HTTP_201_CREATED)
async def create_mcq_endpoint():
    new_mcq = "document_id"
    return new_mcq


@router.get("/{document_id}/download", name='download documents', status_code = status.HTTP_201_CREATED)
async def create_mcq_endpoint():
    new_mcq = "document delete"
    return new_mcq