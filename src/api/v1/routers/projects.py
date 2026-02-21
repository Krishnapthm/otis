from fastapi import APIRouter, Depends, HTTPException, status, Response
from src.api.db.models.session import get_db
from src.api.db.schema import AuthResponse, ProjectResponse, ProjectBase
from src.api.crud import create_new_project, get_all_projects, get_project, delete_project_with_id
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import uuid

from src.core.security import get_current_user

# from src.core.security import get_current_active_user

router = APIRouter(prefix="/projects")

@router.post("/", name='create project', response_model = ProjectResponse, status_code = status.HTTP_201_CREATED)
async def create_project(project: ProjectBase, db: AsyncSession = Depends(get_db), current_user: AuthResponse = Depends(get_current_user)):
   
    return await create_new_project(db, project, current_user)

@router.get("/", name="list projects", response_model= List[ProjectResponse], status_code= status.HTTP_200_OK)
async def list_projects(limit: int = 50, skip: int = 0, db: AsyncSession = Depends(get_db), current_user: AuthResponse = Depends(get_current_user)):

    return await get_all_projects(db, current_user, limit=limit, skip=skip)

@router.get("/{project_id}", name= "list project with id", response_model= ProjectResponse, status_code= status.HTTP_200_OK)
async def list_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: AuthResponse = Depends(get_current_user)):

    return await get_project(db, project_id, current_user)

@router.delete("/{project_id}", name="delete project with id", response_model= dict, status_code= status.HTTP_200_OK)
async def delete_project(project_id: uuid.UUID, current_user: AuthResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    return await delete_project_with_id(db, project_id, current_user)
    
