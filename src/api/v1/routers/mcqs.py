import json
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models.session import get_db
from src.api.crud import create_mcq, get_all_mcqs, get_mcq
from src.api.db.schema import CreateMCQ, ReadMCQ
from typing import List
import uuid

router = APIRouter()

@router.post("/", name='create MCQ', response_model = ReadMCQ, status_code = status.HTTP_201_CREATED)
async def create_mcq_endpoint(mcqs: CreateMCQ, db: AsyncSession = Depends(get_db)):
    new_mcq = await create_mcq(db, mcqs)
    return new_mcq

@router.get("/", name='list mcq', response_model=List[ReadMCQ])
async def list_mcq(db: AsyncSession = Depends(get_db))-> List[ReadMCQ]:
    mcqs = await get_all_mcqs(db)
    return mcqs


# @router.get("/list/{project_id}", name='list mcq', response_model=List[ReadMCQ])
# async def list_mcq(project_id: uuid, db: AsyncSession = Depends(get_db))-> List[ReadMCQ]:
#     mcqs = await get_mcq(db, project_id)
#     return mcqs

@router.get("/download/{id}", name='donwload mcq')
async def download_mcq(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    mcqs = await get_mcq(db, id)

    if not mcqs:
        return Response(status_code=404, content="MCQ not found")

    json_data = [mcq.model_dump() for mcq in mcqs]

    json_bytes = json.dumps(json_data, indent=2, default=str).encode("utf-8")

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="mcqs_{id}.json"'},
    )



