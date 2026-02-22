from typing import List
import uuid

from fastapi import APIRouter, Depends, status
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
	ChatMessageCreate,
	ChatMessageResponse,
	ChatMessageUpdate,
	ChatResponse,
	ChatUpdate,
)
from src.core.security import get_current_user


router = APIRouter(prefix="/chats")

# TODO: Add endpoint to attach an existing chat to a project.
# Suggested shape: POST /projects/{project_id}/chats/{chat_id}/attach
#
# TODO: Add endpoint to create a chat from within a project context.
# Suggested shape: POST /projects/{project_id}/chats


@router.post("/", name="create chat", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_endpoint(
	payload: ChatCreate,
	db: AsyncSession = Depends(get_db),
	current_user: AuthResponse = Depends(get_current_user),
):
	return await create_chat(db, payload, current_user)


@router.get("/", name="list chats", response_model=List[ChatResponse], status_code=status.HTTP_200_OK)
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


@router.get("/{chat_id}", name="get chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def get_chat_endpoint(
	chat_id: uuid.UUID,
	db: AsyncSession = Depends(get_db),
	current_user: AuthResponse = Depends(get_current_user),
):
	return await get_chat(db, chat_id, current_user)


@router.patch("/{chat_id}", name="update chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def update_chat_endpoint(
	chat_id: uuid.UUID,
	payload: ChatUpdate,
	db: AsyncSession = Depends(get_db),
	current_user: AuthResponse = Depends(get_current_user),
):
	return await update_chat(db, chat_id, payload, current_user)


@router.delete("/{chat_id}", name="delete chat", response_model=dict, status_code=status.HTTP_200_OK)
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
