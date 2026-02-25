from typing import List, Optional
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import (
    ChatMessageDocuments,
    ChatMessages,
    Chats,
    Documents,
    Users,
)
from src.api.db.schema import (
    AuthResponse,
    ChatCreate,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageUpdate,
    ChatResponse,
    ChatUpdate,
)


async def _is_admin(db: AsyncSession, user_id: uuid.UUID) -> bool:
    role = (
        await db.execute(select(Users.role).where(Users.user_id == user_id))
    ).scalar_one_or_none()
    return role == "admin"


async def _get_chat_for_user(
    db: AsyncSession,
    chat_id: uuid.UUID,
    current_user: AuthResponse,
    include_deleted: bool = False,
) -> Chats:
    query = select(Chats).where(Chats.chat_id == chat_id)

    if not await _is_admin(db, current_user.user_id):
        query = query.where(Chats.user_id == current_user.user_id)

    if not include_deleted:
        query = query.where(Chats.status != "deleted")

    chat = (await db.execute(query)).scalar_one_or_none()
    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found or you do not have access",
        )
    return chat


async def _sync_chat_aggregates(db: AsyncSession, chat: Chats) -> None:
    token_totals = await db.execute(
        select(
            func.coalesce(func.sum(ChatMessages.input_tokens), 0),
            func.coalesce(func.sum(ChatMessages.output_tokens), 0),
            func.max(ChatMessages.created_at),
        ).where(ChatMessages.chat_id == chat.chat_id)
    )
    total_input, total_output, last_message_at = token_totals.one()

    chat.total_input_tokens = int(total_input or 0)
    chat.total_output_tokens = int(total_output or 0)
    chat.last_message_at = last_message_at
    chat.updated_at = datetime.now(timezone.utc)


def _chat_to_response(chat: Chats) -> ChatResponse:
    return ChatResponse(
        chat_id=chat.chat_id,
        user_id=chat.user_id,
        status=chat.status,
        total_input_tokens=chat.total_input_tokens,
        total_output_tokens=chat.total_output_tokens,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        last_message_at=chat.last_message_at,
        deleted_at=chat.deleted_at,
    )


def _message_to_response(message: ChatMessages) -> ChatMessageResponse:
    return ChatMessageResponse(
        message_id=message.message_id,
        chat_id=message.chat_id,
        role=message.role,
        sequence=message.sequence,
        status=message.status,
        content=message.content,
        structured_data=message.structured_data,
        doc_ids=[],
        input_tokens=message.input_tokens,
        output_tokens=message.output_tokens,
        error=message.error,
        created_at=message.created_at,
    )


def _dedupe_doc_ids(doc_ids: Optional[List[uuid.UUID]]) -> List[uuid.UUID]:
    if not doc_ids:
        return []

    seen: set[uuid.UUID] = set()
    unique_doc_ids: List[uuid.UUID] = []
    for doc_id in doc_ids:
        if doc_id not in seen:
            seen.add(doc_id)
            unique_doc_ids.append(doc_id)
    return unique_doc_ids


async def _validate_doc_ids_for_user(
    db: AsyncSession,
    current_user: AuthResponse,
    doc_ids: List[uuid.UUID],
) -> List[uuid.UUID]:
    if not doc_ids:
        return []

    result = await db.execute(
        select(Documents.doc_id).where(
            and_(
                Documents.doc_id.in_(doc_ids),
                Documents.user_id == current_user.user_id,
            )
        )
    )
    existing_doc_ids = {row[0] for row in result.all()}
    missing = [doc_id for doc_id in doc_ids if doc_id not in existing_doc_ids]
    if missing:
        raise HTTPException(
            status_code=404,
            detail="One or more documents not found or you do not have access",
        )

    return doc_ids


async def _replace_message_documents(
    db: AsyncSession,
    message_id: uuid.UUID,
    doc_ids: List[uuid.UUID],
) -> None:
    await db.execute(
        delete(ChatMessageDocuments).where(
            ChatMessageDocuments.message_id == message_id
        )
    )

    for doc_id in doc_ids:
        db.add(ChatMessageDocuments(message_id=message_id, doc_id=doc_id))


