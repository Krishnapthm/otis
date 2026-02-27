from langgraph.config import get_stream_writer

from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.helpers import build_plan_context, build_retrieved_context
from src.agents.utils.state import QuestionSubgraphState


async def stem_generator_node(state: QuestionSubgraphState, stem_llm) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "stem_generator",
            "status": "started",
            "label": f"Drafting stem for Q{state['question_index'] + 1}…",
        }
    )

    prompt = await PROMPT_REGISTRY["stem_generation"].ainvoke(
        {
            "question_index": state["question_index"],
            "plan": build_plan_context(state["plan"], include_concepts=True),
            "retrieved_context": build_retrieved_context(
                state.get("retrieved_chunks") or []
            ),
        }
    )
    response = await stem_llm.ainvoke(prompt)

    stem = (
        response.content if isinstance(response.content, str) else str(response.content)
    )
    return {"stem": stem.strip()}
