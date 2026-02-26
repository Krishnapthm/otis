from langgraph.config import get_stream_writer

from src.agents.nodes.schemas import DistractorsOutput
from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.helpers import build_retrieved_context
from src.agents.utils.state import QuestionSubgraphState


async def distractor_generator_node(
    state: QuestionSubgraphState, distractors_llm
) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "distractor_generator",
            "status": "started",
            "label": f"Generating distractors for Q{state['question_index'] + 1}…",
        }
    )

    prompt = await PROMPT_REGISTRY["distractor_generation"].ainvoke(
        {
            "plan": state["plan"].model_dump_json(),
            "stem": state.get("stem", ""),
            "retrieved_context": build_retrieved_context(
                state.get("retrieved_chunks") or []
            ),
        }
    )
    result = await distractors_llm.with_structured_output(DistractorsOutput).ainvoke(
        prompt
    )

    writer(
        {
            "event": "node_update",
            "node": "distractor_generator",
            "status": "completed",
            "label": f"Generating distractors for Q{state['question_index'] + 1}…",
        }
    )

    return {"distractors": result.distractors}
