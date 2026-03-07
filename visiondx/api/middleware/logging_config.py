"""
VisionDX — Logging Configuration

Structured logging with loguru.
Logs to console and rotating file.
"""
import sys
from pathlib import Path

from loguru import logger

from visiondx.config import settings


def setup_logging():
    """Configure logging for the application."""
    
    # Remove default handler
    logger.remove()
    
    # Console logging
    logger.add(
        sys.stdout,
        format=(
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=settings.log_level if hasattr(settings, 'log_level') else "INFO",
        colorize=True,
    )
    
    # File logging (rotating)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logger.add(
        logs_dir / "visiondx_{time:YYYY-MM-DD}.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        level="DEBUG",
        rotation="500 MB",
        retention="7 days",
    )
    
    # Error logging (separate file)
    logger.add(
        logs_dir / "visiondx_errors_{time:YYYY-MM-DD}.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        level="ERROR",
        rotation="500 MB",
        retention="30 days",
    )
    
    logger.info(f"Logging configured for {settings.app_name} [{settings.app_env}]")
