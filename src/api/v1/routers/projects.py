from fastapi import APIRouter, Depends, HTTPException, status, Response
from src.api.db.models.session import get_db
from src.api.db.schema import ProjectResponse, ProjectBase
from src.api.crud import create_new_project, get_all_projects, get_project, delete_project_with_id
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import uuid

router = APIRouter()

@router.post("/", name='create project', response_model = ProjectResponse, status_code = status.HTTP_201_CREATED)
async def create_project(project: ProjectBase, db: AsyncSession = Depends(get_db)):
   
    return await create_new_project(db, project)

@router.get("/", name="list projects", response_model= List[ProjectResponse], status_code= status.HTTP_200_OK)
async def list_projects(db: AsyncSession = Depends(get_db)):

    return await get_all_projects(db)

@router.get("/{project_id}", name= "list project with id", response_model= ProjectResponse, status_code= status.HTTP_200_OK)
async def list_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):

    return await get_project(db, project_id)

@router.delete("/{project_id}", name="delete project with id", response_model= dict, status_code= status.HTTP_200_OK)
async def delete_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):

    return await delete_project_with_id(db, project_id)