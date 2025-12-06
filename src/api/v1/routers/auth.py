import json
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.crud.users import create_user, login_user
from src.api.db.models import Users
from src.api.db.models.session import get_db
from src.api.crud import create_mcq, get_all_mcqs, get_mcq
from src.api.db.schema import AuthResponse, CreateMCQ, CreateUser, ReadMCQ, Token
from typing import List
import uuid

from src.core.security import get_current_user


router = APIRouter(prefix="/auth")

@router.post("/register", name="register new user", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: CreateUser, db: AsyncSession = Depends(get_db)):

    return await create_user(user_data, db)
@router.post("/login", name="Log In", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    
    return await login_user(form_data, db)

@router.get("/me", name="me", response_model=AuthResponse)
async def me(current_user: AuthResponse = Depends(get_current_user)):
    return current_user
        
@router.post("/logout", name="Log out")
async def logout():
    return ""
@router.post("/refresh", name="Refresh")
async def refresh():
    return ""

@router.delete("/delete", name="delete user")
async def delete_user():
    return ""

@router.put("/edit", name="edit user")
async def edit_user():
    return ""