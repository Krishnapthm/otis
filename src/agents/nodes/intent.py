from langgraph.config import get_stream_writer

from src.agents.nodes.schemas import IntentResult
from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.state import State


async def intent_classifier_node(state: State, intent_llm) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "intent_classifier",
            "status": "started",
            "label": "Understanding your request…",
        }
    )

    messages = state.get("messages") or []
    user_message = ""
    if messages:
        last = messages[-1]
        user_message = last.get("content", "") if isinstance(last, dict) else str(last)

    prompt = await PROMPT_REGISTRY["intent_classifier"].ainvoke(
        {
            "session_summary": "",
            "user_message": user_message,
        }
    )
    result = await intent_llm.with_structured_output(IntentResult).ainvoke(prompt)

    writer(
        {
            "event": "node_update",
            "node": "intent_classifier",
            "status": "completed",
            "label": "Understanding your request…",
            "detail": result.intent,
        }
    )
    return {"intent": result}
