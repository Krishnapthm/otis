"""
Agent/Graph Router

Updated to use user's vectorstore instead of requiring collection_id in request.
"""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.types import Command

from src.api.crud.embeddings import get_or_create_vectorstore
from src.api.db.models import UserVectorstore
from src.api.db.models.session import get_db
from src.api.db.schema import (
    AuthResponse,
    ResumeRequest,
    StartGraphRequest,
)
from src.core.security import get_current_user


router = APIRouter(prefix="/graph")


def get_graph(request: Request):
    """Get the compiled graph from app state"""
    graph = getattr(request.app.state, "compiled_graph", None)
    if graph is None:
        raise RuntimeError("Graph not initialized. Lifespan failed or not attached.")
    return graph


@router.post("/start")
async def start_graph(
    req: StartGraphRequest,
    graph=Depends(get_graph),
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """
    Start the graph with the user's vectorstore.
    
    Collection is automatically derived from user's vectorstore.
    No need to pass collection_id in request.
    """
    # Get user's vectorstore
    vectorstore = await get_or_create_vectorstore(current_user.user_id, db)
    
    # Derive collection name from user_id
    collection_name = f"user_{current_user.user_id}"
    
    # Check if vectorstore is ready
    if vectorstore.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Vectorstore is not ready. Current status: {vectorstore.status}. Please sync embeddings first."
        )
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"doc_ids": req.doc_ids, "collection_name": collection_name}

    async def stream():
        async for mode, payload in graph.astream(
            input_state,
            config,
            stream_mode=["custom"],
        ):
            yield f"data: {json.dumps({'mode': mode, 'payload': payload})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Thread-ID": thread_id},
    )


@router.post("/resume/{thread_id}")
async def resume_graph(
    thread_id: str,
    req: ResumeRequest,
    graph=Depends(get_graph),
    current_user: AuthResponse = Depends(get_current_user),
):
    """Resume the graph with selected concepts."""
    config = {"configurable": {"thread_id": thread_id}}

    async def stream():
        async for mode, payload in graph.astream(
            Command(resume=req.selected_concepts),
            config,
            stream_mode=["custom"],
        ):
            yield f"data: {json.dumps({'mode': mode, 'payload': payload})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
