"""
VisionDX — Doctor Dashboard & Report Lookup

GET /doctor/abnormal-reports   — List reports with abnormal data (prioritized)
GET /doctor/report/{report_id} — Full report view (patient + params + predictions + PDF)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.database.connection import get_db
from visiondx.database.schemas import AbnormalReportItem, FullReportResponse
from visiondx.services import report_service

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])


@router.get("/abnormal-reports", response_model=list[AbnormalReportItem])
async def list_abnormal_reports(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """
    List reports that have abnormal parameters (LOW/HIGH), sorted by severity (abnormal count).
    Helps doctors prioritize patients requiring attention.
    """
    rows = await report_service.list_reports_with_abnormal(db, limit=limit)
    return [
        AbnormalReportItem(
            report_id=r.report_id,
            abnormal_count=count,
            patient_name=r.patient.name if r.patient else None,
            app_user_id=r.app_user_id,
            report_date=r.report_date,
            lab_name=r.lab_name,
            created_at=r.created_at,
        )
        for r, count in rows
    ]


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
