import json

from langgraph.config import get_stream_writer

from src.agents.nodes.schemas import PlannerOutput
from src.agents.prompts import PROMPT_REGISTRY
from src.agents.utils.helpers import resolve_user_prompt
from src.agents.utils.state import State


async def planner_node(state: State, planner_llm) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "planner",
            "status": "started",
            "label": "Planning your MCQs…",
        }
    )

    user_message = resolve_user_prompt(state)
    previous_plan = state.get("plan")
    prompt = await PROMPT_REGISTRY["planner"].ainvoke(
        {
            "user_message": user_message,
            "session_summary": "",
            "previous_plan": json.dumps(
                previous_plan.model_dump() if previous_plan else {}, ensure_ascii=False
            ),
            "validation_feedback": state.get("validation_feedback", ""),
        }
    )

    plan_output = await planner_llm.with_structured_output(PlannerOutput).ainvoke(
        prompt
    )
    plan_version = (state.get("plan_version") or 0) + 1

    writer(
        {
            "event": "node_update",
            "node": "planner",
            "status": "completed",
            "label": "Planning your MCQs…",
            "detail": f"{plan_output.num_questions} question(s)",
        }
    )

    edit_indices = list(plan_output.edit_indices)
    if plan_output.edit_target == "all":
        edit_indices = list(range(plan_output.num_questions))

    return {
        "plan": plan_output,
        "plan_version": plan_version,
        "edit_mode": plan_output.edit_mode,
        "edit_target": plan_output.edit_target,
        "edit_indices": edit_indices,
        "edit_strategy": plan_output.edit_strategy,
    }
