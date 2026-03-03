"""KIP Users API"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from models.database import get_db, User, BusinessProfile

router = APIRouter()

class CreateUserRequest(BaseModel):
    name:     Optional[str] = None
    email:    Optional[str] = None
    phone:    Optional[str] = None
    location: Optional[str] = None

@router.post("/")
async def create_user(req: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    user = User(id=str(uuid.uuid4()), **req.dict(exclude_none=True))
    db.add(user)
    await db.flush()
    return {"user_id": user.id}

@router.get("/{user_id}/businesses")
async def get_user_businesses(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.user_id == user_id)
    )
    businesses = result.scalars().all()
    return {"businesses": [{"id": b.id, "name": b.name, "sector": b.sector, "stage": b.stage.value if b.stage else None} for b in businesses]}
