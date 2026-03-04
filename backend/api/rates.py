"""
KIP Rates & Notifications API
"""

import logging
from fastapi import APIRouter, Query
from typing import Optional

from services.exchange_service import get_current_rates, get_rate_history, get_recent_alerts
from services.notification_service import (
    get_user_notifications, get_unread_count, mark_read, create_notification
)

logger = logging.getLogger("kip.rates_api")
router = APIRouter()


# ── Exchange Rates ─────────────────────────────────────────────────────────────

@router.get("/rates/current")
async def current_rates():
    """Live ZMW exchange rates."""
    data = await get_current_rates()
    return {
        "summary":      data["summary"],
        "source":       data["source"],
        "recent_alerts": get_recent_alerts()[:5],
    }


@router.get("/rates/history")
async def rate_history():
    """Last 24 hourly snapshots."""
    return {"history": get_rate_history()}


@router.get("/rates/alerts")
async def rate_alerts():
    """Recent rate change alerts."""
    return {"alerts": get_recent_alerts()}


# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications")
async def get_notifications(user_id: Optional[str] = Query(None)):
    """Get notifications for a user."""
    if not user_id:
        return {"notifications": [], "unread": 0}
    notifs  = get_user_notifications(user_id)
    unread  = get_unread_count(user_id)
    return {"notifications": notifs, "unread": unread}


@router.get("/notifications/unread")
async def unread_count(user_id: Optional[str] = Query(None)):
    """Quick unread count — called frequently by frontend bell."""
    if not user_id:
        return {"unread": 0}
    return {"unread": get_unread_count(user_id)}


@router.post("/notifications/read")
async def mark_notifications_read(
    user_id:         str,
    notification_id: Optional[str] = None,
):
    """Mark notification(s) as read."""
    mark_read(user_id, notification_id)
    return {"ok": True}
