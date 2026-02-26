from typing import List
import uuid
import json
import os
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from langchain_ollama import OllamaEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud import (
    create_chat,
    create_chat_message,
    delete_chat,
    delete_chat_message,
    get_chat,
    get_chat_message,
    list_chat_messages,
    list_chats,
    update_chat,
    update_chat_message,
)
from src.api.db.models.session import get_db
from src.api.db.schema import (
    AuthResponse,
    ChatCreate,
    ChatInvokeRequest,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageUpdate,
    ChatResponse,
    ChatUpdate,
)
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
            status="streaming",
        ),
        current_user,
    )

    config = {"configurable": {"thread_id": str(chat_id)}}
    input_state = {
        "chat_messages": [{"role": "user", "content": message_text}],
        "user_prompt": message_text,
        "doc_ids": payload.doc_ids or [],
        "user_id": str(current_user.user_id),
        "use_naive_generator": settings.use_naive_mcq_generator,
    }

    # --- Concept-aware retrieval (when documents are mentioned) ---
    # If the user attached doc_ids (via mention picker), run two-layer retrieval
    # and inject the retrieved context as a system message.
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
                input_state["chat_messages"].insert(
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

    async def stream():
        yield (
            "data: "
            + json.dumps(
                {
                    "event": "started",
                    "user_message": user_message.model_dump(mode="json"),
                    "assistant_message_id": str(assistant_message.message_id),
                }
            )
            + "\n\n"
        )

        try:
            result = await graph.ainvoke(input_state, config=config)
            full_text = _extract_text_from_chat_result(result)

            words = full_text.split(" ") if full_text else []
            for index, token in enumerate(words):
                chunk = token if index == len(words) - 1 else f"{token} "
                yield f"data: {json.dumps({'event': 'token', 'content': chunk})}\n\n"

            final_message = await update_chat_message(
                db,
                chat_id,
                assistant_message.message_id,
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
            await update_chat_message(
                db,
                chat_id,
                assistant_message.message_id,
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
