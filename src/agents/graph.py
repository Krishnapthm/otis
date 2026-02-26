"""
DEPRECATED — Agent Graph (RAG / Concept Extraction flow)
=========================================================

This module implements the original agentic RAG pipeline:

    START → fetch_documents → generate_summaries → human_approval
          → generate_search_queries → retrieve_context → END

**Status: DEPRECATED.**  Concept extraction has been moved to upload time
(see ``src/services/concept_service.py``), and document retrieval is now
handled by the two-layer retrieval service wired into the chat invoke
endpoint (see ``src/services/retrieval_service.py``).

This file is kept for reference and will be removed in a future cleanup.
Use ``src/agents/chat_agent.py`` instead.
"""

from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END

from src.agents.utils.nodes import AgentNodes
from src.agents.utils.state import AgentState


def create_agent_builder() -> StateGraph:
    """Returns the uncompiled graph builder.

    .. deprecated::
        This graph is superseded by the chat agent
        (``src/agents/chat_agent.py``) combined with the two-layer
        retrieval service (``src/services/retrieval_service.py``).
    """

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
