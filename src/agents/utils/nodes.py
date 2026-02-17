import asyncio
from email.mime import base
import json
from typing import List
from langchain.tools import tool, ToolRuntime
from langchain.messages import SystemMessage, HumanMessage
from langchain_ollama import OllamaEmbeddings
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from langchain_postgres import PGVector
from openai import vector_stores
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.agents.utils.prompts import PROMPTS
from src.agents.utils.services.document_service import fetch_document_content
from src.agents.utils.state import AgentState, DocumentContent, Overview, SearchQueries

from src.api.db.models.session import async_session_maker

from langgraph.config import get_stream_writer
from langgraph.types import interrupt


embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")


load_dotenv()

llm = AzureChatOpenAI(azure_deployment="gpt-4o-mini", api_version="2024-12-01-preview")
# llm_overview = AzureChatOpenAI(
#     azure_deployment="gpt-4o-mini",
#     api_version="2024-12-01-preview",
#     temperature=0.2,
#     top_p=0.9,
#     max_tokens=400,
#     presence_penalty=0.0,
#     frequency_penalty=0.2,
# )

sys_msg = SystemMessage("you are a helpful ai assitant")
human_msg = HumanMessage("ping")

messages = [sys_msg, human_msg]

# async_engine = create_async_engine(
#     "postgresql+asyncpg://user:password@db:5432/otis",  # asyncpg driver!
#     echo=True,  # Optional: logging
# )


# import asyncio
# from typing import List

# from langchain_core.tools import tool
# from langgraph.types import interrupt
# from langgraph.runtime import ToolRuntime

# assuming Overview is a Pydantic model
# from your.schemas import Overview


class AgentNodes:
    def __init__(self, llm_overview: AzureChatOpenAI):
        self.base_llm = llm_overview
        self.llm_overview = self.base_llm.with_structured_output(Overview)
        self.llm_queries = self.base_llm.with_structured_output(SearchQueries)

    async def fetch_documents(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer({"status": "Fetching Documents"})

        async with async_session_maker() as db:
            documents = await fetch_document_content(state["doc_ids"], db=db)

        writer({"status": "Documents Fetched", "num_docs": len(documents)})
        return {"documents": documents}

    async def generate_summaries(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer({"status": "Extracting Content"})

        overview_list = []

        for doc in state.get("documents", []):
            prompt = await PROMPTS["summarize"].ainvoke({"document": doc})
            summary_obj = await self.llm_overview.ainvoke(prompt)
            overview_list.append(summary_obj)

        writer(
            {
                "status": "Concepts extracted",
                "overview": [o.model_dump() for o in overview_list],
            }
        )

        return {"overview": overview_list}

    async def select_concepts(self, state: AgentState) -> dict:
        """Pause for user to select concepts"""
        overview = state.get("overview", [])
        selected = interrupt({"overview_for_user": overview})
        return {"selected_concepts": selected}

    async def generate_search_queries(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer({"status": "Generating search queries for selected concepts"})

        selected_concepts = state.get("selected_concepts") or []
        if not selected_concepts:
            return {"search_queries": []}

        queries = []

        for concept in selected_concepts:
            name = getattr(concept, "name", None) or concept.get("name", "")
            summary = getattr(concept, "summary", None) or concept.get("summary", "")

            prompt = await PROMPTS["search_queries"].ainvoke(
                {
                    "concept_name": name,
                    "concept_summary": summary,
                }
            )

            result = await self.llm_queries.ainvoke(prompt)
            queries.extend([q.strip() for q in result.queries if q.strip()])

        queries = list(dict.fromkeys(queries))
        writer({"status": "Queries generated", "num_queries": len(queries)})
        return {"search_queries": queries}

    async def retriever_node(self, state: AgentState) -> dict:
        writer = get_stream_writer()
        writer({"status": "Running Dynamic Retrieval"})

        collection_name = state.get("collection_name")
        search_queries = state.get("search_queries", [])

        if not collection_name:
            return {"retrieved_context": [], "error": "Missing collection_name"}
        if not search_queries:
            return {"retrieved_context": [], "error": "Missing search_queries"}

        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection="postgresql+psycopg://user:password@db:5432/otis",
        )
        retriever = vector_store.as_retriever()

        docs = []
        loop = asyncio.get_running_loop()

        for query in search_queries:
            try:
                retrieved_docs = await loop.run_in_executor(
                    None, retriever.invoke, query
                )
                docs.extend(retrieved_docs)
            except Exception as e:
                print(f"Retrieval error for '{query}': {e}")

        writer({"status": "Retrieval Complete", "docs": len(docs)})
        return {"retrieved_context": docs}

    # @tool
    # async def dynamic_retriever(runtime: ToolRuntime) -> dict:
    #     """
    #     search the specified collection for relevant documents
    #     (Tool version: reads from runtime.state)
    #     """
    #     writer = get_stream_writer()
    #     writer({"status": "Preparing retriever"})

    #     collection_name = runtime.state.get("collection_name")
    #     if not collection_name:
    #         return {"retrieved_context": [], "error": "Missing collection_name"}

    #     vector_store = PGVector(
    #         embeddings=embeddings,
    #         collection_name=collection_name,
    #         connection="postgresql+psycopg://user:password@db:5432/otis",
    #     )
    #     retriever = vector_store.as_retriever()

    #     search_queries = runtime.state.get("search_queries", [])
    #     if not search_queries:
    #         return {"retrieved_context": [], "error": "No search_queries in state"}

    #     docs = []
    #     loop = asyncio.get_running_loop()

    #     for query in search_queries:
    #         try:
    #             retrieved_docs = await loop.run_in_executor(
    #                 None, retriever.invoke, query
    #             )
    #             docs.extend(retrieved_docs)
    #         except Exception as e:
    #             print(f"Retrieval error for '{query}': {e}")

    #     return {"retrieved_context": docs}


if __name__ == "__main__":

    print(AgentNodes.chat_agent(messages))
