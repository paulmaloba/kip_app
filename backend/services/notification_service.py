"""
KIP Notifications Service
==========================
Manages in-app notifications for rate alerts and other KIP events.
Stores notifications in DB per user. Frontend polls /api/notifications.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("kip.notifications")

# ── In-memory notification store (upgrades to DB below) ──────────────────────
# Keyed by user_id → list of notifications
_notifications: dict[str, list] = {}

# Global notifications (shown to ALL users — e.g. major rate moves)
_global_notifications: list = []


def create_notification(
    title:    str,
    message:  str,
    notif_type: str = "info",   # info | warning | alert | success
    # user_id:  Optional[str] = None,
    user_id: Optional[str | int] = None,
    data:     Optional[dict] = None,
    action_label: Optional[str] = None,
    action_url:   Optional[str] = None,
) -> dict:
    """Create a notification. user_id=None means global (all users)."""
    notif = {
        "id":           str(uuid.uuid4()),
        "title":        title,
        "message":      message,
        "type":         notif_type,
        "data":         data or {},
        "action_label": action_label,
        "action_url":   action_url,
        "created_at":   datetime.now(timezone.utc).isoformat(),
        "read":         False,
    }

    if user_id:
        if user_id not in _notifications:
            _notifications[user_id] = []
        _notifications[user_id].insert(0, notif)
        # Keep max 50 per user
        _notifications[user_id] = _notifications[user_id][:50]
    else:
        _global_notifications.insert(0, notif)
        # Keep max 20 global
        if len(_global_notifications) > 20:
            _global_notifications.pop()

    return notif


def get_user_notifications(user_id: str) -> list:
    """Get all notifications for a user (personal + global)."""
    personal = _notifications.get(user_id, [])
    # Merge global into personal, sorted by created_at
    all_notifs = personal + _global_notifications
    all_notifs.sort(key=lambda x: x["created_at"], reverse=True)
    return all_notifs[:30]


def get_unread_count(user_id: str) -> int:
    personal = _notifications.get(user_id, [])
    personal_unread = sum(1 for n in personal if not n["read"])
    global_unread   = sum(1 for n in _global_notifications if not n["read"])
    return personal_unread + global_unread


def mark_read(user_id: str, notification_id: Optional[str] = None):
    """Mark one or all notifications as read."""
    # Mark personal
    for notif in _notifications.get(user_id, []):
        if notification_id is None or notif["id"] == notification_id:
            notif["read"] = True
    # Mark global (per session — simplified)
    for notif in _global_notifications:
        if notification_id is None or notif["id"] == notification_id:
            notif["read"] = True


def notify_rate_change(changes: list[dict]):
    """
    Called by exchange_service when significant rate changes are detected.
    Creates appropriate notifications.
    """
    for change in changes:
        severity = change.get("severity", "normal")
        currency = change.get("currency", "ZMW")
        pct      = abs(change.get("pct_change", 0))
        msg      = change.get("message", "")
        impact   = change.get("impact", "")

        if currency == "ZMW":
            if severity == "major":
                notif_type = "alert"
                title = f"⚡ Major Kwacha Move: {pct:.1f}%"
            else:
                notif_type = "warning" if change.get("pct_change", 0) > 0 else "info"
                title = f"💱 Kwacha Rate Update"

            create_notification(
                title=title,
                message=f"{msg}\n{impact}",
                notif_type=notif_type,
                user_id=None,  # Global — all users see this
                data=change,
                action_label="View Rates",
                action_url="/dashboard",
            )
            logger.info(f"Global rate notification created: {title}")
        else:
            # Non-ZMW pairs — quieter notification
            if severity == "major":
                create_notification(
                    title=f"💱 {change.get('label')} Major Move",
                    message=msg,
                    notif_type="info",
                    user_id=None,
                    data=change,
                )
