"""
KIP Business Journey API
Manages business profiles, logs, and KIP's ongoing business analysis.
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from models.database import (
    get_db, BusinessProfile, BusinessLog, BusinessStage, LogType
)
from services.kip_brain import generate_business_log_analysis

logger = logging.getLogger("kip.business")
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class UpdateBusinessRequest(BaseModel):
    stage:          Optional[str] = None
    monthly_revenue: Optional[float] = None
    monthly_costs:  Optional[float] = None
    employees:      Optional[int] = None


class AddLogRequest(BaseModel):
    user_id:     str
    log_type:    str = "general"
    title:       str
    description: Optional[str] = None
    amount_zmw:  Optional[float] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{business_id}")
async def get_business(
    business_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    bp = result.scalar_one_or_none()
    if not bp:
        raise HTTPException(404, "Business not found")

    return {
        "id":             bp.id,
        "name":           bp.name,
        "sector":         bp.sector,
        "sub_sector":     bp.sub_sector,
        "stage":          bp.stage.value if bp.stage else None,
        "location":       bp.location,
        "description":    bp.description,
        "start_capital":  float(bp.start_capital) if bp.start_capital else None,
        "monthly_revenue": float(bp.monthly_revenue) if bp.monthly_revenue else None,
        "monthly_costs":  float(bp.monthly_costs) if bp.monthly_costs else None,
        "employees":      bp.employees,
        "created_at":     bp.created_at.isoformat() if bp.created_at else None,
    }


@router.patch("/{business_id}")
async def update_business(
    business_id: str,
    req: UpdateBusinessRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    bp = result.scalar_one_or_none()
    if not bp:
        raise HTTPException(404, "Business not found")

    if req.stage:
        try:
            bp.stage = BusinessStage(req.stage)
        except ValueError:
            pass
    if req.monthly_revenue is not None:
        bp.monthly_revenue = req.monthly_revenue
    if req.monthly_costs is not None:
        bp.monthly_costs = req.monthly_costs
    if req.employees is not None:
        bp.employees = req.employees

    return {"updated": True, "business_id": business_id}


@router.post("/{business_id}/log")
async def add_business_log(
    business_id: str,
    req: AddLogRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    User submits a business log update.
    KIP analyses it and returns suggestions.
    """
    # Get business profile
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    bp = result.scalar_one_or_none()
    if not bp:
        raise HTTPException(404, "Business not found")

    # Get recent logs for context
    recent_result = await db.execute(
        select(BusinessLog)
        .where(BusinessLog.business_id == business_id)
        .order_by(BusinessLog.created_at.desc())
        .limit(5)
    )
    recent_logs = [
        {
            "log_type":    log.log_type.value,
            "title":       log.title,
            "description": log.description,
            "amount_zmw":  float(log.amount_zmw) if log.amount_zmw else None,
        }
        for log in recent_result.scalars().all()
    ]

    # KIP analyses the log
    bp_dict = {
        "name":            bp.name,
        "sector":          bp.sector,
        "location":        bp.location,
        "stage":           bp.stage.value if bp.stage else "unknown",
        "monthly_revenue": float(bp.monthly_revenue) if bp.monthly_revenue else None,
        "employees":       bp.employees,
    }

    try:
        analysis = await generate_business_log_analysis(
            log_title=req.title,
            log_description=req.description or "",
            log_type=req.log_type,
            amount_zmw=req.amount_zmw,
            business_profile=bp_dict,
            recent_logs=recent_logs,
        )
    except Exception as e:
        logger.warning(f"Log analysis failed: {e}")
        analysis = {
            "analysis": "KIP has noted this update.",
            "suggestions": [],
            "warning": None,
            "encouragement": "Keep logging — every entry makes KIP smarter about your business.",
        }

    # Save log
    try:
        log_type_enum = LogType(req.log_type)
    except ValueError:
        log_type_enum = LogType.general

    log = BusinessLog(
        id=str(uuid.uuid4()),
        business_id=business_id,
        user_id=req.user_id,
        log_type=log_type_enum,
        title=req.title,
        description=req.description,
        amount_zmw=req.amount_zmw,
        kip_analysis=analysis.get("analysis", ""),
        kip_suggestions=analysis.get("suggestions", []),
    )
    db.add(log)
    await db.flush()

    return {
        "log_id":       log.id,
        "analysis":     analysis,
        "log_saved":    True,
    }


@router.get("/{business_id}/logs")
async def get_business_logs(
    business_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BusinessLog)
        .where(BusinessLog.business_id == business_id)
        .order_by(BusinessLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return {
        "logs": [
            {
                "id":           log.id,
                "log_type":     log.log_type.value,
                "title":        log.title,
                "description":  log.description,
                "amount_zmw":   float(log.amount_zmw) if log.amount_zmw else None,
                "kip_analysis": log.kip_analysis,
                "kip_suggestions": log.kip_suggestions,
                "created_at":   log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }
