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

    request_timeout: int = 25
    max_retries: int = 3
    retry_delay: float = 1.5
    retry_backoff: float = 2.0
    concurrent_requests: int = 4
    google_trends_geo: str = "US"
    reddit_subreddits: tuple[str, ...] = (
        "popular",
        "videos",
        "TikTokCringe",
        "YouTube",
        "ContentCreation",
        "socialmedia",
    )
    youtube_region: str = "US"
    use_pytrends: bool = True
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "ViralScopeEngine/2.0 (trend research)"


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
    export: ExportSettings = field(default_factory=ExportSettings)
    scheduler: SchedulerSettings = field(default_factory=SchedulerSettings)
    logging: LogSettings = field(default_factory=LogSettings)
    project_root: Path = PROJECT_ROOT

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables."""
        reddit_id = os.getenv("REDDIT_CLIENT_ID", "")
        reddit_secret = os.getenv("REDDIT_CLIENT_SECRET", "")

        return cls(
            scraping=ScrapingSettings(
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", "25")),
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                retry_delay=float(os.getenv("RETRY_DELAY", "1.5")),
                retry_backoff=float(os.getenv("RETRY_BACKOFF", "2.0")),
                concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "4")),
                google_trends_geo=os.getenv("GOOGLE_TRENDS_GEO", "US"),
                youtube_region=os.getenv("YOUTUBE_REGION", "US"),
                use_pytrends=os.getenv("USE_PYTRENDS", "true").lower() == "true",
                reddit_client_id=reddit_id,
                reddit_client_secret=reddit_secret,
                reddit_user_agent=os.getenv(
                    "REDDIT_USER_AGENT", "ViralScopeEngine/2.0 (trend research)"
                ),
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
