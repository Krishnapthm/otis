from typing import List
from fastapi import HTTPException
from openai import project
from regex import D
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import LangchainPgCollection
from src.api.db.models import Documents, t_project_docs, EmbeddingVersions
from src.api.db.models.session import get_db
from src.api.db.schema import EmbeddingVersionResponse
import uuid
from datetime import timezone, timedelta
from src.services.embedding_service import embed_docs
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, insert

IST = timezone(timedelta(hours=5, minutes=30))

async def create_embeddings(project_id: uuid.UUID, db: AsyncSession)-> EmbeddingVersionResponse:

    result = await db.execute(select(EmbeddingVersions).where(EmbeddingVersions.project_id==project_id))
    version_result = result.scalars().all()

    version_number: int = 1

    if version_result[-1].version_number>=version_number:
        version_number = version_result[-1].version_number+1

    collection_name = f"project_{project_id}_v{version_number}"

    result = await db.execute(select(Documents).join(t_project_docs, Documents.doc_id == t_project_docs.c.doc_id).where(t_project_docs.c.project_id == project_id))

    documents = result.scalars().all()

    file_path=[doc.file_path for doc in documents]

    doc_count =  await embed_docs(file_path, collection_name)

    if doc_count:
        result = await db.execute(select(LangchainPgCollection.id).where(LangchainPgCollection.name==collection_name))
        col_id = result.scalar_one_or_none()

    embedding_version = EmbeddingVersions(
        project_id=project_id,
        collection_id=col_id,
        version_number=version_number,
        is_active=False,
        document_count=doc_count
    )

    db.add(embedding_version)
    await db.commit()
    await db.refresh(embedding_version)

    ist_time = embedding_version.created_at.replace(tzinfo=timezone.utc).astimezone(IST)


    return EmbeddingVersionResponse(
        version_id=embedding_version.version_id,
        project_id=embedding_version.project_id,
        collection_id=embedding_version.collection_id,
        version_number=embedding_version.version_number,
        is_active=embedding_version.is_active,
        desc=embedding_version.description,
        doc_count=embedding_version.document_count,
        created_at=ist_time
    )

async def list_embeddings(project_id: uuid.UUID, db: AsyncSession)-> List[EmbeddingVersionResponse]:

    result = await db.execute(select(EmbeddingVersions).where(EmbeddingVersions.project_id==project_id))

    if not result:
        raise HTTPException(status_code=404, detail="project does not exist")

    embedding_versions = result.scalars().all()

    return [
        EmbeddingVersionResponse(
            version_id=embedding_version.version_id,
            project_id=embedding_version.project_id,
            collection_id=embedding_version.collection_id,
            version_number=embedding_version.version_number,
            is_active=embedding_version.is_active,
            desc=embedding_version.description,
            doc_count=embedding_version.document_count,
            created_at=embedding_version.created_at
        )
        for embedding_version in embedding_versions
    ]

async def delete_embedding(project_id: uuid.UUID, version_ids: List[uuid.UUID], db: AsyncSession)-> dict:

    await db.execute(
        delete(EmbeddingVersions).where(
            EmbeddingVersions.project_id == project_id,
            EmbeddingVersions.version_id.in_(version_ids)
        )
    )
    await db.commit()
    return {"deleted_count": len(version_ids)}
    # del_versions=(
    #     await db.execute(
    #         select(EmbeddingVersions).where(
    #             EmbeddingVersions.project_id==project_id, 
    #             EmbeddingVersions.version_id.in_(version_ids)
    #         )
    #     )
    # ).scalars().all()
    

    # for del_version in del_versions:
    #     await db.delete(del_version) 

    # await db.commit() 


