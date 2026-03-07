"""
VisionDX — FastAPI Application Entry Point

Registers all routers, configures middleware, lifecycle events.
Production-grade error handling, authentication, and logging.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
import time

from visiondx.config import settings
from visiondx.database.connection import create_tables
from visiondx.api.routes import auth, reports, doctor, developer, public_api, users, labs, follow_ups, chat
from visiondx.database.api_key_models import ApiDeveloper, ApiKey
from visiondx.ml.predictor import DiseasePredictor

# ── Middleware Imports ─────────────────────────────────────────────────────────
from visiondx.api.middleware import (
    setup_logging,
    register_error_handlers,
)


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


# ── Request Timing Middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers."""
    start_time = time.time()
    
    # Log incoming request
    logger.debug(
        f"→ {request.method} {request.url.path}",
        method=request.method,
        path=request.url.path,
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    log_level = "warning" if response.status_code >= 400 else "debug"
    logger_func = getattr(logger, log_level)
    logger_func(
        f"← {response.status_code} {request.url.path} ({process_time:.3f}s)",
        status_code=response.status_code,
        method=request.method,
        path=request.url.path,
        duration=process_time,
    )
    
    return response


# ── Error Handlers & Logging ──────────────────────────────────────────────────
register_error_handlers(app)
setup_logging()

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(doctor.router)
# App users (patients): register, login, profile, my reports, upload
app.include_router(users.router)
# Labs: list labs, bookings; Lab API for report submission
app.include_router(labs.router)
app.include_router(labs.lab_api_router)
# Weekly & monthly follow-ups
app.include_router(follow_ups.router)
# AI Chat Doctor
app.include_router(chat.router)
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
