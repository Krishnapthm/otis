from collections import UserDict
from typing import List
from fastapi import HTTPException
from openai import project
from regex import D
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import VersionDocuments, Documents, t_project_docs, EmbeddingVersions, Projects, LangchainPgCollection
from src.api.db.models.session import get_db
from src.api.db.schema import EmbeddingVersionResponse
import uuid
from datetime import timezone, timedelta
from src.services.embedding_service import embed_docs
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, insert

IST = timezone(timedelta(hours=5, minutes=30))

async def create_embeddings(version_name, project_id: uuid.UUID, db: AsyncSession, doc_id: List[uuid.UUID]) -> EmbeddingVersionResponse:
    # Fetch existing versions (sorted)
    result = await db.execute(
        select(EmbeddingVersions)
        .where(EmbeddingVersions.project_id == project_id)
        .order_by(EmbeddingVersions.version_number.asc())
    )
    versions = result.scalars().all()

    # Determine version number safely
    version_number = (versions[-1].version_number + 1) if versions else 1

    collection_name = f"project_{project_id}_v{version_number}"

    # Fetch documents
    result = await db.execute(
        select(Documents)
        .join(t_project_docs)
        .where(
            t_project_docs.c.project_id == project_id,
            t_project_docs.c.doc_id.in_(doc_id),
        )
    )
    documents = result.scalars().all()
    file_paths = [doc.file_path for doc in documents]

    # Create embeddings
    doc_count = await embed_docs(file_paths, collection_name)

    col_id = None
    if doc_count:
        result = await db.execute(
            select(LangchainPgCollection.id).where(
                LangchainPgCollection.name == collection_name
            )
        )
        col_id = result.scalar_one_or_none()

    # Create embedding version
    embedding_version = EmbeddingVersions(
        version_name=version_name,
        project_id=project_id,
        collection_id=col_id,
        version_number=version_number,
        is_active=False,
        document_count=doc_count,
    )

    db.add(embedding_version)
    await db.flush()  # ensure version_id is populated

    # Add version-document relations
    version_documents = [
        VersionDocuments(
            version_id=embedding_version.version_id,
            document_id=did,
        )
        for did in doc_id
    ]
    db.add_all(version_documents)

    # Commit
    await db.commit()
    await db.refresh(embedding_version)

    # Timezone conversion
    created_at = embedding_version.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    ist_time = created_at.astimezone(IST)

    return EmbeddingVersionResponse(
        version_name=version_name,
        version_id=embedding_version.version_id,
        project_id=embedding_version.project_id,
        collection_id=embedding_version.collection_id,
        version_number=embedding_version.version_number,
        is_active=embedding_version.is_active,
        desc=embedding_version.description,
        doc_count=embedding_version.document_count,
        created_at=ist_time,
    )

async def list_embeddings(project_id: uuid.UUID, db: AsyncSession)-> List[EmbeddingVersionResponse]:

    result = await db.execute(select(EmbeddingVersions).where(EmbeddingVersions.project_id==project_id))

    if not result:
        raise HTTPException(status_code=404, detail="project does not exist")

    embedding_versions = result.scalars().all()

    return [
    EmbeddingVersionResponse(
        version_name=embedding_version.version_name,
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


