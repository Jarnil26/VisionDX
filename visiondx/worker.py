"""
VisionDX — Celery Worker

Handles background task processing for long-running report pipelines.
"""
from celery import Celery
from visiondx.config import settings

celery_app = Celery(
    "visiondx",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["visiondx.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_soft_time_limit=120,  # 2 min soft limit
    task_time_limit=180,       # 3 min hard limit
)
