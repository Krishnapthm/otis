from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud import create_mcq
from src.api.db.schema import CreateMCQ, MCQ, Options, Questions, ReadMCQ


def _to_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return dict(value)


def _build_questions(final_mcqs: list[Any]) -> list[Questions]:
    questions: list[Questions] = []

    for index, question in enumerate(final_mcqs):
        question_dict = _to_dict(question)
        options_raw = question_dict.get("options") or []

        options = [
            Options(
                key=(option.get("key") or "A"),
                text=(option.get("text") or ""),
            )
            for option in options_raw
        ]

        questions.append(
            Questions(
                question_index=question_dict.get("question_index", index),
                question=question_dict.get("question", ""),
                options=options,
                right_answer=question_dict.get("right_answer", "A"),
                explanation=question_dict.get("explanation", ""),
            )
        )

    return questions


def _derive_test_name(state: dict[str, Any]) -> str:
    plan = _to_dict(state.get("plan"))
    topic = (plan.get("topic") or "").strip()
    if topic:
        return f"{topic} MCQ Test"
    return "Untitled MCQ Test"


async def persist_generated_mcq_test_from_state(
    db: AsyncSession,
    state: dict[str, Any],
    *,
    test_name: str | None = None,
) -> ReadMCQ | None:
    final_mcqs = state.get("final_mcqs") or []
    if not final_mcqs:
        return None

    plan = _to_dict(state.get("plan"))
    mcq_payload = MCQ(
        doc_ids=list(state.get("doc_ids") or []),
        plan=plan,
        questions=_build_questions(final_mcqs),
        test_name=(test_name or _derive_test_name(state)),
        created_at=datetime.utcnow(),
    )

    # TODO(HITL): When revision/HITL is introduced, resolve whether this run creates
    # a new test artifact or revises an existing one, then persist revision metadata
    # (parent test linkage, revision reason, approver/user action, and timestamps).
    return await create_mcq(db, CreateMCQ(mcq=mcq_payload))
