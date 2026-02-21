"""
Projects CRUD

All operations verify user ownership (except admin can see all).
"""

from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from src.api.db.models import Projects, Users
from src.api.db.schema import AuthResponse, ProjectBase, ProjectResponse
import uuid
from datetime import timezone, timedelta
from fastapi import HTTPException

IST = timezone(timedelta(hours=5, minutes=30))


async def create_new_project(
    db: AsyncSession, project: ProjectBase, current_user: AuthResponse
) -> ProjectResponse:
    """Create a new project owned by the current user."""
    new_project = Projects(
        project_name=project.project_name,
        project_desc=project.project_desc,
        created_by=current_user.user_id,
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
        created_by=new_project.created_by,
    )


async def get_all_projects(
    db: AsyncSession, current_user: AuthResponse, limit: int = 50, skip: int = 0
) -> List[ProjectResponse]:
    """
    Get all projects for the current user.
    Admin users can see all projects.
    """
    is_admin = (
        await db.execute(
            select(Users.role).where(Users.user_id == current_user.user_id)
        )
    ).scalar_one_or_none()

    if is_admin == "admin":
        result = await db.execute(select(Projects).offset(skip).limit(limit))
    else:
        result = await db.execute(
            select(Projects)
            .where(Projects.created_by == current_user.user_id)
            .offset(skip)
            .limit(limit)
        )
    projects = result.scalars().all()

    return [
        ProjectResponse(
            project_id=m.project_id,
            project_name=m.project_name,
            project_desc=m.project_desc,
            created_at=m.created_at,
            created_by=m.created_by,
        )
        for m in projects
    ]


async def get_project(
    db: AsyncSession, pid: uuid.UUID, current_user: Optional[AuthResponse] = None
) -> ProjectResponse:
    """
    Get a specific project by ID.
    
    If current_user is provided, verifies ownership (admin can see all).
    If current_user is None, returns project without ownership check (legacy behavior).
    """
    # Build query
    query = select(Projects).where(Projects.project_id == pid)
    
    # Add ownership check if user provided
    if current_user:
        is_admin = (
            await db.execute(
                select(Users.role).where(Users.user_id == current_user.user_id)
            )
        ).scalar_one_or_none()
        
        if is_admin != "admin":
            query = query.where(Projects.created_by == current_user.user_id)
    
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404, 
            detail="Project not found or you do not have access"
        )

    return ProjectResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        project_desc=project.project_desc,
        created_at=project.created_at,
        created_by=project.created_by,
    )


async def delete_project_with_id(
    db: AsyncSession, pid: uuid.UUID, current_user: AuthResponse
) -> dict:
    """
    Delete a project.
    
    User can only delete their own projects.
    Admin can delete any project.
    """
    is_admin = (
        await db.execute(
            select(Users.role).where(Users.user_id == current_user.user_id)
        )
    ).scalar_one_or_none()

    if is_admin == "admin":
        result = await db.execute(
            select(Projects).where(Projects.project_id == pid)
        )
    else:
        result = await db.execute(
            select(Projects).where(
                and_(
                    Projects.created_by == current_user.user_id,
                    Projects.project_id == pid,
                )
            )
        )

    del_project = result.scalar_one_or_none()

    if not del_project:
        raise HTTPException(
            status_code=404,
            detail="Project not found or you do not have permission to delete it",
        )

    await db.delete(del_project)
    await db.commit()

    return {"message": f"Project {del_project.project_name} deleted successfully"}
