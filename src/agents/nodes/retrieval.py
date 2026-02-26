from langgraph.config import get_stream_writer

from src.agents.utils.helpers import resolve_user_prompt
from src.agents.utils.state import RetrievalStatus, State
from src.agents.utils.services.retrieval import retrieve_chunks


async def retrieval_node(state: State) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "event": "node_update",
            "node": "retrieval",
            "status": "started",
            "label": "Searching your documents…",
        }
    )

    doc_ids = [str(doc_id) for doc_id in (state.get("doc_ids") or [])]
    plan = state.get("plan")
    search_queries = (plan.retrieval_queries if plan else []) or []
    user_id = state.get("user_id")

    if not search_queries:
        fallback_query = resolve_user_prompt(state).strip() or (
            plan.topic if plan and getattr(plan, "topic", "") else "mcq generation"
        )
        search_queries = [fallback_query]

    if not doc_ids:
        writer(
            {
                "event": "node_update",
                "node": "retrieval",
                "status": "completed",
                "label": "Searching your documents…",
                "detail": "No documents were attached for retrieval",
            }
        )
        return {
            "retrieved_chunks": [],
            "retrieval_status": RetrievalStatus(
                status="failed", error="No doc_ids provided for retrieval"
            ),
        }

    if not user_id:
        writer(
            {
                "event": "node_update",
                "node": "retrieval",
                "status": "completed",
                "label": "Searching your documents…",
                "detail": "Missing user context for retrieval",
            }
        )
        return {
            "retrieved_chunks": [],
            "retrieval_status": RetrievalStatus(
                status="failed", error="Missing user_id for retrieval"
            ),
        }

    try:
        chunks = await retrieve_chunks(
            doc_ids=doc_ids,
            search_queries=search_queries,
            user_id=user_id,
        )
    except Exception as exc:
        writer(
            {
                "event": "node_update",
                "node": "retrieval",
                "status": "completed",
                "label": "Searching your documents…",
                "detail": "Retrieval failed, continuing",
            }
        )
        return {
            "retrieved_chunks": [],
            "retrieval_status": RetrievalStatus(status="failed", error=str(exc)),
        }

    writer(
        {
            "event": "node_update",
            "node": "retrieval",
            "status": "completed",
            "label": "Searching your documents…",
            "detail": f"Pulled {len(chunks)} relevant passages",
        }
    )
    return {
        "retrieved_chunks": chunks,
        "retrieval_status": RetrievalStatus(status="done"),
    }
