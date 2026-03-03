"""
KIP Auth Router
===============
POST /auth/register   — create account
POST /auth/login      — get access + refresh tokens
POST /auth/refresh    — swap refresh token for new access token
GET  /auth/me         — get current user profile
POST /auth/logout     — invalidate refresh token
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.database import get_db, User, RefreshToken
from services.auth_service import (
    hash_password, authenticate_user, get_user_by_email,
    get_user_by_id, create_access_token, create_refresh_token,
    get_user_id_from_token, decode_token,
)

logger = logging.getLogger("kip")
router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str
    location: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          dict


class UserResponse(BaseModel):
    id:       int
    name:     str
    email:    str
    location: str | None


# ── Dependency: current user from Bearer token ────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ── Optional auth (returns None if not authenticated) ─────────────────────────
async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        name=req.name,
        email=req.email,
        hashed_password=hash_password(req.password),
        location=req.location,
        created_at=datetime.now(timezone.utc),
        last_active=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id)

    # Persist refresh token
    rt = RefreshToken(user_id=user.id, token=refresh, created_at=datetime.now(timezone.utc))
    db.add(rt)
    await db.commit()

    logger.info(f"New user registered: {user.email}")
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={"id": user.id, "name": user.name, "email": user.email, "location": user.location},
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Update last active
    user.last_active = datetime.now(timezone.utc)
    await db.commit()

    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id)

    rt = RefreshToken(user_id=user.id, token=refresh, created_at=datetime.now(timezone.utc))
    db.add(rt)
    await db.commit()

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={"id": user.id, "name": user.name, "email": user.email, "location": user.location},
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check token exists in DB (not revoked)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == req.refresh_token)
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    user_id = int(payload["sub"])
    user    = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Rotate: delete old, issue new
    await db.delete(stored)
    new_access  = create_access_token(user.id, user.email)
    new_refresh = create_refresh_token(user.id)
    rt = RefreshToken(user_id=user.id, token=new_refresh, created_at=datetime.now(timezone.utc))
    db.add(rt)
    await db.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user={"id": user.id, "name": user.name, "email": user.email, "location": user.location},
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        location=current_user.location,
    )


@router.post("/logout", status_code=204)
async def logout(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(RefreshToken).where(RefreshToken.token == req.refresh_token))
    await db.commit()
