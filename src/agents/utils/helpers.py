"""Pure utility / helper functions shared across agent nodes."""

from __future__ import annotations

from typing import Any, Dict, List, Set

from src.agents.utils.state import State


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
        sections.append(
            f"[{index}] doc_id={chunk.get('doc_id')} "
            f"chunk_id={chunk.get('chunk_id')} source={file_name}\n"
            f"{chunk.get('content', '')}"
        )
    return "\n\n".join(sections)


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
