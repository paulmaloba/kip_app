"""
KIP WhatsApp Webhook Router
Handles incoming Twilio WhatsApp messages.
"""

import uuid
import logging
from fastapi import APIRouter, Request, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db, Conversation, Message, MessageRole, User, Channel
from services.kip_brain import generate_response
from services.whatsapp_service import (
    validate_twilio_request, format_for_whatsapp, send_whatsapp_message
)
from fastapi import Depends

logger = logging.getLogger("kip.whatsapp")
router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(None),
    Body: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio WhatsApp webhook.
    Receives messages, generates KIP response, sends back via Twilio.
    """
    if not From or not Body:
        raise HTTPException(400, "Missing From or Body")

    # Extract phone number
    phone = From.replace("whatsapp:", "").strip()
    message_text = Body.strip()

    logger.info(f"WhatsApp message from {phone}: {message_text[:50]}")

    # Get or create user
    result = await db.execute(
        select(User).where(User.phone == phone)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=str(uuid.uuid4()), phone=phone)
        db.add(user)
        await db.flush()

    # Get or create conversation (WhatsApp = one long session per user)
    session_token = f"wa_{phone}"
    result = await db.execute(
        select(Conversation).where(Conversation.session_token == session_token)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(
            id=str(uuid.uuid4()),
            session_token=session_token,
            user_id=user.id,
            channel=Channel.whatsapp,
        )
        db.add(conv)
        await db.flush()

    # Get conversation history (last 10 messages)
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history = [
        {"role": m.role.value, "content": m.content}
        for m in reversed(msg_result.scalars().all())
    ]

    # Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role=MessageRole.user,
        content=message_text,
    )
    db.add(user_msg)

    # Generate KIP response
    try:
        result = await generate_response(
            user_message=message_text,
            conversation_history=history,
        )
    except Exception as e:
        logger.error(f"KIP generation failed for WhatsApp: {e}")
        await send_whatsapp_message(
            phone,
            "KIP is temporarily unavailable. Please try again in a moment."
        )
        return {"status": "error"}

    # Format for WhatsApp
    wa_text = format_for_whatsapp(
        response_type=result["response_type"],
        content=result["content"],
        structured=result.get("structured"),
    )

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
    )
    db.add(assistant_msg)

    # Send reply
    await send_whatsapp_message(phone, wa_text)

    return {"status": "ok"}


@router.get("/test")
async def test_webhook():
    """Confirm webhook is reachable (for ngrok/Twilio setup verification)."""
    return {"status": "KIP WhatsApp webhook is live"}
