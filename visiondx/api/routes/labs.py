"""
VisionDX — Lab Collaboration Routes

App user:
  GET  /labs              — List partner labs
  GET  /labs/bookings     — My lab bookings
  POST /labs/bookings     — Create booking (home sample or lab visit)

Lab API (X-Lab-API-Key):
  POST /lab-api/reports   — Submit report PDF for a booking
  PUT  /lab-api/bookings/{id}/status — Update booking status
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from visiondx.database.connection import get_db
from visiondx.database.models import AppUser, Lab, LabBooking
from visiondx.database.schemas import LabBookingCreate, LabBookingOut, LabOut
from visiondx.api.routes.users import get_current_app_user
from visiondx.services import report_service
from visiondx.config import settings


# ─── User: list labs, my bookings, create booking ────────────────────────────

router = APIRouter(prefix="/labs", tags=["Labs (User)"])


def _hash_lab_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def get_lab_by_api_key(
    x_lab_api_key: str = Header(..., alias="X-Lab-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Lab:
    key_hash = _hash_lab_key(x_lab_api_key)
    result = await db.execute(
        select(Lab).where(Lab.api_key_hash == key_hash, Lab.is_active == True)
    )
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive lab API key",
        )
    return lab


@router.get("", response_model=list[LabOut])
async def list_labs(db: AsyncSession = Depends(get_db)):
    """List active partner labs (home sample / lab visit)."""
    result = await db.execute(
        select(Lab).where(Lab.is_active == True).order_by(Lab.name)
    )
    labs = result.scalars().all()
    return [LabOut.model_validate(lab) for lab in labs]


@router.get("/bookings", response_model=list[LabBookingOut])
async def list_my_bookings(
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's lab bookings."""
    result = await db.execute(
        select(LabBooking)
        .where(LabBooking.app_user_id == current_user.id)
        .order_by(LabBooking.created_at.desc())
    )
    bookings = result.scalars().all()
    return [LabBookingOut.model_validate(b) for b in bookings]


@router.post("/bookings", response_model=LabBookingOut, status_code=201)
async def create_booking(
    body: LabBookingCreate,
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """Book a lab test (home sample collection or lab visit)."""
    result = await db.execute(select(Lab).where(Lab.id == body.lab_id, Lab.is_active == True))
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    if body.collection_type == "home" and not lab.supports_home_collection:
        raise HTTPException(
            status_code=400,
            detail="This lab does not support home sample collection",
        )
    booking = LabBooking(
        app_user_id=current_user.id,
        lab_id=body.lab_id,
        collection_type=body.collection_type,
        test_type=body.test_type,
        scheduled_at=body.scheduled_at,
    )
    db.add(booking)
    await db.flush()
    return LabBookingOut.model_validate(booking)


# ─── Lab API (for labs to submit reports and update status) ────────────────────

lab_api_router = APIRouter(prefix="/lab-api", tags=["Lab API"])


class BookingStatusUpdate(BaseModel):
    status: str  # sample_collected | processing | report_ready | cancelled


@lab_api_router.put("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    body: BookingStatusUpdate,
    lab: Lab = Depends(get_lab_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Update booking status (sample_collected, processing, report_ready, cancelled)."""
    result = await db.execute(
        select(LabBooking).where(
            LabBooking.id == booking_id,
            LabBooking.lab_id == lab.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    allowed = {"scheduled", "sample_collected", "processing", "report_ready", "cancelled"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {allowed}")
    booking.status = body.status
    await db.flush()
    return {"message": "Status updated", "booking_id": booking_id, "status": body.status}


@lab_api_router.post("/reports", status_code=202)
async def lab_submit_report(
    file: UploadFile = File(..., description="Report PDF"),
    booking_id: str | None = Form(None, description="Optional: link report to this booking ID"),
    lab: Lab = Depends(get_lab_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Lab submits a report PDF. Optionally link to a booking_id.
    Runs full pipeline (OCR, parse, abnormal detection, prediction) and notifies user.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb} MB limit")
    pdf_path = await report_service.save_upload(content, file.filename or "report.pdf")
    try:
        report = await report_service.process_report(pdf_path, db, app_user_id=None)
    except Exception as e:
        logger.error(f"Lab report processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report processing failed: {str(e)}")
    if booking_id:
        result = await db.execute(
            select(LabBooking).where(
                LabBooking.id == booking_id,
                LabBooking.lab_id == lab.id,
            )
        )
        booking = result.scalar_one_or_none()
        if booking:
            booking.report_id = report.report_id
            booking.status = "report_ready"
            report.app_user_id = booking.app_user_id
            await db.flush()
    return {
        "message": "Report submitted successfully",
        "report_id": report.report_id,
        "booking_id": booking_id,
    }
