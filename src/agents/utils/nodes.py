import json
import uuid
from typing import Any, Dict, List

from langchain.messages import SystemMessage
from langchain_openai import AzureChatOpenAI

from src.core.config import settings
from src.agents.utils.prompts import PROMPTS
from src.agents.utils.services.document_service import fetch_document_content
from src.agents.utils.state import (
    AgentState,
    BeforeAgentGuardrail,
    DocumentContent,
    Overview,
    SearchQueries,
    State,
)

from src.agents.utils.llm_config import llm, guardrail_llm
from src.agents.utils.helpers import (
    build_retrieved_context,
    deduplicate_queries,
    resolve_user_prompt,
)
from src.agents.utils.services.concept_service import fetch_concept_map
from src.agents.utils.services.retrieval import retrieve_chunks

from src.api.db.models.session import async_session_maker

from langgraph.config import get_stream_writer
from langgraph.types import interrupt


class AgentNodes:
    def __init__(self, llm: AzureChatOpenAI, guardrail_llm: AzureChatOpenAI):
        self.base_llm = llm
        self.llm_overview = self.base_llm.with_structured_output(Overview)
        self.llm_queries = self.base_llm.with_structured_output(SearchQueries)
        self.guardrail_llm = guardrail_llm.with_structured_output(BeforeAgentGuardrail)

    # ── guardrail ────────────────────────────────────────────────

    async def guardrail_node(self, state: State) -> dict:
        """Entry guardrail node to validate intent and block invalid requests."""
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "guardrail",
                "status": "started",
                "label": "Checking your request\u2026",
            }
        )

        messages = state.get("messages") or []
        user_request = messages[-1] if messages else state.get("user_prompt", "")

        prompt = await PROMPTS["before_agent_guardrail"].ainvoke(
            {"user_request": user_request}
        )
        result = await self.guardrail_llm.ainvoke(prompt)

        writer(
            {
                "event": "node_update",
                "node": "guardrail",
                "status": "completed",
                "label": "Checking your request\u2026",
                "detail": "Looking good, let\u2019s go",
            }
        )
        return {"intent": result}

    # ── query generation ─────────────────────────────────────────

    async def query_generation_node(self, state: State) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "query_generation",
                "status": "started",
                "label": "Figuring out what to look for\u2026",
            }
        )

        user_prompt = resolve_user_prompt(state)
        doc_ids = state.get("doc_ids") or []

        if not user_prompt.strip() or not doc_ids:
            fallback_query = (
                user_prompt.strip() if user_prompt.strip() else "mcq generation topics"
            )
            return {"search_queries": [fallback_query][: settings.num_search_queries]}

        concept_map = await fetch_concept_map(doc_ids)
        concept_payload = json.dumps(concept_map, ensure_ascii=False)

        prompt = await PROMPTS["query_generation"].ainvoke(
            {
                "user_prompt": user_prompt,
                "concept_map": concept_payload,
                "num_queries": settings.num_search_queries,
            }
        )
        result = await self.llm_queries.ainvoke(prompt)

        unique_queries = deduplicate_queries(
            result.queries, max_count=settings.num_search_queries
        )
        if not unique_queries:
            unique_queries = [user_prompt.strip()][: settings.num_search_queries]

        writer(
            {
                "event": "node_update",
                "node": "query_generation",
                "status": "completed",
                "label": "Figuring out what to look for\u2026",
                "detail": f"Found {len(unique_queries)} angles to explore",
            }
        )
        return {"user_prompt": user_prompt, "search_queries": unique_queries}

    # ── retrieval ────────────────────────────────────────────────

    async def retrieval_node(self, state: State) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "retrieval",
                "status": "started",
                "label": "Searching your documents\u2026",
            }
        )

        if not settings.chat_graph_retrieval_enabled:
            return {"retrieved_chunks": []}

        doc_ids = [str(doc_id) for doc_id in (state.get("doc_ids") or [])]
        search_queries = state.get("search_queries") or []
        user_id = state.get("user_id")

        if not doc_ids or not search_queries or not user_id:
            return {"retrieved_chunks": []}

        deduped_results = await retrieve_chunks(
            doc_ids=doc_ids, search_queries=search_queries, user_id=user_id
        )

        writer(
            {
                "event": "node_update",
                "node": "retrieval",
                "status": "completed",
                "label": "Searching your documents\u2026",
                "detail": f"Pulled {len(deduped_results)} relevant passages",
            }
        )
        return {"retrieved_chunks": deduped_results}

    # ── MCQ generation ───────────────────────────────────────────

    async def naive_mcq_generator_node(self, state: State) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "mcq_generation",
                "status": "started",
                "label": "Drafting questions from what I found\u2026",
            }
        )

        retrieved_chunks = state.get("retrieved_chunks") or []
        user_prompt = resolve_user_prompt(state)
        retrieved_context = build_retrieved_context(retrieved_chunks)

        prompt = await PROMPTS["naive_mcq_generation"].ainvoke(
            {
                "user_prompt": user_prompt,
                "retrieved_context": retrieved_context,
            }
        )
        response = await self.base_llm.ainvoke(prompt)

        writer(
            {
                "event": "node_update",
                "node": "mcq_generation",
                "status": "completed",
                "label": "Drafting questions from what I found\u2026",
                "detail": "Questions ready",
            }
        )
        return {"messages": [response]}

    # ── chat ─────────────────────────────────────────────────────

    async def chat_model(self, state: State) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "chat_generation",
                "status": "started",
                "label": "Thinking about your question\u2026",
            }
        )

        messages = list(state.get("messages") or [])
        retrieved_chunks = state.get("retrieved_chunks") or []

        if retrieved_chunks:
            context_text = build_retrieved_context(retrieved_chunks)
            system_message = SystemMessage(
                content=(
                    "Answer the user request using only the retrieved document chunks below. "
                    "If the chunks do not contain enough information, clearly say so.\n\n"
                    f"{context_text}"
                )
            )
            messages = [system_message, *messages]

        response = await self.base_llm.ainvoke(messages)

        writer(
            {
                "event": "node_update",
                "node": "chat_generation",
                "status": "completed",
                "label": "Thinking about your question\u2026",
                "detail": "Done thinking",
            }
        )
        return {"messages": [response]}

    # ── document / summary flow ──────────────────────────────────

    async def fetch_documents(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "fetch_documents",
                "status": "started",
                "label": "Reading your documents\u2026",
            }
        )

        async with async_session_maker() as db:
            documents = await fetch_document_content(state["doc_ids"], db=db)

        writer(
            {
                "event": "node_update",
                "node": "fetch_documents",
                "status": "completed",
                "label": "Reading your documents\u2026",
                "detail": f"Read {len(documents)} document(s)",
            }
        )
        return {"documents": documents}

    async def generate_summaries(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "generate_summaries",
                "status": "started",
                "label": "Picking out the key concepts\u2026",
            }
        )

        overview_list = []
        for doc in state.get("documents", []):
            prompt = await PROMPTS["summarize"].ainvoke({"document": doc})
            summary_obj = await self.llm_overview.ainvoke(prompt)
            overview_list.append(summary_obj)

        writer(
            {
                "event": "node_update",
                "node": "generate_summaries",
                "status": "completed",
                "label": "Picking out the key concepts\u2026",
                "detail": "Found concepts across your docs",
                "overview": [o.model_dump() for o in overview_list],
            }
        )
        return {"overview": overview_list}

    async def select_concepts(self, state: AgentState) -> dict:
        """Pause for user to select concepts."""
        overview = state.get("overview", [])
        selected = interrupt({"overview_for_user": overview})
        return {"selected_concepts": selected}

    # ── search-query generation (concept-based) ──────────────────

    async def _generate_queries_for_concepts(
        self, selected_concepts: list, prompt_key: str
    ) -> List[str]:
        """Shared logic for generate_search_queries / v2."""
        queries: List[str] = []
        for concept in selected_concepts:
            name = getattr(concept, "name", None) or concept.get("name", "")
            summary = getattr(concept, "summary", None) or concept.get("summary", "")
            prompt = await PROMPTS[prompt_key].ainvoke(
                {"concept_name": name, "concept_summary": summary}
            )
            result = await self.llm_queries.ainvoke(prompt)
            queries.extend(q.strip() for q in result.queries if q.strip())
        return list(dict.fromkeys(queries))

    async def generate_search_queriesv2(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "search_queries_v2",
                "status": "started",
                "label": "Building search queries for your topics\u2026",
            }
        )

        selected_concepts = state.get("selected_concepts") or []
        if not selected_concepts:
            return {"search_queries": []}

        queries = await self._generate_queries_for_concepts(
            selected_concepts, "search_queries_v2"
        )
        writer(
            {
                "event": "node_update",
                "node": "search_queries_v2",
                "status": "completed",
                "label": "Building search queries for your topics\u2026",
                "detail": f"Created {len(queries)} search queries",
            }
        )
        return {"search_queries": queries}

    async def generate_search_queries(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer(
            {
                "event": "node_update",
                "node": "search_queries",
                "status": "started",
                "label": "Building search queries for your topics\u2026",
            }
        )

        selected_concepts = state.get("selected_concepts") or []
        if not selected_concepts:
            return {"search_queries": []}

        queries = await self._generate_queries_for_concepts(
            selected_concepts, "search_queries"
        )
        writer(
            {
                "event": "node_update",
                "node": "search_queries",
                "status": "completed",
                "label": "Building search queries for your topics\u2026",
                "detail": f"Created {len(queries)} search queries",
            }
        )
        return {"search_queries": queries}

    # ── backward-compat alias ────────────────────────────────────

    async def retriever_node(self, state: AgentState) -> dict:
        result = await self.retrieval_node(state)
        return {"retrieved_context": result.get("retrieved_chunks", [])}


if __name__ == "__main__":
    print("AgentNodes module loaded")