async def _get_message_doc_ids(
    db: AsyncSession,
    message_ids: List[uuid.UUID],
) -> dict[uuid.UUID, List[uuid.UUID]]:
    if not message_ids:
        return {}

    result = await db.execute(
        select(ChatMessageDocuments.message_id, ChatMessageDocuments.doc_id)
        .where(ChatMessageDocuments.message_id.in_(message_ids))
        .order_by(ChatMessageDocuments.created_at.asc())
    )

    message_doc_ids: dict[uuid.UUID, List[uuid.UUID]] = {
        message_id: [] for message_id in message_ids
    }
    for message_id, doc_id in result.all():
        if message_id is not None and doc_id is not None:
            message_doc_ids.setdefault(message_id, []).append(doc_id)

    return message_doc_ids


async def create_chat(
    db: AsyncSession, payload: ChatCreate, current_user: AuthResponse
) -> ChatResponse:
    chat = Chats(
        user_id=current_user.user_id,
        title=payload.title,
        status="active",
        total_input_tokens=0,
        total_output_tokens=0,
    )

    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    return _chat_to_response(chat)


async def list_chats(
    db: AsyncSession,
    current_user: AuthResponse,
    limit: int = 50,
    skip: int = 0,
    status: Optional[str] = None,
) -> List[ChatResponse]:
    query = select(Chats)

    if not await _is_admin(db, current_user.user_id):
        query = query.where(Chats.user_id == current_user.user_id)

    if status:
        query = query.where(Chats.status == status)
    else:
        query = query.where(Chats.status != "deleted")

    result = await db.execute(
        query.order_by(Chats.updated_at.desc().nullslast()).offset(skip).limit(limit)
    )
    chats = result.scalars().all()

    return [_chat_to_response(chat) for chat in chats]


async def get_chat(
    db: AsyncSession, chat_id: uuid.UUID, current_user: AuthResponse
) -> ChatResponse:
    chat = await _get_chat_for_user(db, chat_id, current_user)
    return _chat_to_response(chat)


async def update_chat(
    db: AsyncSession,
    chat_id: uuid.UUID,
    payload: ChatUpdate,
    current_user: AuthResponse,
) -> ChatResponse:
    chat = await _get_chat_for_user(db, chat_id, current_user, include_deleted=True)

    if payload.title is None and payload.status is None:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    if payload.title is not None:
        chat.title = payload.title

    if payload.status is not None:
        chat.status = payload.status
        chat.deleted_at = (
            datetime.now(timezone.utc) if payload.status == "deleted" else None
        )

    chat.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(chat)

    return _chat_to_response(chat)


async def delete_chat(
    db: AsyncSession, chat_id: uuid.UUID, current_user: AuthResponse
) -> dict:
    chat = await _get_chat_for_user(db, chat_id, current_user, include_deleted=True)

    if chat.status == "deleted":
        return {"message": "Chat already deleted"}

    chat.status = "deleted"
    chat.deleted_at = datetime.now(timezone.utc)
    chat.updated_at = datetime.now(timezone.utc)

    await db.commit()

    return {"message": "Chat deleted successfully"}


async def create_chat_message(
    db: AsyncSession,
    chat_id: uuid.UUID,
    payload: ChatMessageCreate,
    current_user: AuthResponse,
) -> ChatMessageResponse:
    chat = await _get_chat_for_user(db, chat_id, current_user)

    if chat.status == "deleted":
        raise HTTPException(
            status_code=400, detail="Cannot add messages to a deleted chat"
        )

    max_sequence = (
        await db.execute(
            select(func.coalesce(func.max(ChatMessages.sequence), 0)).where(
                ChatMessages.chat_id == chat_id
            )
        )
    ).scalar_one()

    message = ChatMessages(
        chat_id=chat_id,
        role=payload.role,
        sequence=int(max_sequence) + 1,
        status=payload.status,
        content=payload.content,
        structured_data=payload.structured_data,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        error=payload.error,
    )

    db.add(message)
    await db.flush()

    doc_ids = _dedupe_doc_ids(payload.doc_ids)
    validated_doc_ids = await _validate_doc_ids_for_user(db, current_user, doc_ids)
    await _replace_message_documents(db, message.message_id, validated_doc_ids)

    await _sync_chat_aggregates(db, chat)

    await db.commit()
    await db.refresh(message)

    return ChatMessageResponse(
        message_id=message.message_id,
        chat_id=message.chat_id,
        role=message.role,
        sequence=message.sequence,
        status=message.status,
        content=message.content,
        structured_data=message.structured_data,
        doc_ids=validated_doc_ids,
        input_tokens=message.input_tokens,
        output_tokens=message.output_tokens,
        error=message.error,
        created_at=message.created_at,
    )


