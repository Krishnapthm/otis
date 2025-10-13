from pydantic import parse_obj_as
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Documents, Mcqs
from src.api.db.schema import CreateMCQ, DocBase, DocResponse, ReadMCQ, MCQ
import uuid
import datetime

async def create_mcq(db: AsyncSession, mcq: CreateMCQ)-> ReadMCQ:
    new_mcq = Mcqs(
        mcq = mcq.model_dump(mode="json"),
        generated_at = datetime.datetime.utcnow()
    )

    db.add(new_mcq)
    await db.commit()
    await db.refresh(new_mcq)
    # mcq_obj =  MCQ.model_validate(new_mcq.mcq)

    return ReadMCQ(
        id=new_mcq.id,
        project=new_mcq.project,
        mcq=mcq.mcq,
        generated_at=new_mcq.generated_at
    )

async def get_mcq(db: AsyncSession, mcq_id: uuid)-> ReadMCQ | None:
    result = await db.execute(select(Mcqs).where(Mcqs.id == mcq_id))
    mcq = result.scalars().all()

    if not mcq:
        return None
    return [
        ReadMCQ(
            id=m.id,
            project=m.project,
            generated_at=m.generated_at,
            mcq=MCQ.model_validate(m.mcq.get("mcq"))
        )
        for m in mcq
    ]

async def get_all_mcqs(db: AsyncSession, limit: int=20, skip: int=0):
    result = await db.execute(select(Mcqs).offset(skip).limit(limit))
    mcqs = result.scalars().all()

    return [
        ReadMCQ(
            id=m.id,
            project=m.project,
            generated_at=m.generated_at,
            mcq=MCQ.model_validate(m.mcq.get("mcq"))
        )
        for m in mcqs
    ]

async def upload_new_doc(db: AsyncSession, docs: DocBase):
    new_doc = Documents(
        filename = docs.filename,
        file_size = docs.file_size,
        file_type = docs.file_type
    )

    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    return DocResponse(
        doc_id=new_doc.doc_id,
        filename=new_doc.filename,
        file_type=new_doc.file_type,
        file_size=new_doc.file_size,
        created_at=new_doc.created_at,
        updated_at=new_doc.updated_at,
    )

