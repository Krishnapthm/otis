from langgraph.graph import END, START, StateGraph

from src.agents.nodes.generation import (
    distractor_generator_node,
    options_generator_node,
    stem_generator_node,
)
from src.agents.nodes.validator import validator_node
from src.agents.utils.llm_config import (
    distractors_llm,
    options_llm,
    stem_llm,
    validator_llm,
)
from src.agents.utils.state import MCQDraft, QuestionSubgraphState

_SUBGRAPH_MAX_RETRIES = 2


async def stem_subgraph_node(state: QuestionSubgraphState) -> dict:
    return await stem_generator_node(state, stem_llm)


async def options_subgraph_node(state: QuestionSubgraphState) -> dict:
    return await options_generator_node(state, options_llm)


async def distractor_subgraph_node(state: QuestionSubgraphState) -> dict:
    return await distractor_generator_node(state, distractors_llm)


async def validator_subgraph_node(state: QuestionSubgraphState) -> dict:
    return await validator_node(state, validator_llm)


def _validation_route(state: QuestionSubgraphState) -> str:
    if state.get("validation_passed"):
        return "PASS"
    if state.get("retry_count", 0) >= _SUBGRAPH_MAX_RETRIES:
        return "FAIL"
    return "RETRY"


def _finalize_draft_node(state: QuestionSubgraphState) -> dict:
    draft = MCQDraft(
        question_index=state["question_index"],
        stem=state.get("stem", ""),
        options=state.get("options") or [],
        distractors=state.get("distractors") or [],
        answer=state.get("correct_answer"),
        explanation=state.get("explanation") or "",
        validation_feedback=state.get("validation_feedback") or None,
    )
    return {"draft": draft}


def build_question_subgraph():
    graph = StateGraph(QuestionSubgraphState)

    graph.add_node("stem_generator", stem_subgraph_node)
    graph.add_node("options_generator", options_subgraph_node)
    graph.add_node("distractor_generator", distractor_subgraph_node)
    graph.add_node("validator", validator_subgraph_node)
    graph.add_node("finalize_draft", _finalize_draft_node)

    graph.add_edge(START, "stem_generator")
    graph.add_edge("stem_generator", "options_generator")
    graph.add_edge("stem_generator", "distractor_generator")
    graph.add_edge("options_generator", "validator")
    graph.add_edge("distractor_generator", "validator")

    graph.add_conditional_edges(
        "validator",
        _validation_route,
        {
            "PASS": "finalize_draft",
            "RETRY": "stem_generator",
            "FAIL": "finalize_draft",
        },
    )
    graph.add_edge("finalize_draft", END)

    return graph.compile()
