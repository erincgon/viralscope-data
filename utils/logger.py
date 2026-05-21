"""Structured logging setup using loguru."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from config.settings import get_settings

_configured = False


def setup_logging() -> None:
    """Configure loguru with console and file sinks."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    log_dir: Path = settings.logging.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.logging.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    logger.add(
        log_dir / "viralscope_{time:YYYY-MM-DD}.log",
        level=settings.logging.log_level,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        enqueue=True,
    )

    _configured = True
    logger.info("Logging initialized")


def get_logger(name: str):
    """Return a contextualized logger instance."""
    return logger.bind(module=name)
