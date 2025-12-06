from typing import List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Projects, Users
from src.api.db.schema import AuthResponse, ProjectBase, ProjectResponse
import uuid
from datetime import timezone, timedelta
from fastapi import HTTPException
IST = timezone(timedelta(hours=5, minutes=30))

async def create_new_project(db: AsyncSession, project: ProjectBase, current_user: AuthResponse)-> ProjectResponse:

    new_project = Projects(
        project_name = project.project_name,
        project_desc = project.project_desc,
        created_by = current_user.user_id
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    ist_time = new_project.created_at.replace(tzinfo=timezone.utc).astimezone(IST)

    return ProjectResponse(
        project_name=new_project.project_name,
        project_desc=new_project.project_desc,
        project_id=new_project.project_id,
        created_at=ist_time,
        created_by=new_project.created_by
    )  


async def get_all_projects(db: AsyncSession,  current_user: AuthResponse, limit: int=50, skip: int=0)-> List[ProjectResponse]:

    is_admin = (await db.execute(select(Users.role).where(Users.user_id==current_user.user_id))).scalar_one_or_none()
    if is_admin=='admin':
        result = await db.execute(select(Projects).offset(skip).limit(limit))
    else:
        result = await db.execute(select(Projects).where(Projects.created_by==current_user.user_id).offset(skip).limit(limit))
    projects = result.scalars().all()

    return [
        ProjectResponse(
            project_id=m.project_id,
            project_name=m.project_name,
            project_desc=m.project_desc,
            created_at=m.created_at,
            created_by=m.created_by
            
        )
        for m in projects
    ]

async def get_project(db: AsyncSession, pid: uuid)-> ProjectResponse | None:

    result = await db.execute(select(Projects).where(Projects.project_id == pid))
    project = result.scalar_one_or_none()

    if not project:
        return None
    
    return ProjectResponse(
            project_id=project.project_id,
            project_name=project.project_name,
            project_desc=project.project_desc,
            created_at=project.created_at,
            created_by=project.created_by 
        )

async def delete_project_with_id(db: AsyncSession, pid: uuid, current_user: AuthResponse)-> dict | None:


    is_admin = (await db.execute(select(Users.role).where(Users.user_id==current_user.user_id))).scalar_one_or_none()
    if is_admin=='admin':
        result = await db.execute(select(Projects))
    else:
        result = await db.execute(select(Projects).where(Projects.created_by==current_user.user_id).filter( Projects.project_id==pid))
   

    del_project = result.scalar_one_or_none()

    if not del_project:
        raise HTTPException(status_code= 404)
    
    await db.delete(del_project)
    await db.commit()

    return {
        "message":f"project {del_project.project_name} deleted successfully"
    }
    
