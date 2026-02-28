from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import Mcqs
from src.api.db.schema import CreateMCQ, MCQ, Options, Questions, ReadMCQ


def _coerce_question(raw_question: dict[str, Any], fallback_index: int) -> Questions:
    options_raw = raw_question.get("options") or []
    normalized_options = []

    for i, option in enumerate(options_raw):
        if isinstance(option, dict):
            key = (
                option.get("key") or option.get("id") or ["A", "B", "C", "D"][min(i, 3)]
            )
            text = option.get("text", "")
        else:
            key = ["A", "B", "C", "D"][min(i, 3)]
            text = str(option)
        normalized_options.append(Options(key=key, text=text))

    right_answer = (
        raw_question.get("right_answer")
        or raw_question.get("answer")
        or (normalized_options[0].key if normalized_options else "A")
    )

    return Questions(
        question_index=raw_question.get(
            "question_index", raw_question.get("question_id", fallback_index)
        ),
        question=raw_question.get("question", ""),
        options=normalized_options,
        right_answer=right_answer,
        explanation=raw_question.get("explanation", ""),
    )


def _row_to_read_mcq(row: Mcqs) -> ReadMCQ:
    if row.questions:
        questions = [
            _coerce_question(question, idx)
            for idx, question in enumerate(row.questions or [])
        ]
    else:
        legacy_payload = (row.mcq or {}).get("mcq", {}) if row.mcq else {}
        legacy_questions = legacy_payload.get("questions") or []
        questions = [
            _coerce_question(question, idx)
            for idx, question in enumerate(legacy_questions)
        ]

    mcq_payload = MCQ(
        test_id=row.test_id or uuid.uuid4(),
        doc_ids=list(row.doc_ids or []),
        plan=row.plan or {},
        questions=questions,
        test_name=row.test_name or "Untitled MCQ Test",
        created_at=(row.created_at or row.generated_at or datetime.now(timezone.utc)),
    )

    return ReadMCQ(
        mcq_id=row.mcq_id,
        mcq=mcq_payload,
    )


async def create_mcq(db: AsyncSession, mcq: CreateMCQ) -> ReadMCQ:
    payload = mcq.mcq
    new_mcq = Mcqs(
        mcq=mcq.model_dump(mode="json"),
        test_id=payload.test_id,
        doc_ids=list(payload.doc_ids),
        plan=payload.plan,
        questions=[question.model_dump(mode="json") for question in payload.questions],
        created_at=payload.created_at,
        test_name=payload.test_name,
    )

    db.add(new_mcq)
    await db.commit()
    await db.refresh(new_mcq)

    return _row_to_read_mcq(new_mcq)


async def get_mcq(db: AsyncSession, mcq_id: uuid.UUID) -> list[ReadMCQ] | None:
    result = await db.execute(select(Mcqs).where(Mcqs.mcq_id == mcq_id))
    mcqs = result.scalars().all()

    if not mcqs:
        return None

    return [_row_to_read_mcq(row) for row in mcqs]


async def get_all_mcqs(
    db: AsyncSession, limit: int = 50, skip: int = 0
) -> list[ReadMCQ]:
    result = await db.execute(
        select(Mcqs)
        .order_by(
            Mcqs.created_at.desc().nullslast(), Mcqs.generated_at.desc().nullslast()
        )
        .offset(skip)
        .limit(limit)
    )
    mcqs = result.scalars().all()
    return [_row_to_read_mcq(row) for row in mcqs]
