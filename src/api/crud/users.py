from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Users
from src.api.db.schema import (
    AuthResponse,
    Token,
    UserResponse,
    CreateUser,
    UserUpdateRequest,
)
from datetime import timedelta
from src.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    revoke_refresh_jti,
    store_refresh_jti,
    validate_refresh_jti,
    verify_password,
)


async def create_user(user_data: CreateUser, db: AsyncSession) -> UserResponse:

    result = await db.execute(select(Users).where(user_data.email == Users.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="email already exists")

    hashed_password = get_password_hash(user_data.password)
    db_user = Users(
        user_name=user_data.uname,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse(
        id=db_user.user_id,
        uname=db_user.user_name,
        email=db_user.email,
        created_at=db_user.created_at,
    )


async def login_user(form_data: OAuth2PasswordRequestForm, db: AsyncSession):
    user = (
        await db.execute(select(Users).where(Users.email == form_data.username))
    ).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    refresh_payload = decode_token(refresh_token, expected_type="refresh")
    refresh_jti = refresh_payload.get("jti")
    if not refresh_jti:
        raise HTTPException(status_code=500, detail="Failed to generate refresh token")

    store_refresh_jti(user.email, refresh_jti)

    return Token(
        access_token=access_token,
        token_type="Bearer",
        refresh_token=refresh_token,
    )


async def refresh_user_token(refresh_token: str, db: AsyncSession) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except Exception:
        raise credentials_exception

    email = payload.get("sub")
    jti = payload.get("jti")
    if not email or not jti:
        raise credentials_exception

    user = (
        await db.execute(select(Users).where(Users.email == email))
    ).scalar_one_or_none()
    if not user:
        raise credentials_exception

    if not validate_refresh_jti(email, jti):
        raise credentials_exception

    access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})
    new_refresh_payload = decode_token(new_refresh_token, expected_type="refresh")
    new_jti = new_refresh_payload.get("jti")
    if not new_jti:
        raise HTTPException(status_code=500, detail="Failed to rotate refresh token")

    store_refresh_jti(email, new_jti)

    return Token(
        access_token=access_token,
        token_type="Bearer",
        refresh_token=new_refresh_token,
    )


async def logout_user(current_user: AuthResponse) -> dict:
    revoke_refresh_jti(current_user.email)
    return {"message": "Logged out successfully"}


async def delete_current_user(current_user: AuthResponse, db: AsyncSession) -> dict:
    user = await db.get(Users, current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    revoke_refresh_jti(current_user.email)
    return {"message": "User account deleted successfully"}


async def edit_current_user(
    payload: UserUpdateRequest,
    current_user: AuthResponse,
    db: AsyncSession,
) -> UserResponse:
    user = await db.get(Users, current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email and payload.email != user.email:
        existing = (
            await db.execute(select(Users).where(Users.email == payload.email))
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = payload.email

    if payload.uname:
        user.user_name = payload.uname

    if payload.password:
        user.hashed_password = get_password_hash(payload.password)

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.user_id,
        uname=user.user_name,
        email=user.email,
        created_at=user.created_at,
    )
