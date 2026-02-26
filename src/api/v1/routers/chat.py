from typing import List, Optional
import uuid
import json
import os
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from langchain_ollama import OllamaEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud import (
    create_chat,
    create_chat_message,
    create_message_event,
    delete_chat,
    delete_chat_message,
    get_chat,
    get_chat_message,
    list_chat_messages,
    list_chats,
    list_message_events,
    update_chat,
    update_chat_message,
)
from src.api.db.models.session import get_db
from src.api.db.schema import (
    AuthResponse,
    ChatCreate,
    ChatInvokeRequest,
    ChatMessageCreate,
    ChatMessageEventReplayResponse,
    ChatMessageResponse,
    ChatMessageUpdate,
    ChatResponse,
    ChatUpdate,
)
from src.api.constants import (
    EVENT_DONE,
    EVENT_ERROR,
    EVENT_REASONING_TOKEN,
    EVENT_STARTED,
    EVENT_THINKING,
    EVENT_TOKEN_CHUNK,
)
from src.api.utils import EventSequencer, TokenChunkBuffer
from src.core.security import get_current_user
from src.core.config import settings
from src.services.retrieval_service import (
    retrieve_with_concepts,
    format_retrieved_context,
)


router = APIRouter(prefix="/chats")


def get_chat_graph(request: Request):
    graph = getattr(request.app.state, "compiled_chat_graph", None)
    if graph is None:
        raise RuntimeError(
            "Chat graph not initialized. Lifespan failed or not attached."
        )
    return graph


def _extract_text_from_chat_result(result: dict) -> str:
    messages = result.get("chat_messages") or []
    if not messages:
        return ""

    last = messages[-1]
    content = getattr(last, "content", None)
    if content is None and isinstance(last, dict):
        content = last.get("content")

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)

    return str(content or "")


# TODO: Add endpoint to attach an existing chat to a project.
# Suggested shape: POST /projects/{project_id}/chats/{chat_id}/attach
#
# TODO: Add endpoint to create a chat from within a project context.
# Suggested shape: POST /projects/{project_id}/chats


