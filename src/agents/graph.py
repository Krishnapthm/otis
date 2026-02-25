from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END

from src.agents.utils.nodes import AgentNodes
from src.agents.utils.state import AgentState


def create_agent_builder() -> StateGraph:
    """Returns the uncompiled graph builder"""

    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        api_version="2024-12-01-preview",
        temperature=0.2,
        top_p=0.9,
        max_completion_tokens=500,
        presence_penalty=0.0,
        frequency_penalty=0.2,
    )

    nodes = AgentNodes(llm=llm, guardrail_llm=llm)

    workflow = StateGraph(AgentState)

    workflow.add_node("fetch_documents", nodes.fetch_documents)
    workflow.add_node("generate_summaries", nodes.generate_summaries)
    workflow.add_node("human_approval", nodes.select_concepts)
    workflow.add_node("generate_search_queries", nodes.generate_search_queries)
    workflow.add_node("retrieve_context", nodes.retriever_node)

    workflow.add_edge(START, "fetch_documents")
    workflow.add_edge("fetch_documents", "generate_summaries")
    workflow.add_edge("generate_summaries", "human_approval")
    workflow.add_edge("human_approval", "generate_search_queries")
    workflow.add_edge("generate_search_queries", "retrieve_context")
    workflow.add_edge("retrieve_context", END)

    return workflow


graph_builder = create_agent_builder()
