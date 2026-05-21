"""Base scraper interface for all trend sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from models.trend import Trend


@dataclass
class ScraperResult:
    """Result envelope from a scraper run."""

    source: str
    trends: list[Trend] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract base class for all trend scrapers."""

    source_name: str = "unknown"
    enabled: bool = True

    @abstractmethod
    async def scrape(self) -> ScraperResult:
        """Fetch trends from the source."""
        ...

    async def run(self) -> ScraperResult:
        """Execute scraper with error handling."""
        if not self.enabled:
            logger.info(f"Scraper {self.source_name} is disabled, skipping")
            return ScraperResult(source=self.source_name, trends=[], success=True)

        try:
            logger.info(f"Starting scraper: {self.source_name}")
            result = await self.scrape()
            logger.info(
                f"Scraper {self.source_name} completed: {len(result.trends)} trends"
            )
            return result
        except Exception as exc:
            logger.error(f"Scraper {self.source_name} failed: {exc}")
            return ScraperResult(
                source=self.source_name,
                trends=[],
                success=False,
                error=str(exc),
            )

    def _build_trend(
        self,
        *,
        title: str,
        category: str,
        description: str,
        raw_signals: dict[str, Any] | None = None,
        best_platform: str = "Multi-Platform",
    ) -> Trend:
        """Helper to construct a Trend with source metadata."""
        from models.trend import TrendCategory

        try:
            cat = TrendCategory(category)
        except ValueError:
            cat = TrendCategory.GENERAL

        return Trend(
            title=title.strip(),
            category=cat,
            description=description.strip(),
            source=self.source_name,
            best_platform=best_platform,
            raw_signals=raw_signals or {},
        )
