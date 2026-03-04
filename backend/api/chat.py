"""
KIP Chat API Router
Main conversation endpoint — handles web chat and streams responses.
"""

import json
import uuid
import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, AsyncGenerator

from models.database import get_db, Conversation, Message, MessageRole, BusinessProfile
from services.kip_brain import generate_response
from services.intent_classifier import classify_intent
from services.kip_persona import get_system_prompt

logger = logging.getLogger("kip.chat")
router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

# class ChatRequest(BaseModel):
#     message:         str
#     session_token:   str
#     user_id:         Optional[str] = None
#     business_id:     Optional[str] = None
class ChatRequest(BaseModel):
    message:       str = ""
    content:       str = ""          # ← frontend sends this
    session_token: str = ""
    # user_id:       Optional[str] = None
    user_id: Optional[str | int] = None
    business_id:   Optional[str] = None

    def get_message(self) -> str:
        return self.message or self.content

    def get_user_id(self) -> Optional[str]:
        return str(self.user_id) if self.user_id is not None else None


class StartBusinessJourneyRequest(BaseModel):
    conversation_id: str
    user_id:         str
    business_name:   str
    sector:          str
    location:        str
    start_capital:   Optional[float] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def get_or_create_conversation(
    db: AsyncSession,
    session_token: str,
    user_id: Optional[str],
    business_id: Optional[str],
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.session_token == session_token)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(
            id=str(uuid.uuid4()),
            session_token=session_token,
            user_id=user_id,
            business_id=business_id,
        )
        db.add(conv)
        await db.flush()
    return conv


async def get_conversation_history(
    db: AsyncSession, conversation_id: str
) -> list[dict]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role.value, "content": m.content} for m in messages]


async def get_business_profile(
    db: AsyncSession, business_id: Optional[str]
) -> Optional[dict]:
    if not business_id:
        return None
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    bp = result.scalar_one_or_none()
    if not bp:
        return None
    return {
        "name":           bp.name,
        "sector":         bp.sector,
        "location":       bp.location,
        "stage":          bp.stage.value if bp.stage else None,
        "monthly_revenue": float(bp.monthly_revenue) if bp.monthly_revenue else None,
        "employees":      bp.employees,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/message")
async def send_message(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint. Returns full structured response.
    """
    if not req.get_message().strip():
        raise HTTPException(400, "Message cannot be empty")
    if len(req.get_message()) > 4000:
        raise HTTPException(400, "Message too long (max 4000 chars)")

    # Get or create conversation
    conv = await get_or_create_conversation(
        db, req.session_token, req.get_user_id(), req.business_id
    )

    # Load history and business profile
    history        = await get_conversation_history(db, conv.id)
    business_prof  = await get_business_profile(db, req.business_id)

    # Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role=MessageRole.user,
        content=req.get_message(),
    )
    db.add(user_msg)

    # Generate KIP response
    try:
        result = await generate_response(
            user_message=req.get_message(),
            conversation_history=history,
            business_profile=business_prof,
        )
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        raise HTTPException(500, f"KIP response failed: {str(e)}")

    # Save assistant message
    from models.database import ResponseType
    try:
        rt = ResponseType(result["response_type"])
    except Exception:
        rt = ResponseType.general

    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role=MessageRole.assistant,
        content=result["content"],
        response_type=rt,
        structured_data=result.get("structured"),
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0),
    )
    db.add(assistant_msg)
    await db.flush()

    return {
        "message_id":    assistant_msg.id,
        "conversation_id": conv.id,
        "response_type": result["response_type"],
        "content":       result["content"],
        "structured":    result.get("structured"),
        "tokens_used":   result.get("tokens_used", 0),
        "latency_ms":    result.get("latency_ms", 0),
    }


@router.get("/history/{session_token}")
async def get_history(
    session_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Return conversation history for a session."""
    result = await db.execute(
        select(Conversation).where(Conversation.session_token == session_token)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return {"messages": [], "conversation_id": None}

    msgs = await get_conversation_history(db, conv.id)
    return {
        "messages": msgs,
        "conversation_id": conv.id,
        "business_id": conv.business_id,
    }


@router.post("/start-journey")
async def start_business_journey(
    req: StartBusinessJourneyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Convert a business idea response into an active business journey.
    Creates a BusinessProfile and links it to the conversation.
    """
    from models.database import BusinessStage

    # Create business profile
    bp = BusinessProfile(
        id=str(uuid.uuid4()),
        user_id=req.user_id,
        name=req.business_name,
        sector=req.sector,
        location=req.location,
        stage=BusinessStage.planning,
        start_capital=req.start_capital,
    )
    db.add(bp)

    # Link to conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == req.conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv:
        conv.business_id = bp.id

    await db.flush()

    return {
        "business_id":   bp.id,
        "business_name": bp.name,
        "message": f"KIP is now tracking your {bp.name} journey. Share updates anytime."
    }


@router.get("/classify")
async def classify_message(message: str):
    """Debug endpoint — see how KIP classifies a message."""
    intent = classify_intent(message)
    return {"message": message, "intent": intent.value}