@router.post(
    "/",
    name="create chat",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_endpoint(
    payload: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await create_chat(db, payload, current_user)


@router.get(
    "/",
    name="list chats",
    response_model=List[ChatResponse],
    status_code=status.HTTP_200_OK,
)
async def list_chats_endpoint(
    limit: int = 50,
    skip: int = 0,
    chat_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await list_chats(
        db,
        current_user,
        limit=limit,
        skip=skip,
        status=chat_status,
    )


@router.get(
    "/{chat_id}",
    name="get chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def get_chat_endpoint(
    chat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await get_chat(db, chat_id, current_user)


@router.patch(
    "/{chat_id}",
    name="update chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def update_chat_endpoint(
    chat_id: uuid.UUID,
    payload: ChatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await update_chat(db, chat_id, payload, current_user)


@router.delete(
    "/{chat_id}",
    name="delete chat",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def delete_chat_endpoint(
    chat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await delete_chat(db, chat_id, current_user)


@router.post(
    "/{chat_id}/messages",
    name="create chat message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_message_endpoint(
    chat_id: uuid.UUID,
    payload: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await create_chat_message(db, chat_id, payload, current_user)


@router.get(
    "/{chat_id}/messages",
    name="list chat messages",
    response_model=List[ChatMessageResponse],
    status_code=status.HTTP_200_OK,
)
async def list_chat_messages_endpoint(
    chat_id: uuid.UUID,
    limit: int = 200,
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await list_chat_messages(db, chat_id, current_user, limit=limit, skip=skip)


@router.get(
    "/{chat_id}/messages/{message_id}",
    name="get chat message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_chat_message_endpoint(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await get_chat_message(db, chat_id, message_id, current_user)


@router.patch(
    "/{chat_id}/messages/{message_id}",
    name="update chat message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def update_chat_message_endpoint(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: ChatMessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await update_chat_message(db, chat_id, message_id, payload, current_user)


@router.delete(
    "/{chat_id}/messages/{message_id}",
    name="delete chat message",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def delete_chat_message_endpoint(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    return await delete_chat_message(db, chat_id, message_id, current_user)


@router.post(
    "/{chat_id}/invoke",
    name="invoke chat",
    status_code=status.HTTP_200_OK,
)
async def invoke_chat_endpoint(
    chat_id: uuid.UUID,
    payload: ChatInvokeRequest,
    request: Request,
    graph=Depends(get_chat_graph),
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    message_text = payload.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    await get_chat(db, chat_id, current_user)

    user_message = await create_chat_message(
        db,
        chat_id,
        ChatMessageCreate(
            role="user",
            content=message_text,
            doc_ids=payload.doc_ids,
            status="completed",
        ),
        current_user,
    )

    assistant_message = await create_chat_message(
        db,
        chat_id,
        ChatMessageCreate(
            role="assistant",
            content="",
            status="pending",
        ),
        current_user,
    )

    config = {"configurable": {"thread_id": str(chat_id)}}
    input_state = {
        "messages": [{"role": "user", "content": message_text}],
        "user_prompt": message_text,
        "doc_ids": payload.doc_ids or [],
        "user_id": str(current_user.user_id),
        "use_naive_generator": settings.use_naive_mcq_generator,
    }

    # --- Concept-aware retrieval (when documents are mentioned) ---
    # If the user attached doc_ids (via mention picker), run two-layer retrieval
    # and inject the retrieved context as a system message.
    did_pre_retrieval = False
    if payload.doc_ids and settings.chat_router_retrieval_fallback:
        try:
            _embeddings = OllamaEmbeddings(
                model="nomic-embed-text",
                base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
            )
            retrieved_docs = await retrieve_with_concepts(
                query=message_text,
                doc_ids=payload.doc_ids,
                user_id=str(current_user.user_id),
                db=db,
                embedding_model=_embeddings,
            )
            context_text = format_retrieved_context(retrieved_docs)
            if context_text:
                did_pre_retrieval = True
                input_state["messages"].insert(
                    0,
                    {
                        "role": "system",
                        "content": (
                            "Use the following document context to answer the "
                            "user's question. If the context doesn't contain "
                            "relevant information, say so.\n\n"
                            f"{context_text}"
                        ),
                    },
                )
        except Exception as retrieval_err:
            logging.getLogger(__name__).warning(
                "Retrieval failed for chat %s, proceeding without context: %s",
                chat_id,
                retrieval_err,
            )

    # ── Helper: persist an event (best-effort, never breaks stream) ──
    _log = logging.getLogger(__name__)
    _msg_id = assistant_message.message_id
    _pending_events: list = []  # accumulate before periodic flush

    async def _persist_event(
        seq: int,
        event_type: str,
        content: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Queue an event row. Flushed periodically or on completion."""
        try:
            await create_message_event(
                db,
                message_id=_msg_id,
                seq=seq,
                event_type=event_type,
                content=content,
                metadata=metadata,
            )
            _pending_events.append(seq)
            # Flush every 5 events to avoid huge unflushed batches
            if len(_pending_events) >= 5:
                await db.flush()
                _pending_events.clear()
        except Exception:
            _log.warning(
                "Failed to persist event seq=%d for message %s",
                seq,
                _msg_id,
                exc_info=True,
            )

    async def _flush_pending() -> None:
        """Flush any un-flushed event rows."""
        if _pending_events:
            try:
                await db.flush()
                _pending_events.clear()
            except Exception:
                _log.warning(
                    "Failed to flush pending events for message %s",
                    _msg_id,
                    exc_info=True,
                )

    async def stream():
        # Transition message: pending → streaming
        try:
            await update_chat_message(
                db,
                chat_id,
                _msg_id,
                ChatMessageUpdate(status="streaming"),
                current_user,
            )
        except Exception:
            _log.warning(
                "Failed to set message %s to streaming", _msg_id, exc_info=True
            )

        # Initialize event sequencer and token chunk buffer
        seq = EventSequencer(start=1)
        token_buffer = TokenChunkBuffer(seq_start=0)  # seq managed externally

        # ── SSE: started event ──
        started_seq = seq.next()
        await _persist_event(
            started_seq,
            EVENT_STARTED,
            metadata={
                "assistant_message_id": str(_msg_id),
            },
        )

        yield (
            "data: "
            + json.dumps(
                {
                    "event": "started",
                    "user_message": user_message.model_dump(mode="json"),
                    "assistant_message_id": str(_msg_id),
                }
            )
            + "\n\n"
        )

        # --- Synthetic thinking events for pre-graph retrieval ---
        if did_pre_retrieval:
            s1 = seq.next()
            await _persist_event(
                s1,
                EVENT_THINKING,
                content="Searching your documents…",
                metadata={
                    "node": "document_search",
                    "status": "started",
                },
            )
            yield f"data: {json.dumps({'event': 'thinking', 'node': 'document_search', 'status': 'started', 'label': 'Searching your documents…'})}\n\n"

            s2 = seq.next()
            await _persist_event(
                s2,
                EVENT_THINKING,
                content="Searching your documents…",
                metadata={
                    "node": "document_search",
                    "status": "completed",
                    "detail": "Found relevant context",
                },
            )
            yield f"data: {json.dumps({'event': 'thinking', 'node': 'document_search', 'status': 'completed', 'label': 'Searching your documents…', 'detail': 'Found relevant context'})}\n\n"

        try:
            full_text = ""
            reasoning_text = ""

            # Only stream tokens from terminal generation nodes
            _GENERATION_NODES = {"chat_model", "naive_mcq_generator_node"}

            # Helper to persist + flush a token chunk from the buffer
            async def _flush_token_chunk(chunk_content: str) -> None:
                s = seq.next()
                await _persist_event(s, EVENT_TOKEN_CHUNK, content=chunk_content)

            async for mode, chunk in graph.astream(
                input_state,
                config=config,
                stream_mode=["custom", "messages"],
            ):
                if mode == "custom":
                    # Forward writer() payloads as thinking events
                    node = chunk.get("node", "")
                    status_val = chunk.get("status", "")
                    label = chunk.get("label", "")
                    detail = chunk.get("detail")

                    s = seq.next()
                    await _persist_event(
                        s,
                        EVENT_THINKING,
                        content=label,
                        metadata={
                            "node": node,
                            "status": status_val,
                            "detail": detail,
                        },
                    )

                    yield f"data: {json.dumps({'event': 'thinking', 'node': node, 'status': status_val, 'label': label, 'detail': detail})}\n\n"

                elif mode == "messages":
                    # chunk is a tuple: (AIMessageChunk, metadata)
                    msg_chunk, metadata = chunk
                    node_name = metadata.get("langgraph_node", "")

                    # Skip tokens from non-generation nodes (guardrail,
                    # query_generation, retrieval produce structured output
                    # that should not be shown as chat text).
                    if node_name not in _GENERATION_NODES:
                        continue

                    # Check for reasoning/thinking content (OpenAI o-series)
                    reasoning_content = getattr(msg_chunk, "additional_kwargs", {}).get(
                        "reasoning_content"
                    )
                    if reasoning_content:
                        reasoning_text += reasoning_content
                        s = seq.next()
                        await _persist_event(
                            s,
                            EVENT_REASONING_TOKEN,
                            content=reasoning_content,
                            metadata={
                                "node": node_name,
                            },
                        )
                        yield f"data: {json.dumps({'event': 'reasoning_token', 'content': reasoning_content, 'node': node_name})}\n\n"

                    # Check for thinking content blocks (Anthropic-style)
                    thinking_blocks = [
                        block
                        for block in getattr(msg_chunk, "content", [])
                        if isinstance(block, dict) and block.get("type") == "thinking"
                    ]
                    for block in thinking_blocks:
                        thinking_text = block.get("thinking", "")
                        if thinking_text:
                            reasoning_text += thinking_text
                            s = seq.next()
                            await _persist_event(
                                s,
                                EVENT_REASONING_TOKEN,
                                content=thinking_text,
                                metadata={
                                    "node": node_name,
                                },
                            )
                            yield f"data: {json.dumps({'event': 'reasoning_token', 'content': thinking_text, 'node': node_name})}\n\n"

                    # Regular content tokens
                    content = ""
                    if isinstance(msg_chunk.content, str):
                        content = msg_chunk.content
                    elif isinstance(msg_chunk.content, list):
                        # Extract text blocks only (skip thinking blocks)
                        for block in msg_chunk.content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                content += block.get("text", "")
                            elif isinstance(block, str):
                                content += block

                    if content:
                        full_text += content

                        # Feed into chunk buffer for persistence
                        pending = token_buffer.add(content)
                        if pending:
                            await _flush_token_chunk(pending.content)

                        # SSE: always emit per-token for live responsiveness
                        yield f"data: {json.dumps({'event': 'token', 'content': content})}\n\n"

                # Periodically check time-based flush for token buffer
                stale = token_buffer.flush_if_stale()
                if stale:
                    await _flush_token_chunk(stale.content)

            # Flush any remaining buffered tokens
            final_chunk = token_buffer.flush_final()
            if final_chunk:
                await _flush_token_chunk(final_chunk.content)

            # Persist done event
            done_seq = seq.next()
            await _persist_event(
                done_seq,
                EVENT_DONE,
                metadata={
                    "content_length": len(full_text),
                },
            )
            await _flush_pending()

            final_message = await update_chat_message(
                db,
                chat_id,
                _msg_id,
                ChatMessageUpdate(
                    content=full_text,
                    status="completed",
                ),
                current_user,
            )

            yield (
                "data: "
                + json.dumps(
                    {
                        "event": "done",
                        "assistant_message": final_message.model_dump(mode="json"),
                    }
                )
                + "\n\n"
            )
        except Exception as exc:
            # Flush remaining token buffer on error
            try:
                err_chunk = token_buffer.flush_final()
                if err_chunk:
                    await _flush_token_chunk(err_chunk.content)
            except Exception:
                pass

            # Persist error event
            try:
                err_seq = seq.next()
                await _persist_event(
                    err_seq,
                    EVENT_ERROR,
                    content=str(exc),
                    metadata={
                        "error_type": type(exc).__name__,
                    },
                )
                await _flush_pending()
            except Exception:
                _log.warning(
                    "Failed to persist error event for message %s",
                    _msg_id,
                    exc_info=True,
                )

            await update_chat_message(
                db,
                chat_id,
                _msg_id,
                ChatMessageUpdate(
                    status="failed",
                    error={"message": str(exc)},
                ),
                current_user,
            )
            yield f"data: {json.dumps({'event': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Thread-ID": str(chat_id)},
    )


# ==========================================================================
# Event replay / resume
# ==========================================================================


def _event_to_sse_line(event: dict) -> str:
    """Convert a stored event dict into an SSE-compatible data payload.

    Maps persisted event_type + content/metadata back into the same SSE
    shape that the live invoke endpoint emits, so the client can use the
    same handler pipeline for both live and replayed events.
    """
    etype = event.get("event_type", "")
    content = event.get("content")
    meta = event.get("metadata") or {}

    if etype == EVENT_STARTED:
        return json.dumps(
            {
                "event": "started",
                "assistant_message_id": meta.get("assistant_message_id", ""),
                # user_message is not stored on the event — client already has it
            }
        )
    elif etype == EVENT_THINKING:
        return json.dumps(
            {
                "event": "thinking",
                "node": meta.get("node", ""),
                "status": meta.get("status", ""),
                "label": content or "",
                "detail": meta.get("detail"),
            }
        )
    elif etype == EVENT_TOKEN_CHUNK:
        return json.dumps({"event": "token", "content": content or ""})
    elif etype == EVENT_REASONING_TOKEN:
        return json.dumps(
            {
                "event": "reasoning_token",
                "content": content or "",
                "node": meta.get("node"),
            }
        )
    elif etype == EVENT_DONE:
        return json.dumps({"event": "done"})
    elif etype == EVENT_ERROR:
        return json.dumps({"event": "error", "detail": content or ""})
    else:
        # Unknown/future event types — pass through generically
        return json.dumps({"event": etype, "content": content, "metadata": meta})


@router.get(
    "/{chat_id}/messages/{message_id}/events",
    name="replay message events",
    status_code=status.HTTP_200_OK,
)
async def replay_message_events_endpoint(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    after_seq: int = Query(0, ge=0, description="Resume from this seq (exclusive)"),
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
):
    """Replay persisted events for an assistant message.

    - **Completed/failed messages**: Returns all events as a JSON response
      (``ChatMessageEventReplayResponse``).
    - **Streaming/pending messages**: Returns an SSE ``StreamingResponse``
      that first emits all stored events, then polls for new events every
      500 ms until the message reaches a terminal state.

    The client can pass ``after_seq`` (from a previous ``last_seq``) to
    resume without replaying already-received events.
    """
    # Fetch initial batch
    replay = await list_message_events(
        db, chat_id, message_id, current_user, after_seq=after_seq
    )

    # Completed message → return fast JSON response
    if replay.is_complete:
        return replay

    # In-progress message → SSE live tail
    async def _live_tail():
        # Emit stored events first
        for ev in replay.events:
            line = _event_to_sse_line(ev.model_dump(mode="json"))
            yield f"data: {line}\n\n"

        last_seen = replay.last_seq

        # Poll for new events until message completes
        while True:
            await asyncio.sleep(0.5)
            batch = await list_message_events(
                db, chat_id, message_id, current_user, after_seq=last_seen
            )
            for ev in batch.events:
                line = _event_to_sse_line(ev.model_dump(mode="json"))
                yield f"data: {line}\n\n"

            if batch.last_seq > last_seen:
                last_seen = batch.last_seq

            if batch.is_complete:
                break

    return StreamingResponse(
        _live_tail(),
        media_type="text/event-stream",
    )
