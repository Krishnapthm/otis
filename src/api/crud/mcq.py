from typing import List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Mcqs
from src.api.db.schema import CreateMCQ, ReadMCQ, MCQ
import uuid
from datetime import timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlalchemy import insert

IST = timezone(timedelta(hours=5, minutes=30))

async def create_mcq(db: AsyncSession, mcq: CreateMCQ)-> ReadMCQ:
    new_mcq = Mcqs(
        mcq = mcq.model_dump(mode="json"),
    )

    db.add(new_mcq)
    await db.commit()
    await db.refresh(new_mcq)

    ist_time = new_mcq.generated_at.replace(tzinfo=timezone.utc).astimezone(IST)

    return ReadMCQ(
        mcq_id=new_mcq.mcq_id,
        mcq=mcq.mcq,
        generated_at=ist_time
    )

async def get_mcq(db: AsyncSession, mcq_id: uuid)-> ReadMCQ | None:
    result = await db.execute(select(Mcqs).where(Mcqs.mcq_id == mcq_id))
    mcq = result.scalars().all()

    if not mcq:
        return None
    return [
        ReadMCQ(
            mcq_id=m.mcq_id,
            generated_at=m.generated_at,
            mcq=MCQ.model_validate(m.mcq.get("mcq"))
        )
        for m in mcq
    ]

async def get_all_mcqs(db: AsyncSession, limit: int=50, skip: int=0):
    result = await db.execute(select(Mcqs).offset(skip).limit(limit))
    mcqs = result.scalars().all()

    return [
        ReadMCQ(
            mcq_id=m.mcq_id,
            generated_at=m.generated_at,
            mcq=MCQ.model_validate(m.mcq.get("mcq"))
        )
        for m in mcqs
    ]



