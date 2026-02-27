from datetime import timedelta, datetime, timezone
import uuid
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models import Users, Projects
from src.api.db.models.session import get_db
from src.api.db.schema import AuthResponse, TokenData
from src.core.config import settings

try:
    from redis import Redis
except Exception:  # pragma: no cover - optional fallback
    Redis = None

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

_refresh_token_store: dict[str, tuple[str, int]] = {}
_redis_client = None
if Redis is not None:
    try:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
    except Exception:
        _redis_client = None


def verify_password(plain_passowrd: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_passowrd, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(
    data: dict,
    token_type: str,
    expires_delta: timedelta,
    jti: Optional[str] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    token_id = jti or str(uuid.uuid4())
    to_encode.update({"exp": expire, "typ": token_type, "jti": token_id})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data=data,
        token_type="access",
        expires_delta=expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data=data,
        token_type="refresh",
        expires_delta=expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: Optional[str] = None) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    token_type = payload.get("typ")
    if expected_type and token_type and token_type != expected_type:
        raise JWTError("Invalid token type")
    return payload


def _refresh_store_key(subject: str) -> str:
    return f"auth:refresh:{subject}"


def store_refresh_jti(subject: str, jti: str) -> None:
    expires_at = int(
        (
            datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        ).timestamp()
    )
    key = _refresh_store_key(subject)

    if _redis_client:
        ttl_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        _redis_client.setex(key, ttl_seconds, jti)
        return

    _refresh_token_store[key] = (jti, expires_at)


def validate_refresh_jti(subject: str, jti: str) -> bool:
    key = _refresh_store_key(subject)

    if _redis_client:
        stored = _redis_client.get(key)
        return stored == jti

    value = _refresh_token_store.get(key)
    if not value:
        return False

    stored_jti, expires_at = value
    if int(datetime.now(timezone.utc).timestamp()) >= expires_at:
        _refresh_token_store.pop(key, None)
        return False

    return stored_jti == jti


def revoke_refresh_jti(subject: str) -> None:
    key = _refresh_store_key(subject)
    if _redis_client:
        _redis_client.delete(key)
        return
    _refresh_token_store.pop(key, None)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, expected_type="access")
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = (
        await db.execute(select(Users).where(Users.email == token_data.email))
    ).scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return AuthResponse(
        user_id=user.user_id, email=user.email, uname=user.user_name, role=user.role
    )


# async def get_current_active_user(current_user: Users = Depends(get_current_user)):
#     if not current_user.is_active:
#         raise HTTPException(status_code=400, detail="inactive user")
#     return current_user
async def verify_project_access(
    project_id: uuid.UUID,
    current_user: AuthResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Projects:
    """Verifies user owns/has access to a project"""

    project = await db.get(Projects, project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if current_user.role != "admin" and project.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or acces denied",
        )

    return project
