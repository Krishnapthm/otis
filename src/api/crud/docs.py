from typing import List
from fastapi.responses import FileResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Documents, Projects, t_project_docs
from src.api.db.schema import  AuthResponse, DocBase, DocResponse
import uuid
from datetime import timezone, timedelta
from fastapi import HTTPException
from src.services.file_handling import delete_file, download_file, pdf_thumbnail, zip_files
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, insert

# IST = timezone(timedelta(hours=5, minutes=30))

# async def upload_new_doc(project_id: uuid.UUID, db: AsyncSession, docs: List[DocBase], current_user:AsyncSession):

#     result = await db.execute(select(Projects).options(selectinload(Projects.doc)).where(Projects.project_id == project_id))
#     project = result.scalar_one_or_none()

#     if not project:
#         raise HTTPException(status_code=404, detail="project does not exist")
    

#     db_docs = []
#     for doc in docs:
#         new_doc = Documents(
#             filename = doc.filename,
#             file_size = doc.file_size,
#             file_type = doc.file_type,
#             file_path = doc.file_path
#         )

#         db.add(new_doc)
#         db_docs.append(new_doc)

#     await db.flush()

#     await db.execute(insert(t_project_docs), [{"project_id": project_id, "doc_id": db_doc.doc_id} for db_doc in db_docs])

#     await db.commit()

#     for db_doc in db_docs:
#         await db.refresh(db_doc)

#     return [
#         DocResponse(
#             doc_id=db_doc.doc_id,
#             filename=db_doc.filename,
#             file_type=db_doc.file_type,
#             file_size=db_doc.file_size,
#             created_at=db_doc.created_at,
#             updated_at=db_doc.updated_at,
#             file_path=db_doc.file_path,
#             project_id=project_id

#         ).model_dump()
#         for db_doc in db_docs
#     ]

# async def get_doc(db: AsyncSession, did: uuid, project_id)-> List[DocResponse]:

#     result = await db.execute(select(Documents).join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id).where(t_project_docs.c.project_id == project_id))

#     document = result.scalars().all()

#     if not document:
#         raise HTTPException(status_code=404)
    
#     return [
#         DocResponse(
#             file_size=doc.file_size,
#             file_type=doc.file_type,
#             filename=doc.filename,
#             doc_id=doc.doc_id,
#             created_at=doc.created_at,
#             updated_at=doc.updated_at,
#             file_path=doc.file_path,
#             project_id=project_id
#         )
#         for doc in document
#     ] 

# async def get_all_docs(project_id: uuid.UUID, db: AsyncSession, limit: int=50, skip: int=0) -> List[DocResponse]:

#     result = await db.execute(select(Documents).offset(skip).limit(limit))
#     docs = result.scalars().all()

#     return [
#         DocResponse(
#             doc_id=doc.doc_id,
#             filename=doc.filename,
#             file_type=doc.file_type,
#             file_size = doc.file_size,
#             created_at=doc.created_at,
#             updated_at=doc.updated_at,
#             file_path=doc.file_path,
#             project_id=project_id
#         )
#         for doc in docs
#     ]

# async def delete_doc(db: AsyncSession, did: List[uuid.UUID])-> dict:

#     del_docs: List[Documents]=[]
#     for di in did:
#         result = await db.execute(select(Documents). where(Documents.doc_id==di))
#         del_docs.append(result.scalar_one_or_none())

#     # for del_doc in del_docs:
#     #     if not del_doc:
#     #         raise HTTPException(status_code=404, detail=f"Document does not exist")
        

#     # del_doc_name = del_doc.filename

#     for del_doc in del_docs:

#         del_doc_name = del_doc.filename

#         if await delete_file(del_doc_name):
#             await db.delete(del_doc)

#         await db.commit()

#         return {
#             "message": f"{del_doc_name} deleted successfully"
#         }
    
# async def download_doc(db: AsyncSession, project_id)-> List[FileResponse]:
#     result = await db.execute(
#         select(Documents.filename)
#         .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
#         .where(t_project_docs.c.project_id == project_id)
#     )
#     down_docs = result.scalars().all()

#     if not down_docs:
#         raise HTTPException(status_code=404, detail="Document does not exist")
    
#     if len(down_docs) == 1:
#         return download_file(down_docs[0])
    
#     return await zip_files(down_docs)

# # async def delete_docs(db: AsyncSession, project_id):


