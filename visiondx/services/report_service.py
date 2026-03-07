"""
VisionDX — Report Service

Orchestrates the full pipeline:
  PDF → OCR → Parse → Abnormal Detection → Prediction → Persist → Return
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from visiondx.config import settings
from visiondx.core.abnormal_detector import AbnormalDetector
from visiondx.core.highlight_engine import HighlightEngine
from visiondx.core.ocr_engine import PDFExtractor
from visiondx.core.parser import MedicalParameterParser
from visiondx.database.models import Parameter, Patient, Prediction, Report
from visiondx.database.schemas import (
    FullReportResponse,
    ParsedReport,
    PredictionOut,
    ReportAnalysisResponse,
    ReportOut,
)
from visiondx.ml.predictor import DiseasePredictor

_ocr = PDFExtractor()
_parser = MedicalParameterParser()
_detector = AbnormalDetector()
_highlighter = HighlightEngine()


async def save_upload(file_bytes: bytes, original_filename: str) -> str:
    """Save uploaded PDF to disk and return its path."""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{Path(original_filename).name}"
    dest = upload_dir / safe_name
    async with aiofiles.open(dest, "wb") as f:
        await f.write(file_bytes)
    return str(dest)


async def process_report(
    pdf_path: str,
    db: AsyncSession,
    app_user_id: str | None = None,
) -> Report:
    """
    Full pipeline: OCR → parse → detect → predict → persist.
    Returns the saved Report ORM object.
    """
    # 1. OCR
    logger.info(f"Starting OCR on {pdf_path}")
    raw_text = _ocr.extract(pdf_path)

    # 2. Parse
    parsed: ParsedReport = _parser.parse(raw_text)
    if not parsed.report_id:
        parsed.report_id = _generate_report_id()

    # 3. Abnormal detection
    all_params, abnormal = _detector.detect(parsed.parameters)

    # 4. Disease prediction
    predictor = DiseasePredictor.get()
    predictions: list[PredictionOut] = predictor.predict(all_params)

    # 5. Persist patient
    patient = Patient(
        name=parsed.patient_name or "Unknown",
        age=int(parsed.age) if parsed.age and parsed.age.isdigit() else None,
        gender=parsed.gender,
    )
    db.add(patient)
    await db.flush()

    # 6. Persist report
    report = Report(
        report_id=parsed.report_id,
        app_user_id=app_user_id,
        patient_id=patient.id,
        pdf_path=pdf_path,
        raw_text=raw_text[:10000],  # truncate for DB storage
        status="done",
        report_date=parsed.date,
        lab_name=parsed.lab_name,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(report)
    await db.flush()

    # 7. Persist parameters
    for p in all_params:
        param = Parameter(
            report_id=report.id,
            name=p.name,
            raw_name=p.raw_name,
            value=p.value,
            raw_value=p.raw_value,
            unit=p.unit,
            reference_range=p.reference_range,
            status=p.status,
        )
        db.add(param)

    # 8. Persist predictions
    for pred in predictions:
        db.add(Prediction(
            report_id=report.id,
            disease=pred.disease,
            confidence=pred.confidence,
        ))

    await db.flush()
    logger.success(f"Report {parsed.report_id} processed successfully")
    return report


async def get_report_by_id(report_id: str, db: AsyncSession) -> Report | None:
    """Fetch a report with its patient, parameters, and predictions."""
    result = await db.execute(
        select(Report)
        .options(
            selectinload(Report.patient),
            selectinload(Report.parameters),
            selectinload(Report.predictions),
        )
        .where(Report.report_id == report_id)
    )
    return result.scalar_one_or_none()


async def list_reports_by_app_user(
    app_user_id: str, db: AsyncSession, limit: int = 100
) -> list[Report]:
    """List reports belonging to an app user."""
    result = await db.execute(
        select(Report)
        .options(
            selectinload(Report.patient),
            selectinload(Report.parameters),
            selectinload(Report.predictions),
        )
        .where(Report.app_user_id == app_user_id)
        .order_by(Report.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_reports_with_abnormal(
    db: AsyncSession, limit: int = 50
) -> list[tuple[Report, int]]:
    """
    List reports that have at least one abnormal parameter (LOW/HIGH).
    Returns list of (Report, abnormal_count) sorted by abnormal_count desc.
    """
    from sqlalchemy import func
    from visiondx.database.models import Parameter

    # Subquery: report_id -> count of abnormal params
    abnormal_counts = (
        select(Parameter.report_id, func.count(Parameter.id).label("abnormal_count"))
        .where(Parameter.status.in_(["LOW", "HIGH"]))
        .group_by(Parameter.report_id)
        .subquery()
    )
    result = await db.execute(
        select(Report, abnormal_counts.c.abnormal_count)
        .join(abnormal_counts, Report.id == abnormal_counts.c.report_id)
        .options(
            selectinload(Report.patient),
            selectinload(Report.parameters),
            selectinload(Report.predictions),
            selectinload(Report.app_user),
        )
        .order_by(abnormal_counts.c.abnormal_count.desc())
        .limit(limit)
    )
    return [(row[0], row[1]) for row in result.all()]


async def build_report_analysis(
    report: Report,
) -> ReportAnalysisResponse:
    """Build structured analysis response."""
    from visiondx.database.schemas import ParameterOut

    params = [ParameterOut.model_validate(p) for p in report.parameters]
    abnormal = [p for p in params if p.status != "NORMAL"]
    predictions = [
        PredictionOut.model_validate(pred) for pred in report.predictions
    ]
    summary = _highlighter.generate_summary(
        report.parameters, predictions  # type: ignore[arg-type]
    )
    return ReportAnalysisResponse(
        report_id=report.report_id,
        total_parameters=len(params),
        abnormal_count=len(abnormal),
        normal_count=len(params) - len(abnormal),
        parameters=params,
        summary=summary,
    )


async def build_full_report(report: Report, base_url: str = "") -> FullReportResponse:
    """Build full doctor-facing report response."""
    from visiondx.database.schemas import ParameterOut, PatientOut

    params = [ParameterOut.model_validate(p) for p in report.parameters]
    predictions = [PredictionOut.model_validate(pred) for pred in report.predictions]
    patient = PatientOut.model_validate(report.patient) if report.patient else None
    summary = _highlighter.generate_summary(
        report.parameters, predictions  # type: ignore[arg-type]
    )
    pdf_url = (
        f"{base_url}/pdf/{report.report_id}"
        if report.pdf_path else None
    )
    return FullReportResponse(
        report_id=report.report_id,
        status=report.status,
        patient=patient,
        parameters=params,
        predictions=predictions,
        summary=summary,
        pdf_url=pdf_url,
    )


def _generate_report_id() -> str:
    """Generate a unique report ID in format VDX-YYYYMMDD-XXXX."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"VDX-{date_part}-{unique_part}"
