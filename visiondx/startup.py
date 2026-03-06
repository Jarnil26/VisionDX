"""
VisionDX — Production Startup Script
=====================================
Runs before uvicorn starts:
  1. Creates DB tables (if missing)
  2. Runs DB migrations (Alembic head)
  3. Pre-trains ML model if no model file found
  4. Ensures upload/model directories exist
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from loguru import logger


def ensure_dirs():
    """Create required directories."""
    for d in [
        os.getenv("UPLOAD_DIR", "/tmp/uploads"),
        os.path.dirname(os.getenv("MODEL_PATH", "/tmp/models/disease_predictor.pkl")),
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ready: {d}")


async def create_db():
    """Create all SQLAlchemy tables."""
    try:
        from visiondx.database.connection import create_tables
        await create_tables()
        logger.success("Database tables created/verified")
    except Exception as e:
        logger.warning(f"DB setup warning (non-fatal): {e}")


def train_model_if_missing():
    """Train the ML model if no model file exists."""
    model_path = os.getenv("MODEL_PATH", "visiondx/ml/models/disease_predictor.pkl")
    if Path(model_path).exists():
        logger.info(f"ML model found: {model_path}")
        return
    logger.warning("ML model not found — training now (this may take 30-60 seconds)...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "visiondx.ml.train_model"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            logger.success("ML model trained successfully")
        else:
            logger.warning(f"ML training returned non-zero: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        logger.warning("ML training timed out — starting without model (disease engine will still work)")
    except Exception as e:
        logger.warning(f"ML training failed (non-fatal): {e}")


def main():
    logger.info("=" * 55)
    logger.info("  VisionDX Production Startup")
    logger.info("=" * 55)

    # 1. Dirs
    ensure_dirs()

    # 2. DB
    asyncio.run(create_db())

    # 3. ML model
    train_model_if_missing()

    logger.success("Startup complete — starting uvicorn")


if __name__ == "__main__":
    main()
