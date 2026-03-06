"""
VisionDX — Report API Routes

POST /upload-report                    Upload PDF and run full pipeline
POST /analyze                          Re-run analysis on existing report
GET  /report/{report_id}               Get parsed report JSON
GET  /report/{report_id}/analysis      Get abnormal parameters + summary
GET  /report/{report_id}/prediction    Get disease predictions
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.config import settings
from visiondx.core.highlight_engine import HighlightEngine
from visiondx.database.connection import get_db
from visiondx.database.schemas import (
    FullReportResponse,
    PredictionOut,
    PredictionResponse,
    ReportAnalysisResponse,
    ReportOut,
    UploadResponse,
)
from visiondx.services import report_service

router = APIRouter(tags=["Reports"])
_highlighter = HighlightEngine()


def _check_pdf(file: UploadFile) -> None:
    """Validate uploaded file is a PDF under size limit."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )


@router.post("/upload-report", response_model=UploadResponse, status_code=202)
async def upload_report(
    file: UploadFile = File(..., description="Blood test report PDF"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a blood test PDF and run the full AI analysis pipeline.

    - Extracts text via OCR
    - Parses medical parameters
    - Detects abnormal values (LOW / NORMAL / HIGH)
    - Predicts possible diseases using the ML model
    """
    _check_pdf(file)

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    # Save PDF to disk
    pdf_path = await report_service.save_upload(content, file.filename or "report.pdf")
    logger.info(f"PDF saved: {pdf_path}")

    # Run pipeline
    try:
        report = await report_service.process_report(pdf_path, db)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report processing failed: {str(e)}",
        )

    return UploadResponse(
        report_id=report.report_id,
        message="Report processed successfully",
        status=report.status,
    )


@router.post("/analyze", response_model=UploadResponse)
async def analyze(
    file: UploadFile = File(..., description="Blood test report PDF"),
    db: AsyncSession = Depends(get_db),
):
    """Run the full analysis pipeline — same as /upload-report (alias)."""
    return await upload_report(file, db)  # type: ignore


@router.get("/report/{report_id}", response_model=ReportOut)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the parsed report data for a given Report ID.
    Returns patient info, all extracted parameters with status.
    """
    report = await report_service.get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return ReportOut.model_validate(report)


@router.get("/report/{report_id}/analysis", response_model=ReportAnalysisResponse)
async def get_report_analysis(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get abnormal parameter analysis for a report.
    Returns all parameters with their status (NORMAL/LOW/HIGH) and a plain-English summary.
    """
    report = await report_service.get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return await report_service.build_report_analysis(report)


@router.get("/report/{report_id}/prediction", response_model=PredictionResponse)
async def get_report_prediction(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get AI disease predictions for a report.
    Returns top predictions with confidence scores.
    """
    report = await report_service.get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

    predictions = [
        PredictionOut.model_validate(pred) for pred in report.predictions  # type: ignore[attr-defined]
    ]
    return PredictionResponse(
        report_id=report.report_id,
        possible_conditions=predictions,
    )
