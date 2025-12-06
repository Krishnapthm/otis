import email
from os import uname
from typing import List
from xml.dom import UserDataHandler
from fastapi import HTTPException
from fastapi.datastructures import FormData
from fastapi.security import OAuth2PasswordRequestForm
from grpc import StatusCode
from openai import project
from regex import D
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Users
from src.api.db.models.session import get_db
from src.api.db.schema import Token, UserResponse, LoginUser, CreateUser
import uuid
from datetime import timezone, timedelta
from src.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password
from src.services.embedding_service import embed_docs
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, insert

IST = timezone(timedelta(hours=5, minutes=30))


async def create_user(user_data: CreateUser, db: AsyncSession)-> UserResponse:
    print("PASSWORD VALUE:", repr(user_data.password), "LENGTH:", len(user_data.password))

    result = await db.execute(select(Users).where(user_data.email==Users.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="email already exists")

    hashed_password = get_password_hash(user_data.password)
    db_user = Users(
        user_name=user_data.uname,
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse(
        id=db_user.user_id,
        uname=db_user.user_name,
        email=db_user.email,
        created_at=db_user.created_at
    )

async def login_user(form_data: OAuth2PasswordRequestForm, db: AsyncSession):
    user = (await db.execute(select(Users).where(Users.email==form_data.username))).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password", headers={"WWW-Authenticate":"Bearer"})
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": user.email}, expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token, token_type="Bearer"
    )
