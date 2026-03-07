"""
VisionDX — Public API Routes (API-key protected)
==================================================
These are the endpoints external developers call
after receiving their API key.

Base path: /api/v1
Auth:       X-API-Key header required on all routes

Endpoints:
  POST /api/v1/analyze          Upload PDF → full analysis
  POST /api/v1/analyze/text     Send raw text → analysis
  GET  /api/v1/report/{id}      Get report JSON
  GET  /api/v1/report/{id}/analysis      Abnormal values
  GET  /api/v1/report/{id}/prediction    Disease predictions
  GET  /api/v1/ping             Health check (no auth)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.api.middleware.api_auth import require_api_key
from visiondx.config import settings
from visiondx.database.api_key_models import ApiDeveloper
from visiondx.database.connection import get_db
from visiondx.database.schemas import (
    FullReportResponse, PredictionOut, PredictionResponse,
    ReportAnalysisResponse, ReportOut, UploadResponse,
)
from visiondx.services import report_service

router = APIRouter(prefix="/api/v1", tags=["Public API v1"])


# ── Health check ──────────────────────────────────────────────────────────────

@router.get("/ping", summary="Health check — no auth required")
async def ping():
    """Check if the API is online."""
    return {
        "status": "online",
        "version": "2.0",
        "service": "VisionDX Medical AI API",
        "docs": "/developer/docs",
    }


# ── PDF Upload & Analysis ─────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=UploadResponse,
    status_code=202,
    summary="Upload lab report PDF → get Report ID",
    description="""
Upload a blood test / lab report PDF.

**Pipeline:**
1. OCR text extraction
2. Medical parameter parsing (LOINC standardization)
3. Abnormal value detection
4. AI disease prediction (dynamic engine + ML model)

Returns a `report_id` — use it to fetch results via `/report/{id}`.

**Rate limits:** 100 req/day (Free) · 5,000 req/day (Pro)
""",
)
async def public_analyze(
    file: UploadFile = File(..., description="Lab report PDF (max 20 MB)"),
    db: AsyncSession = Depends(get_db),
    dev: ApiDeveloper = Depends(require_api_key),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb} MB limit")

    pdf_path = await report_service.save_upload(content, file.filename or "report.pdf")
    report   = await report_service.process_report(pdf_path, db)

    return UploadResponse(
        report_id=report.report_id,
        message="Report processed successfully",
        status=report.status,
    )


class TextAnalyzeRequest(BaseModel):
    text: str
    patient_name: str | None = None
    patient_age: int | None = None
    patient_gender: str | None = None

@router.post(
    "/analyze/text",
    summary="Analyze raw lab text (no PDF required)",
    description="""
Send raw text extracted from a lab report.
Useful when you already have the OCR text and don't need to re-process the PDF.

**Example input text:**
```
Patient Name: John Doe
Age: 45  Gender: Male
Glucose: 141 mg/dL  (74-106)
Hemoglobin: 10.2 g/dL (12-17)
Vitamin B12: 148 pg/mL (187-833)
```
""",
)
async def analyze_text(
    body: TextAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    dev: ApiDeveloper = Depends(require_api_key),
):
    from visiondx.core.parser import MedicalParameterParser
    from visiondx.core.abnormal_detector import AbnormalDetector
    from visiondx.ml.predictor import DiseasePredictor

    parser   = MedicalParameterParser()
    detector = AbnormalDetector()
    predictor = DiseasePredictor.get()

    parsed   = parser.parse(body.text)
    if body.patient_name:  parsed.patient_name = body.patient_name
    if body.patient_age:   parsed.age          = str(body.patient_age)
    if body.patient_gender: parsed.gender       = body.patient_gender

    params, abnormal_list = detector.detect(parsed.parameters)
    preds    = predictor.predict(params)

    abnormal = [p for p in params if p.status != "NORMAL"]
    return {
        "patient_name":    parsed.patient_name,
        "age":             parsed.age,
        "gender":          parsed.gender,
        "total_parameters": len(params),
        "abnormal_count":  len(abnormal),
        "parameters": [
            {"name": p.name, "value": p.value, "unit": p.unit,
             "reference_range": p.reference_range, "status": p.status}
            for p in params
        ],
        "predictions": [
            {"disease": p.disease, "confidence": p.confidence}
            for p in preds
        ],
    }


# ── Report fetch endpoints ────────────────────────────────────────────────────

@router.get("/report/{report_id}", response_model=ReportOut, summary="Get parsed report JSON")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    dev: ApiDeveloper = Depends(require_api_key),
):
    report = await report_service.get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(404, f"Report '{report_id}' not found")
    return ReportOut.model_validate(report)


@router.get("/report/{report_id}/analysis", response_model=ReportAnalysisResponse, summary="Get abnormal values + summary")
async def get_analysis(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    dev: ApiDeveloper = Depends(require_api_key),
):
    report = await report_service.get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(404, f"Report '{report_id}' not found")
    return await report_service.build_report_analysis(report)


@router.get("/report/{report_id}/prediction", response_model=PredictionResponse, summary="Get AI disease predictions")
async def get_prediction(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    dev: ApiDeveloper = Depends(require_api_key),
):
    report = await report_service.get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(404, f"Report '{report_id}' not found")
    predictions = [PredictionOut.model_validate(p) for p in report.predictions]
    return PredictionResponse(report_id=report.report_id, possible_conditions=predictions)
