"""Centralized configuration for ViralScope Engine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ScrapingSettings:
    """Scraping behavior configuration."""

    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 2.0
    retry_backoff: float = 2.0
    concurrent_requests: int = 5
    google_trends_geo: str = "US"
    reddit_subreddits: tuple[str, ...] = (
        "popular",
        "videos",
        "TikTokCringe",
        "YouTube",
        "ContentCreation",
    )
    youtube_region: str = "US"


@dataclass(frozen=True)
class AISettings:
    """OpenAI model configuration."""

    api_key: str = ""
    model: str = "gpt-4o-mini"
    max_tokens: int = 1200
    temperature: float = 0.7
    batch_size: int = 5
    enabled: bool = True


@dataclass(frozen=True)
class ExportSettings:
    """JSON export configuration."""

    export_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "exports")
    free_trend_limit: int = 3
    free_fields: tuple[str, ...] = (
        "id",
        "title",
        "category",
        "description",
        "viral_score",
        "growth_velocity",
        "best_platform",
        "created_at",
    )
    filenames: dict[str, str] = field(
        default_factory=lambda: {
            "free": "free.json",
            "premium": "premium.json",
            "master": "trends.json",
        }
    )


@dataclass(frozen=True)
class SchedulerSettings:
    """Automation scheduler configuration."""

    interval_hours: int = 6
    run_on_startup: bool = True


@dataclass(frozen=True)
class LogSettings:
    """Logging configuration."""

    log_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    log_level: str = "INFO"
    rotation: str = "10 MB"
    retention: str = "30 days"


@dataclass(frozen=True)
class Settings:
    """Root application settings."""

    scraping: ScrapingSettings = field(default_factory=ScrapingSettings)
    ai: AISettings = field(default_factory=AISettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    scheduler: SchedulerSettings = field(default_factory=SchedulerSettings)
    logging: LogSettings = field(default_factory=LogSettings)
    project_root: Path = PROJECT_ROOT

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables."""
        ai_key = os.getenv("OPENAI_API_KEY", "")
        ai_enabled = os.getenv("AI_ANALYSIS_ENABLED", "true").lower() == "true"

        return cls(
            scraping=ScrapingSettings(
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                retry_delay=float(os.getenv("RETRY_DELAY", "2.0")),
                retry_backoff=float(os.getenv("RETRY_BACKOFF", "2.0")),
                concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "5")),
                google_trends_geo=os.getenv("GOOGLE_TRENDS_GEO", "US"),
                youtube_region=os.getenv("YOUTUBE_REGION", "US"),
            ),
            ai=AISettings(
                api_key=ai_key,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1200")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                batch_size=int(os.getenv("AI_BATCH_SIZE", "5")),
                enabled=ai_enabled and bool(ai_key),
            ),
            export=ExportSettings(
                export_dir=Path(
                    os.getenv("EXPORT_DIR", str(PROJECT_ROOT / "exports"))
                ),
                free_trend_limit=int(os.getenv("FREE_TREND_LIMIT", "3")),
            ),
            scheduler=SchedulerSettings(
                interval_hours=int(os.getenv("SCHEDULE_INTERVAL_HOURS", "6")),
                run_on_startup=os.getenv("RUN_ON_STARTUP", "true").lower()
                == "true",
            ),
            logging=LogSettings(
                log_dir=Path(os.getenv("LOG_DIR", str(PROJECT_ROOT / "logs"))),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
            ),
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
