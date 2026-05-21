"""Centralized JSON export system for Flutter app consumption."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config.settings import get_settings
from models.trend import Trend


class JSONExporter:
    """Export trends to free.json, premium.json, and trends.json."""

    EXPORT_VERSION = "1.0.0"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.export_dir = self.settings.export.export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        trends: list[Trend],
        *,
        analytics: dict[str, Any] | None = None,
        scraper_stats: dict[str, Any] | None = None,
    ) -> dict[str, Path]:
        """Export all JSON files and return paths."""
        generated_at = datetime.now(timezone.utc).isoformat()

        master_payload = self._build_master_payload(
            trends, generated_at, analytics, scraper_stats
        )
        free_payload = self._build_free_payload(trends, generated_at)
        premium_payload = self._build_premium_payload(trends, generated_at, analytics)

        paths = {
            "trends": self._write(
                self.settings.export.filenames["master"], master_payload
            ),
            "free": self._write(
                self.settings.export.filenames["free"], free_payload
            ),
            "premium": self._write(
                self.settings.export.filenames["premium"], premium_payload
            ),
        }

        logger.info(
            f"Export complete: {len(trends)} trends → "
            f"free({self.settings.export.free_trend_limit}), "
            f"premium({len(trends)}), master({len(trends)})"
        )
        return paths

    def _build_master_payload(
        self,
        trends: list[Trend],
        generated_at: str,
        analytics: dict[str, Any] | None,
        scraper_stats: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build master trends.json with all raw data."""
        return {
            "meta": {
                "engine": "ViralScope Engine",
                "version": self.EXPORT_VERSION,
                "generated_at": generated_at,
                "total_trends": len(trends),
                "analytics": analytics or {},
                "scraper_stats": scraper_stats or {},
            },
            "trends": [t.to_dict() for t in trends],
        }

    def _build_free_payload(
        self, trends: list[Trend], generated_at: str
    ) -> dict[str, Any]:
        """Build free.json with limited trends and fields."""
        limit = self.settings.export.free_trend_limit
        allowed_fields = set(self.settings.export.free_fields)

        free_trends = []
        for trend in trends[:limit]:
            full = trend.to_dict()
            filtered = {k: v for k, v in full.items() if k in allowed_fields}
            free_trends.append(filtered)

        return {
            "meta": {
                "engine": "ViralScope Engine",
                "version": self.EXPORT_VERSION,
                "tier": "free",
                "generated_at": generated_at,
                "total_trends": len(free_trends),
                "upgrade_message": "Upgrade to PRO for full trend intelligence, hooks, and hashtags",
            },
            "trends": free_trends,
        }

    def _build_premium_payload(
        self,
        trends: list[Trend],
        generated_at: str,
        analytics: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build premium.json with full trend intelligence."""
        premium_trends = []
        for trend in trends:
            data = trend.to_dict()
            # Exclude internal raw_signals from premium export
            data.pop("raw_signals", None)
            data.pop("source", None)
            premium_trends.append(data)

        return {
            "meta": {
                "engine": "ViralScope Engine",
                "version": self.EXPORT_VERSION,
                "tier": "premium",
                "generated_at": generated_at,
                "total_trends": len(premium_trends),
                "analytics": analytics or {},
            },
            "trends": premium_trends,
        }

    def _write(self, filename: str, payload: dict[str, Any]) -> Path:
        """Write JSON file with pretty formatting."""
        path = self.export_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {path}")
        return path