async def list_chat_messages(
    db: AsyncSession,
    chat_id: uuid.UUID,
    current_user: AuthResponse,
    limit: int = 200,
    skip: int = 0,
) -> List[ChatMessageResponse]:
    await _get_chat_for_user(db, chat_id, current_user)

    result = await db.execute(
        select(ChatMessages)
        .where(ChatMessages.chat_id == chat_id)
        .order_by(ChatMessages.sequence.asc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    message_ids = [message.message_id for message in messages]
    message_doc_ids = await _get_message_doc_ids(db, message_ids)

    return [
        ChatMessageResponse(
            message_id=message.message_id,
            chat_id=message.chat_id,
            role=message.role,
            sequence=message.sequence,
            status=message.status,
            content=message.content,
            structured_data=message.structured_data,
            doc_ids=message_doc_ids.get(message.message_id, []),
            input_tokens=message.input_tokens,
            output_tokens=message.output_tokens,
            error=message.error,
            created_at=message.created_at,
        )
        for message in messages
    ]


async def get_chat_message(
    db: AsyncSession,
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: AuthResponse,
) -> ChatMessageResponse:
    await _get_chat_for_user(db, chat_id, current_user)

    message = (
        await db.execute(
            select(ChatMessages).where(
                and_(
                    ChatMessages.chat_id == chat_id,
                    ChatMessages.message_id == message_id,
                )
            )
        )
    ).scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message_doc_ids = await _get_message_doc_ids(db, [message.message_id])

    return ChatMessageResponse(
        message_id=message.message_id,
        chat_id=message.chat_id,
        role=message.role,
        sequence=message.sequence,
        status=message.status,
        content=message.content,
        structured_data=message.structured_data,
        doc_ids=message_doc_ids.get(message.message_id, []),
        input_tokens=message.input_tokens,
        output_tokens=message.output_tokens,
        error=message.error,
        created_at=message.created_at,
    )


async def update_chat_message(
    db: AsyncSession,
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: ChatMessageUpdate,
    current_user: AuthResponse,
) -> ChatMessageResponse:
    chat = await _get_chat_for_user(db, chat_id, current_user)

    message = (
        await db.execute(
            select(ChatMessages).where(
                and_(
                    ChatMessages.chat_id == chat_id,
                    ChatMessages.message_id == message_id,
                )
            )
        )
    ).scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if (
        payload.content is None
        and payload.structured_data is None
        and payload.doc_ids is None
        and payload.status is None
        and payload.input_tokens is None
        and payload.output_tokens is None
        and payload.error is None
    ):
        raise HTTPException(status_code=400, detail="No fields provided to update")

    if payload.content is not None:
        message.content = payload.content
    if payload.structured_data is not None:
        message.structured_data = payload.structured_data
    if payload.doc_ids is not None:
        doc_ids = _dedupe_doc_ids(payload.doc_ids)
        validated_doc_ids = await _validate_doc_ids_for_user(db, current_user, doc_ids)
        await _replace_message_documents(db, message.message_id, validated_doc_ids)
    if payload.status is not None:
        message.status = payload.status
    if payload.input_tokens is not None:
        message.input_tokens = payload.input_tokens
    if payload.output_tokens is not None:
        message.output_tokens = payload.output_tokens
    if payload.error is not None:
        message.error = payload.error

    await _sync_chat_aggregates(db, chat)

    await db.commit()
    await db.refresh(message)

    message_doc_ids = await _get_message_doc_ids(db, [message.message_id])

    return ChatMessageResponse(
        message_id=message.message_id,
        chat_id=message.chat_id,
        role=message.role,
        sequence=message.sequence,
        status=message.status,
        content=message.content,
        structured_data=message.structured_data,
        doc_ids=message_doc_ids.get(message.message_id, []),
        input_tokens=message.input_tokens,
        output_tokens=message.output_tokens,
        error=message.error,
        created_at=message.created_at,
    )


async def delete_chat_message(
    db: AsyncSession,
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: AuthResponse,
) -> dict:
    chat = await _get_chat_for_user(db, chat_id, current_user)

    message = (
        await db.execute(
            select(ChatMessages).where(
                and_(
                    ChatMessages.chat_id == chat_id,
                    ChatMessages.message_id == message_id,
                )
            )
        )
    ).scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    await db.delete(message)
    await db.flush()

    await _sync_chat_aggregates(db, chat)

    await db.commit()

    return {"message": "Message deleted successfully"}
