from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from src.agents.mcq_subgraph import build_question_subgraph
from src.agents.nodes import (
    assemble_final_mcqs_node,
    chat_no_tools_node,
    chat_with_tools_node,
    finalize_metadata_node,
    intent_classifier_node,
    planner_node,
    retrieval_node,
    scope_classifier_node,
)
from src.agents.utils.llm_config import (
    chat_no_tools_llm,
    guardrail_llm,
    intent_llm,
    planner_llm,
)
from src.agents.utils.state import State

question_subgraph = build_question_subgraph()


async def scope_classifier_graph_node(state: State) -> dict:
    return await scope_classifier_node(state, guardrail_llm)


async def intent_classifier_graph_node(state: State) -> dict:
    return await intent_classifier_node(state, intent_llm)


async def planner_graph_node(state: State) -> dict:
    return await planner_node(state, planner_llm)


async def chat_model_graph_node(state: State) -> dict:
    return await chat_no_tools_node(state, chat_no_tools_llm)


def route_scope(state: State) -> str:
    decision = state.get("before_agent_guardrail")
    if decision and getattr(decision, "intent", "BLOCK") == "ALLOW":
        return "ALLOW"
    return "BLOCK"


def route_intent(state: State) -> str:
    intent = getattr(state.get("intent"), "intent", "clarification")
    if intent in {"mcq_request", "followup"}:
        return "PLAN"
    if intent == "utility_task":
        return "TOOLS"
    return "CHAT"


def route_after_planner(state: State) -> str:
    if state.get("edit_mode") and state.get("edit_strategy") == "patch":
        return "PATCH"
    return "GENERATE"


def question_fanout_router(state: State):
    plan = state.get("plan")
    if not plan:
        return []

    num_questions = max(plan.num_questions, 1)
    edit_mode = state.get("edit_mode", False)
    targeted = set(state.get("edit_indices") or [])

    if edit_mode and targeted:
        question_indices = sorted(
            index for index in targeted if 0 <= index < num_questions
        )
    else:
        question_indices = list(range(num_questions))

    existing_map = {
        draft.question_index: draft for draft in (state.get("existing_drafts") or [])
    }

    sends = []
    for question_index in question_indices:
        sends.append(
            Send(
                "question_subgraph_runner",
                {
                    "plan": plan,
                    "question_index": question_index,
                    "retrieved_chunks": state.get("retrieved_chunks") or [],
                    "retry_count": 0,
                    "existing_draft": existing_map.get(question_index),
                },
            )
        )
    return sends


def route_after_tools(state: State) -> str:
    if state.get("artifact_bump"):
        return "BUMP"
    return "CHAT"


def route_retrieval_gate(state: State) -> str:
    chunks = state.get("retrieved_chunks") or []
    return "HAVE_CHUNKS" if len(chunks) > 0 else "NO_CHUNKS"


async def question_subgraph_runner_node(state: State) -> dict:
    result = await question_subgraph.ainvoke(
        {
            "plan": state.get("plan"),
            "question_index": state.get("question_index"),
            "retrieved_chunks": state.get("retrieved_chunks") or [],
            "retry_count": state.get("retry_count", 0),
            "existing_draft": state.get("existing_draft"),
        }
    )
    draft = result.get("draft")
    return {"mcq_drafts": [draft]} if draft else {"mcq_drafts": []}


async def dispatch_questions_node(_: State) -> dict:
    return {}


async def require_retrieved_chunks_node(state: State) -> dict:
    chunks = state.get("retrieved_chunks") or []
    if chunks:
        return {}

    return {
        "tool_result": (
            "MCQ generation was stopped because retrieval returned no context chunks. "
            "Please attach/select relevant documents or refine the request and try again."
        )
    }


def create_chat_builder() -> StateGraph:
    workflow = StateGraph(State)

    workflow.add_node("scope_classifier", scope_classifier_graph_node)
    workflow.add_node("intent_classifier", intent_classifier_graph_node)
    workflow.add_node("planner", planner_graph_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("require_retrieved_chunks", require_retrieved_chunks_node)
    workflow.add_node("dispatch_questions", dispatch_questions_node)
    workflow.add_node("question_subgraph_runner", question_subgraph_runner_node)
    workflow.add_node("assemble_final_output", assemble_final_mcqs_node)
    workflow.add_node("finalize_metadata", finalize_metadata_node)
    workflow.add_node("chat_model", chat_model_graph_node)
    workflow.add_node("chat_tools", chat_with_tools_node)

    workflow.add_edge(START, "scope_classifier")
    workflow.add_conditional_edges(
        "scope_classifier",
        route_scope,
        {
            "ALLOW": "intent_classifier",
            "BLOCK": END,
        },
    )

    workflow.add_conditional_edges(
        "intent_classifier",
        route_intent,
        {
            "PLAN": "planner",
            "TOOLS": "chat_tools",
            "CHAT": "chat_model",
        },
    )

    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "PATCH": "chat_tools",
            "GENERATE": "retrieval",
        },
    )

    workflow.add_edge("retrieval", "require_retrieved_chunks")
    workflow.add_conditional_edges(
        "require_retrieved_chunks",
        route_retrieval_gate,
        {
            "HAVE_CHUNKS": "dispatch_questions",
            "NO_CHUNKS": "chat_model",
        },
    )
    workflow.add_conditional_edges("dispatch_questions", question_fanout_router)
    workflow.add_edge("question_subgraph_runner", "assemble_final_output")
    workflow.add_edge("assemble_final_output", "finalize_metadata")
    workflow.add_edge("finalize_metadata", "chat_model")

    workflow.add_conditional_edges(
        "chat_tools",
        route_after_tools,
        {
            "BUMP": "finalize_metadata",
            "CHAT": "chat_model",
        },
    )
    workflow.add_edge("chat_model", END)
    return workflow


chat_builder = create_chat_builder()
