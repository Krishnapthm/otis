from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from src.api.crud.embeddings import create_embeddings, delete_embedding, list_embeddings
from src.api.db.schema import EmbeddingVersionDelete, EmbeddingVersionResponse
from src.api.db.models.session import get_db
from langchain_core.documents import Document

router = APIRouter(prefix="/project/{project_id}/embeddings")

@router.post("/", name="create embeddings", response_model=EmbeddingVersionResponse)
async def create_embedding(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await create_embeddings(project_id, db)

@router.get("/", name="list embeddings", response_model=List[EmbeddingVersionResponse])
async def create_embedding(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await list_embeddings(project_id, db)

@router.get("/{collection_id}", name="get embedding")
async def get_embeddings(project_id: uuid.UUID, collection_id: uuid.UUID):
    return "ph"

@router.put("/{collection_id}", name="update embedding")
async def update_embeddings(project_id: uuid.UUID, collection_id: uuid.UUID):
    return "ph"

@router.delete("/", name="delete embedding", response_model=dict)
async def delete_embeddings(request: EmbeddingVersionDelete, project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await delete_embedding(project_id, request.version_ids, db)