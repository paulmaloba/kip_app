"""
KIP Auth Service
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger("kip")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "kip-zambia-super-secret-change-in-production-2025")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
REFRESH_TOKEN_EXPIRE_DAYS   = 30

# Fix: use bcrypt with explicit version to avoid the passlib/bcrypt warning
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def _truncate(password: str) -> str:
    """bcrypt has a 72-byte hard limit — truncate safely."""
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(plain: str) -> str:
    return pwd_context.hash(_truncate(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate(plain), hashed)


def create_access_token(user_id, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "email": email, "type": "access", "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def create_refresh_token(user_id) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "type": "refresh", "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("sub")


async def get_user_by_email(db: AsyncSession, email: str):
    from models.database import User
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id):
    from models.database import User
    result = await db.execute(select(User).where(User.id == str(user_id)))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
