from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.session import get_db
from src.api.db.crud import create_mcq, get_all_mcqs
from src.api.db.schema import CreateMCQ, ReadMCQ
from typing import List
import uuid

router = APIRouter(prefix="/mcqs", tags=["MCQs"])

@router.post("/", response_model = ReadMCQ, status_code = status.HTTP_201_CREATED)
async def create_mcq_endpoint(mcqs: CreateMCQ, db: AsyncSession = Depends(get_db)):
    new_mcq = await create_mcq(db, mcqs)
    return new_mcq
