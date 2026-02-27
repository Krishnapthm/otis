"""Pure utility / helper functions shared across agent nodes."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Set

from src.agents.utils.state import State, TestGenerationPlan


def resolve_user_prompt(state: State) -> str:
    """Extract the user prompt from state, falling back to the last chat message."""
    if state.get("user_prompt"):
        return state["user_prompt"]

    chat_messages = state.get("messages") or state.get("chat_messages") or []
    if not chat_messages:
        return ""

    last_message = chat_messages[-1]
    if isinstance(last_message, dict):
        return str(last_message.get("content", ""))
    return str(getattr(last_message, "content", ""))


def build_retrieved_context(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into a numbered context string for LLM prompts."""
    if not retrieved_chunks:
        return ""

    sections: List[str] = []
    for index, chunk in enumerate(retrieved_chunks, 1):
        file_name = chunk.get("metadata", {}).get("file_name", "unknown")
        sections.append(f"[{index}] source={file_name}\n" f"{chunk.get('content', '')}")
    return "\n\n".join(sections)


def build_plan_context(plan: TestGenerationPlan, *, include_concepts: bool) -> str:
    """Return a compact JSON plan payload for LLM prompts."""
    payload = {
        "topic": plan.topic,
        "difficulty": plan.difficulty,
        "blooms_level": plan.blooms_level,
        "stem_guidance": plan.stem_guidance,
        "distractor_strategy": plan.distractor_strategy,
    }
    if include_concepts:
        payload["concepts"] = [
            {"name": concept.name, "summary": concept.summary}
            for concept in plan.concepts
        ]
    return json.dumps(payload, ensure_ascii=False)


def deduplicate_queries(
    queries: List[str], *, max_count: int | None = None
) -> List[str]:
    """Return unique, non-empty queries preserving insertion order."""
    unique: List[str] = []
    seen: Set[str] = set()
    for query in queries:
        normalized = query.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            unique.append(normalized)
        if max_count is not None and len(unique) >= max_count:
            break
    return unique
