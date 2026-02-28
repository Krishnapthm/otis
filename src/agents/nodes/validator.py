import json

from src.agents.nodes.schemas import ValidatorOutput
from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.helpers import build_plan_context, build_retrieved_context
from src.agents.utils.state import QuestionSubgraphState


async def validator_node(state: QuestionSubgraphState, validator_llm) -> dict:
    options_payload = [
        option.model_dump(mode="json") if hasattr(option, "model_dump") else option
        for option in (state.get("options") or [])
    ]
    draft_payload = {
        "stem": state.get("stem"),
        "options": options_payload,
        "correct_answer": state.get("correct_answer"),
    }
    prompt = await PROMPT_REGISTRY["validator"].ainvoke(
        {
            "plan": build_plan_context(state["plan"], include_concepts=False),
            "draft": json.dumps(draft_payload, ensure_ascii=False),
            "retrieved_context": build_retrieved_context(
                state.get("retrieved_chunks") or []
            ),
        }
    )
    validation = await validator_llm.with_structured_output(ValidatorOutput).ainvoke(
        prompt
    )

    retry_count = state.get("retry_count", 0)
    if not validation.validation_passed:
        retry_count += 1

    return {
        "validation_passed": validation.validation_passed,
        "validation_feedback": validation.validation_feedback,
        "retry_count": retry_count,
    }
