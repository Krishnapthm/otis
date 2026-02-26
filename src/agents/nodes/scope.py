from langgraph.config import get_stream_writer

from src.agents.nodes.schemas import ScopeClassification
from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.state import State


async def scope_classifier_node(state: State, guardrail_llm) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "scope_classifier",
            "status": "started",
            "label": "Checking scope…",
        }
    )

    messages = state.get("messages") or []
    user_message = ""
    if messages:
        last = messages[-1]
        user_message = last.get("content", "") if isinstance(last, dict) else str(last)

    prompt = await PROMPT_REGISTRY["scope_classifier"].ainvoke(
        {"user_request": user_message}
    )
    result = await guardrail_llm.with_structured_output(ScopeClassification).ainvoke(
        prompt
    )

    writer(
        {
            "event": "node_update",
            "node": "scope_classifier",
            "status": "completed",
            "label": "Checking scope…",
        }
    )
    return {"before_agent_guardrail": result}
