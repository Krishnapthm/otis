from typing import List
from fastapi.responses import FileResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Documents, Projects, t_project_docs
from src.api.db.schema import  DocBase, DocResponse
import uuid
from datetime import timezone, timedelta
from fastapi import HTTPException
from src.file_handling import delete_file, download_file, zip_files
from sqlalchemy.orm import selectinload
from sqlalchemy import insert

IST = timezone(timedelta(hours=5, minutes=30))

async def upload_new_doc(project_id: uuid.UUID, db: AsyncSession, docs: List[DocBase]):

    result = await db.execute(select(Projects).options(selectinload(Projects.doc)).where(Projects.project_id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="project does not exist")
    

    db_docs = []
    for doc in docs:
        new_doc = Documents(
            filename = doc.filename,
            file_size = doc.file_size,
            file_type = doc.file_type,
            file_path = doc.file_path
        )

        db.add(new_doc)
        db_docs.append(new_doc)

    await db.flush()

    await db.execute(insert(t_project_docs), [{"project_id": project_id, "doc_id": db_doc.doc_id} for db_doc in db_docs])

    await db.commit()

    for db_doc in db_docs:
        await db.refresh(db_doc)

    return [
        DocResponse(
            doc_id=db_doc.doc_id,
            filename=db_doc.filename,
            file_type=db_doc.file_type,
            file_size=db_doc.file_size,
            created_at=db_doc.created_at,
            updated_at=db_doc.updated_at,
            file_path=db_doc.file_path
        ).model_dump()
        for db_doc in db_docs
    ]

async def get_doc(db: AsyncSession, did: uuid)-> DocResponse:

    result = await db.execute(select(Documents).where(Documents.doc_id==did))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404)
    
    return DocResponse(
        file_size=document.file_size,
        file_type=document.file_type,
        filename=document.filename,
        doc_id=document.doc_id,
        created_at=document.created_at,
        updated_at=document.updated_at

    )

async def get_all_docs(db: AsyncSession, limit: int=50, skip: int=0) -> List[DocResponse]:

    result = await db.execute(select(Documents).offset(skip).limit(limit))
    docs = result.scalars().all()

    return [
        DocResponse(
            doc_id=doc.doc_id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size = doc.file_size,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            file_path=doc.file_path
        )
        for doc in docs
    ]

async def delete_doc(db: AsyncSession, did: uuid)-> dict:

    result = await db.execute(select(Documents). where(Documents.doc_id==did))
    del_doc = result.scalar_one_or_none()

    if not del_doc:
        raise HTTPException(status_code=404, detail="Document does not exist")

    del_doc_name = del_doc.filename

    if await delete_file(del_doc_name):
        await db.delete(del_doc)
        await db.commit()

        return {
            "message": f"{del_doc_name} deleted successfully"
        }

async def download_doc(db: AsyncSession, project_id)-> List[FileResponse]:
    result = await db.execute(
        select(Documents.filename)
        .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
        .where(t_project_docs.c.project_id == project_id)
    )
    down_docs = result.scalars().all()

    if not down_docs:
        raise HTTPException(status_code=404, detail="Document does not exist")
    
    if len(down_docs) == 1:
        return download_file(down_docs[0])
    
    return await zip_files(down_docs)

