import asyncio

from src.agents.utils.state import State
from langgraph.graph import StateGraph, START, END
from src.agents.utils.nodes import AgentNodes, llm, guardrail_llm


def route_intent(state: State) -> str:
    if state["intent"].intent == "ALLOW":
        return "ALLOW"
    else:
        return "BLOCK"


def create_chat_builder() -> StateGraph:
    agent_nodes = AgentNodes(llm=llm, guardrail_llm=guardrail_llm)
    workflow = StateGraph(State)
    workflow.add_node("guardrail_node", agent_nodes.guardrail_node)
    workflow.add_node("chat_model", agent_nodes.chat_model)
    workflow.add_edge(START, "guardrail_node")
    workflow.add_conditional_edges(
        "guardrail_node",
        route_intent,
        {
            "ALLOW": "chat_model",
            "BLOCK": END,
        },
    )
    workflow.add_edge("chat_model", END)
    return workflow


chat_builder = create_chat_builder()


async def main():
    graph = chat_builder.compile()
    input1 = {"chat_messages": [{"role": "user", "content": "Hello!"}]}
    result1 = await graph.ainvoke(input1)
    print(result1["chat_messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
