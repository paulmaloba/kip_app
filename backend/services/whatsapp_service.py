"""
KIP WhatsApp Service
Twilio WhatsApp Business API integration.
Converts KIP's 5 response layouts to WhatsApp-formatted text.
"""

import json
import logging
import hmac
import hashlib
from typing import Optional
from twilio.rest import Client as TwilioClient
from twilio.request_validator import RequestValidator
from config import settings

logger = logging.getLogger("kip.whatsapp")

_twilio: Optional[TwilioClient] = None

def get_twilio() -> Optional[TwilioClient]:
    global _twilio
    if not settings.TWILIO_ACCOUNT_SID:
        return None
    if _twilio is None:
        _twilio = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
        )
    return _twilio


def validate_twilio_request(url: str, params: dict, signature: str) -> bool:
    """Validate incoming Twilio webhook signatures."""
    if not settings.TWILIO_AUTH_TOKEN:
        return True  # Skip in development
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    return validator.validate(url, params, signature)


def render_business_idea_wa(data: dict) -> str:
    """Convert business idea JSON to WhatsApp-formatted text."""
    lines = [
        f"💡 *BUSINESS OPPORTUNITY*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"*{data.get('title', 'Business Idea')}*",
        f"_{data.get('tagline', '')}_",
        f"",
        f"📍 Best for: {', '.join(data.get('best_for_location', []))}",
        f"💰 Startup: K{data.get('startup_capital_min', 0):,} – K{data.get('startup_capital_max', 0):,}",
        f"📈 Monthly revenue: K{data.get('monthly_revenue_min', 0):,} – K{data.get('monthly_revenue_max', 0):,}",
        f"⏱ Break-even: ~{data.get('breakeven_months', '?')} months",
        f"",
        f"*WHY THIS WORKS IN ZAMBIA*",
        f"{data.get('why_zambia', '')}",
        f"",
        f"*YOUR FIRST STEPS*",
    ]

    for step in data.get("first_steps", []):
        lines.append(f"{step['step']}. {step['action']} — {step.get('cost','')} ({step.get('timeframe','')})")

    lines += [
        f"",
        f"⚠️ *Main risk:* {data.get('main_risk', '')}",
        f"🏦 *Funding:* {', '.join(data.get('funding_options', []))}",
        f"",
        f"_{data.get('kip_verdict', '')}_",
        f"",
        f"Reply *LOG* to start tracking this business with KIP.",
    ]
    return "\n".join(lines)


def render_crisis_wa(data: dict) -> str:
    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(data.get("severity", "medium"), "🟡")
    lines = [
        f"{severity_emoji} *CRISIS RESPONSE*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"*SITUATION:* {data.get('situation_assessment', '')}",
        f"",
        f"*DO THIS NOW (48 hours):*",
    ]
    for i, item in enumerate(data.get("do_now", []), 1):
        lines.append(f"{i}. {item['action']}")
        if item.get("why"):
            lines.append(f"   _{item['why']}_")

    lines += ["", "*DO THIS WEEK:*"]
    for i, item in enumerate(data.get("do_this_week", []), 1):
        lines.append(f"{i}. {item['action']}")

    lines += [
        f"",
        f"❌ *Don't:* {data.get('avoid_this_mistake', '')}",
        f"",
        f"💬 {data.get('honest_outlook', '')}",
    ]
    return "\n".join(lines)


def render_regulatory_wa(data: dict) -> str:
    lines = [
        f"📋 *REGISTRATION GUIDE*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"*Business type:* {data.get('business_type', '')}",
        f"",
        f"*STEPS:*",
    ]
    for item in data.get("checklist", []):
        cost = f"K{item.get('cost_zmw', 0):,}" if item.get("cost_zmw") else "Free"
        lines.append(
            f"{item['step']}. *{item['institution']}* — {item['action']}\n"
            f"   Cost: {cost} | Time: {item.get('timeframe', '?')}"
        )
    lines += [
        f"",
        f"💰 *Total cost:* K{data.get('total_cost_min', 0):,}–K{data.get('total_cost_max', 0):,}",
        f"⏱ *Total time:* {data.get('total_time', '?')}",
        f"",
        f"💡 *Tip:* {data.get('pro_tip', '')}",
    ]
    return "\n".join(lines)


def render_economic_wa(data: dict) -> str:
    lines = [
        f"📊 *ECONOMIC INTELLIGENCE*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"*{data.get('headline', '')}*",
        f"",
        f"{data.get('summary', '')}",
        f"",
        f"*KEY DATA POINTS:*",
    ]
    for dp in data.get("data_points", []):
        arrow = "↑" if dp.get("trend") == "up" else "↓"
        lines.append(f"• {dp['label']}: {dp['value']} {arrow}")

    lines += [
        f"",
        f"*WHAT THIS MEANS FOR YOUR BUSINESS:*",
    ]
    for impl in data.get("business_implications", []):
        lines.append(f"• {impl}")

    lines += ["", f"📌 *Watch:* {data.get('forecast_note', '')}"]
    return "\n".join(lines)


def render_general_wa(content: str) -> str:
    """Clean up general text for WhatsApp."""
    # Convert markdown bold to WhatsApp bold
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', content)
    text = re.sub(r'#{1,3}\s+(.+)', r'*\1*', text)   # headers → bold
    return text


def format_for_whatsapp(response_type: str, content: str, structured: dict) -> str:
    """
    Master formatter — routes to the correct WhatsApp renderer.
    Falls back to general text if structured data is missing.
    """
    try:
        if response_type == "business_idea" and structured:
            return render_business_idea_wa(structured)
        elif response_type == "crisis" and structured:
            return render_crisis_wa(structured)
        elif response_type == "regulatory" and structured:
            return render_regulatory_wa(structured)
        elif response_type == "economic_analysis" and structured:
            return render_economic_wa(structured)
        else:
            return render_general_wa(content)
    except Exception as e:
        logger.warning(f"WhatsApp render failed: {e}")
        return content[:1500]   # WhatsApp 1600 char limit safety


async def send_whatsapp_message(to_number: str, message: str) -> bool:
    """Send a WhatsApp message via Twilio."""
    client = get_twilio()
    if not client:
        logger.warning("Twilio not configured — WhatsApp message not sent")
        return False
    try:
        # Chunk long messages (WhatsApp limit ~1600 chars)
        chunks = [message[i:i+1500] for i in range(0, len(message), 1500)]
        for chunk in chunks:
            client.messages.create(
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f"whatsapp:{to_number}",
                body=chunk,
            )
        return True
    except Exception as e:
        logger.error(f"Twilio send failed: {e}")
        return False
