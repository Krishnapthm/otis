from collections import UserDict
from datetime import timedelta, datetime
import uuid
from grpc import StatusCode
from sqlalchemy import Select, select
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Users, Projects
from src.api.db.models.session import get_db
from src.api.db.schema import AuthResponse, TokenData

SECRET_KEY = "4f099fa3ac8f851af37409faa83b49e03bcb33dbf90917146b3c9e9e39d6b47f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")
# oauth2_scheme = HTTPBearer()

def verify_password(plain_passowrd: str, hashed_password: str)-> bool:
    return pwd_context.verify(plain_passowrd, hashed_password)

def get_password_hash(password: str)-> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):

    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Invalid Credentials",
        headers = {"WWW-Authenticate":"Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = (await db.execute(select(Users).where(Users.email==token_data.email))).scalar_one_or_none()

    if user is None:
        raise credentials_exception
    
    return AuthResponse(
        user_id=user.user_id,
        email=user.email,
        uname=user.user_name,
        role = user.role
    )

# async def get_current_active_user(current_user: Users = Depends(get_current_user)):
#     if not current_user.is_active:
#         raise HTTPException(status_code=400, detail="inactive user")
#     return current_user
async def verify_project_access(
    project_id: uuid.UUID,
    current_user: AuthResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Projects:  
    """Verifies user owns/has access to a project"""
    
    project = await db.get(Projects, project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if current_user.role != "admin" and project.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or acces denied"
        )
    
    return project
    