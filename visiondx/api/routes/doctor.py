"""
VisionDX — Doctor Report Lookup Routes

GET /doctor/report/{report_id}   Full report view (patient + params + predictions + PDF)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.database.connection import get_db
from visiondx.database.schemas import FullReportResponse
from visiondx.services import report_service

router = APIRouter(prefix="/doctor", tags=["Doctor Lookup"])


@router.get("/report/{report_id}", response_model=FullReportResponse)
async def doctor_get_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor-facing full report view.

    Returns:
      - Patient demographics
      - All blood test parameters with status (NORMAL/LOW/HIGH)
      - AI disease predictions with confidence scores
      - Clinical summary text
      - Link to download original PDF
    """
    report = await report_service.get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' not found. Please verify the Report ID.",
        )
    base_url = str(request.base_url).rstrip("/")
    return await report_service.build_full_report(report, base_url=base_url)
