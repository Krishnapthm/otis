import asyncio

from src.agents.utils.state import State
from langgraph.graph import StateGraph, START, END
from src.agents.utils.nodes import AgentNodes
from src.agents.utils.llm_config import llm, guardrail_llm
from src.core.config import settings


def route_intent(state: State) -> str:
    if state["intent"].intent == "ALLOW":
        return "ALLOW"
    else:
        return "BLOCK"


def route_generator(state: State) -> str:
    use_naive = state.get("use_naive_generator")
    if use_naive is None:
        use_naive = settings.use_naive_mcq_generator
    return "NAIVE" if use_naive else "NAIVE"


def create_chat_builder() -> StateGraph:
    agent_nodes = AgentNodes(llm=llm, guardrail_llm=guardrail_llm)
    workflow = StateGraph(State)
    workflow.add_node("guardrail_node", agent_nodes.guardrail_node)
    workflow.add_node("query_generation_node", agent_nodes.query_generation_node)
    workflow.add_node("retrieval_node", agent_nodes.retrieval_node)
    workflow.add_node("naive_mcq_generator_node", agent_nodes.naive_mcq_generator_node)
    workflow.add_node("chat_model", agent_nodes.chat_model)
    workflow.add_edge(START, "guardrail_node")
    workflow.add_conditional_edges(
        "guardrail_node",
        route_intent,
        {
            "ALLOW": "query_generation_node",
            "BLOCK": END,
        },
    )
    workflow.add_edge("query_generation_node", "retrieval_node")
    workflow.add_conditional_edges(
        "retrieval_node",
        route_generator,
        {
            "DEFAULT": "chat_model",
            "NAIVE": "naive_mcq_generator_node",
        },
    )
    workflow.add_edge("chat_model", END)
    workflow.add_edge("naive_mcq_generator_node", END)
    return workflow


chat_builder = create_chat_builder()


async def main():
    graph = chat_builder.compile()
    input1 = {"chat_messages": [{"role": "user", "content": "Hello!"}]}
    result1 = await graph.ainvoke(input1)
    print(result1["chat_messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
