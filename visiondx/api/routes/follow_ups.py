"""
VisionDX — Weekly & Monthly Follow-Up Routes

POST /follow-ups/weekly   — Submit weekly health summary
GET  /follow-ups/weekly   — List my weekly follow-ups (optional from/to)
POST /follow-ups/monthly  — Submit monthly evaluation
GET  /follow-ups/monthly  — List my monthly follow-ups
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.database.connection import get_db
from visiondx.database.models import AppUser, MonthlyFollowUp, WeeklyFollowUp
from visiondx.database.schemas import (
    MonthlyFollowUpCreate,
    MonthlyFollowUpOut,
    WeeklyFollowUpCreate,
    WeeklyFollowUpOut,
)
from visiondx.api.routes.users import get_current_app_user

router = APIRouter(prefix="/follow-ups", tags=["Follow-Ups"])


@router.post("/weekly", response_model=WeeklyFollowUpOut, status_code=201)
async def create_weekly_follow_up(
    body: WeeklyFollowUpCreate,
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit weekly health summary (mood, symptoms, diet & lifestyle)."""
    follow_up = WeeklyFollowUp(
        app_user_id=current_user.id,
        week_start_date=body.week_start_date,
        mood_score=body.mood_score,
        mental_state=body.mental_state,
        pain_level=body.pain_level,
        pain_notes=body.pain_notes,
        symptoms=body.symptoms,
        diet_lifestyle=body.diet_lifestyle,
        weight_kg=body.weight_kg,
        notes=body.notes,
    )
    db.add(follow_up)
    await db.flush()
    return WeeklyFollowUpOut.model_validate(follow_up)


@router.get("/weekly", response_model=list[WeeklyFollowUpOut])
async def list_weekly_follow_ups(
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
):
    """List weekly follow-ups for the current user, optionally filtered by date range."""
    q = select(WeeklyFollowUp).where(
        WeeklyFollowUp.app_user_id == current_user.id
    ).order_by(WeeklyFollowUp.week_start_date.desc())
    if from_date:
        q = q.where(WeeklyFollowUp.week_start_date >= from_date)
    if to_date:
        q = q.where(WeeklyFollowUp.week_start_date <= to_date)
    result = await db.execute(q.limit(100))
    items = result.scalars().all()
    return [WeeklyFollowUpOut.model_validate(x) for x in items]


@router.post("/monthly", response_model=MonthlyFollowUpOut, status_code=201)
async def create_monthly_follow_up(
    body: MonthlyFollowUpCreate,
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit monthly comprehensive health evaluation."""
    follow_up = MonthlyFollowUp(
        app_user_id=current_user.id,
        month_start=body.month_start,
        summary=body.summary,
        health_trends=body.health_trends,
        recommendations=body.recommendations,
        medical_alerts=body.medical_alerts,
    )
    db.add(follow_up)
    await db.flush()
    return MonthlyFollowUpOut.model_validate(follow_up)


@router.get("/monthly", response_model=list[MonthlyFollowUpOut])
async def list_monthly_follow_ups(
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
):
    """List monthly follow-ups for the current user."""
    q = select(MonthlyFollowUp).where(
        MonthlyFollowUp.app_user_id == current_user.id
    ).order_by(MonthlyFollowUp.month_start.desc())
    if from_date:
        q = q.where(MonthlyFollowUp.month_start >= from_date)
    if to_date:
        q = q.where(MonthlyFollowUp.month_start <= to_date)
    result = await db.execute(q.limit(24))
    items = result.scalars().all()
    return [MonthlyFollowUpOut.model_validate(x) for x in items]
