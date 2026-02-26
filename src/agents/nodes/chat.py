import json

from langgraph.config import get_stream_writer

from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.state import State


def _format_mcqs_for_display(state: State) -> str:
    rows = []
    for mcq in state.get("final_mcqs") or []:
        rows.append(f"Q{mcq.question_index + 1}. {mcq.question}")
        for option in mcq.options:
            rows.append(f"{option.key}. {option.text}")
        rows.append(f"Right Answer: {mcq.right_answer}")
        rows.append(f"Explanation: {mcq.explanation}")
        rows.append("")
    return "\n".join(rows).strip()


async def chat_no_tools_node(state: State, chat_llm) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "chat_no_tools",
            "status": "started",
            "label": "Preparing response…",
        }
    )

    user_message = ""
    messages = state.get("messages") or []
    if messages:
        last = messages[-1]
        user_message = last.get("content", "") if isinstance(last, dict) else str(last)

    final_mcq_text = _format_mcqs_for_display(state)
    tool_result = state.get("tool_result") or ""
    prompt = await PROMPT_REGISTRY["chat_no_tools"].ainvoke(
        {
            "session_summary": "",
            "final_mcqs": f"{final_mcq_text}\n\nTool result:\n{tool_result}".strip(),
            "user_message": user_message,
        }
    )
    response = await chat_llm.ainvoke(prompt)

    writer(
        {
            "event": "node_update",
            "node": "chat_no_tools",
            "status": "completed",
            "label": "Preparing response…",
        }
    )
    return {"messages": [response]}


async def chat_with_tools_node(state: State) -> dict:
    strategy = state.get("edit_strategy")
    if strategy == "patch":
        payload = {
            "tool": "patch_mcq",
            "status": "placeholder",
            "detail": "patch_mcq tool route is scaffolded but not implemented yet.",
            "edit_indices": state.get("edit_indices") or [],
        }
        return {
            "tool_result": json.dumps(payload),
            "artifact_bump": bool(state.get("edit_mode")),
        }
    return {
        "tool_result": "Tool-routing placeholder.",
        "artifact_bump": False,
    }
