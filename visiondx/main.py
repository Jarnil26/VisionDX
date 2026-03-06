"""
VisionDX — FastAPI Application Entry Point

Registers all routers, configures middleware, lifecycle events.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger

from visiondx.config import settings
from visiondx.database.connection import create_tables
from visiondx.api.routes import auth, reports, doctor, developer, public_api
from visiondx.database.api_key_models import ApiDeveloper, ApiKey
from visiondx.ml.predictor import DiseasePredictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle."""
    logger.info(f"Starting {settings.app_name} [{settings.app_env}]")

    # Create DB tables (dev mode — use Alembic migrations in production)
    try:
        await create_tables()
        logger.success("Database tables ready")
    except Exception as e:
        logger.warning(f"DB table creation skipped: {e}")

    # Pre-load the ML model
    predictor = DiseasePredictor.get()
    if predictor.is_ready:
        logger.success("Disease prediction model pre-loaded")
    else:
        logger.warning(
            "Prediction model not loaded. "
            "Run `python -m visiondx.ml.train_model` to train."
        )

    # Ensure upload directory exists
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    yield  # Application runs here

    logger.info("VisionDX shutting down")


# ── App Factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="VisionDX Medical AI API",
    description=(
        "## 🧬 VisionDX — AI-Powered Medical Report Analysis API\n\n"
        "Upload any lab report PDF and receive:\n"
        "- Structured parameter extraction (LOINC-normalized)\n"
        "- Abnormal value detection (LOW / NORMAL / HIGH)\n"
        "- Dynamic AI disease predictions\n\n"
        "### 🔐 Authentication\n"
        "All `/api/v1/*` endpoints require an `X-API-Key` header.\n"
        "Get your free API key at `/developer/signup`.\n\n"
        "### 📖 Developer Docs\n"
        "See the **Developer Portal** section below.\n"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(doctor.router)
# Public API (v1) — requires X-API-Key header
app.include_router(public_api.router)
# Developer portal routes — signup, key management
app.include_router(developer.router)


# ── Core Endpoints ────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    predictor = DiseasePredictor.get()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env,
        "model_loaded": predictor.is_ready,
    }


@app.get("/pdf/{report_id}", tags=["System"], include_in_schema=False)
async def serve_pdf(report_id: str):
    """Serve original PDF for a given report ID."""
    # In production, scope this behind auth and serve via signed URLs
    upload_dir = Path(settings.upload_dir)
    # Find any PDF matching the report_id in filename
    matches = list(upload_dir.glob(f"*{report_id}*.pdf"))
    if matches:
        return FileResponse(str(matches[0]), media_type="application/pdf")
    return JSONResponse(status_code=404, content={"detail": "PDF not found"})
