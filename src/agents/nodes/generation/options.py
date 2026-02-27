from langgraph.config import get_stream_writer

from src.agents.nodes.schemas import OptionsOutput
from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.helpers import build_plan_context
from src.agents.utils.state import QuestionSubgraphState


async def options_generator_node(state: QuestionSubgraphState, options_llm) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "options_generator",
            "status": "started",
            "label": f"Building options for Q{state['question_index'] + 1}…",
        }
    )

    prompt = await PROMPT_REGISTRY["options_generation"].ainvoke(
        {
            "plan": build_plan_context(state["plan"], include_concepts=False),
            "stem": state.get("stem", ""),
            "distractor_strategy": state["plan"].distractor_strategy,
        }
    )
    result = await options_llm.with_structured_output(OptionsOutput).ainvoke(prompt)

    writer(
        {
            "event": "node_update",
            "node": "options_generator",
            "status": "completed",
            "label": f"Building options for Q{state['question_index'] + 1}…",
        }
    )

    return {
        "options": result.options,
        "correct_answer": result.correct_answer,
        "explanation": result.explanation,
    }
