import json

from src.agents.nodes.schemas import ValidatorOutput
from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.state import QuestionSubgraphState


async def validator_node(state: QuestionSubgraphState, validator_llm) -> dict:
    draft_payload = {
        "stem": state.get("stem"),
        "options": state.get("options") or [],
        "correct_answer": state.get("correct_answer"),
        "distractors": state.get("distractors") or [],
    }
    prompt = await PROMPT_REGISTRY["validator"].ainvoke(
        {
            "plan": state["plan"].model_dump_json(),
            "draft": json.dumps(draft_payload, ensure_ascii=False),
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
