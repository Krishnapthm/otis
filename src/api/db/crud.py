from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Mcqs
from src.api.db.schema import CreateMCQ, ReadMCQ, MCQ
import uuid
import datetime

async def create_mcq(db: AsyncSession, mcq: CreateMCQ)-> ReadMCQ:
    new_mcq = Mcqs(
        project = mcq.project,
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

async def get_mcq(db: AsyncSession, mcq_id: uuid.UUID)-> ReadMCQ | None:
    result = await db.execute(select(Mcqs).where(Mcqs.id == mcq_id))
    mcq = result.scalars().first()

    if not mcq:
        return None
    return ReadMCQ.model_validate(mcq.__dict__)

async def get_all_mcqs(db: AsyncSession, limit: int=20, skip: int=0):
    result = await db.execute(select(Mcqs).offset(skip).limit(limit))
    mcqs = result.scalars().all()

    return [ReadMCQ.model_validate(m.__dict__) for m in mcqs]

