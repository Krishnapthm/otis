from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.crud.users import (
    create_user,
    delete_current_user,
    edit_current_user,
    login_user,
    logout_user,
    refresh_user_token,
)
from src.api.db.models.session import get_db
from src.api.db.schema import (
    AuthResponse,
    CreateUser,
    RefreshTokenRequest,
    Token,
    UserResponse,
    UserUpdateRequest,
)

from src.core.security import get_current_user


router = APIRouter(prefix="/auth")


@router.post("/register", name="register new user", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: CreateUser, db: AsyncSession = Depends(get_db)):

    return await create_user(user_data, db)


@router.post("/login", name="Log  In", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):

    return await login_user(form_data, db)


@router.get("/me", name="me", response_model=AuthResponse)
async def me(current_user: AuthResponse = Depends(get_current_user)):
    return current_user


@router.post("/logout", name="Log out")
async def logout(current_user: AuthResponse = Depends(get_current_user)):
    return await logout_user(current_user)


@router.post("/refresh", name="Refresh", response_model=Token)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await refresh_user_token(payload.refresh_token, db)


@router.delete("/delete", name="delete user")
async def delete_user(
    current_user: AuthResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await delete_current_user(current_user, db)


@router.put("/edit", name="edit user", response_model=UserResponse)
async def edit_user(
    payload: UserUpdateRequest,
    current_user: AuthResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await edit_current_user(payload, current_user, db)