# [Auth Change] Function now uses current_user.user_id to verify project ownership
async def upload_new_doc(project_id: uuid.UUID, db: AsyncSession, docs: List[DocBase], current_user: AuthResponse):

    # [Auth Change] Added filter: Projects.created_by == current_user.user_id
    result = await db.execute(
        select(Projects)
        .options(selectinload(Projects.doc))
        .where(and_(Projects.project_id == project_id, Projects.created_by == current_user.user_id))
    )
    project = result.scalar_one_or_none()

    # [Auth Change] If project exists but belongs to another user, this returns None, raising 404 (secure)
    if not project:
        raise HTTPException(status_code=404, detail="Project does not exist or you do not have access")

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
            file_path=db_doc.file_path,
            project_id=project_id

        ).model_dump()
        for db_doc in db_docs
    ]

# [Auth Change] Added user_id to parameters
async def get_doc(db: AsyncSession, did: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID)-> List[DocResponse]:

    # [Auth Change] Joined with Projects to ensure the project belongs to the user
    result = await db.execute(
        select(Documents)
        .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
        .join(Projects, t_project_docs.c.project_id == Projects.project_id) # Join Project
        .where(and_(t_project_docs.c.project_id == project_id, Projects.created_by == user_id)) # Check ownership
    )

    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404)
    
    return DocResponse(
            file_size=document.file_size,
            file_type=document.file_type,
            filename=document.filename,
            doc_id=document.doc_id,
            created_at=document.created_at,
            updated_at=document.updated_at,
            file_path=document.file_path,
            project_id=project_id
        )
        

# [Auth Change] Added user_id to parameters
async def get_all_docs(project_id: uuid.UUID, db: AsyncSession, user_id: uuid.UUID, limit: int=50, skip: int=0) -> List[DocResponse]:

    # [Auth Change] Complex query needed to verify project ownership before returning docs
    # We join Documents -> ProjectDocs -> Projects -> Check UserID
    result = await db.execute(
        select(Documents)
        .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
        .join(Projects, t_project_docs.c.project_id == Projects.project_id)
        .where(and_(Projects.project_id == project_id, Projects.created_by == user_id))
        .offset(skip)
        .limit(limit)
    )
    docs = result.scalars().all()

    return [
        DocResponse(
            doc_id=doc.doc_id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size = doc.file_size,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            file_path=doc.file_path,
            project_id=project_id
        )
        for doc in docs
    ]

# [Auth Change] Added user_id to parameters
async def delete_doc(db: AsyncSession, did: List[uuid.UUID], user_id: uuid.UUID)-> dict:

    del_docs: List[Documents]=[]
    for di in did:
        # [Auth Change] Verify the doc belongs to a project owned by the user before selecting
        result = await db.execute(
            select(Documents)
            .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
            .join(Projects, t_project_docs.c.project_id == Projects.project_id)
            .where(and_(Documents.doc_id == di, Projects.created_by == user_id))
        )
        doc = result.scalar_one_or_none()
        
        # [Auth Change] If doc exists but user doesn't own the project, this will be None
        if doc:
            del_docs.append(doc)

    # [Auth Change] If no docs were found (or user didn't own them), raise 404
    if not del_docs:
         raise HTTPException(status_code=404, detail="Documents do not exist or you do not have permission")

    for del_doc in del_docs:

        del_doc_name = del_doc.filename

        if await delete_file(del_doc_name):
            await db.delete(del_doc)

        await db.commit()

        return {
            "message": f"{del_doc_name} deleted successfully"
        }
    
# [Auth Change] Added user_id to parameters
async def download_doc(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID)-> List[FileResponse]:
    result = await db.execute(
        select(Documents.filename)
        .join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id)
        .join(Projects, t_project_docs.c.project_id == Projects.project_id) # Join Projects
        .where(and_(t_project_docs.c.project_id == project_id, Projects.created_by == user_id)) # Check ownership
    )
    down_docs = result.scalars().all()

    if not down_docs:
        raise HTTPException(status_code=404, detail="Document does not exist or access denied")
    
    if len(down_docs) == 1:
        return download_file(down_docs[0])
    
    return await zip_files(down_docs)

async def doc_thumbnail(doc_id: uuid.UUID, db: AsyncSession)-> FileResponse:

    result = await db.execute(select(Documents.file_path).where(Documents.doc_id==doc_id))
    file_path = result.scalar_one_or_none()

    return pdf_thumbnail(file_path)