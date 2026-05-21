#!/usr/bin/env python3
"""
ViralScope Engine — Automated viral content trend intelligence system.

Scrapes public trend signals, scores opportunities with rule-based analysis,
generates creator content templates, and exports JSON feeds for the Flutter app.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any

import schedule
from loguru import logger

from analyzers.content_generator import ContentGenerator
from analyzers.scoring_engine import ScoringEngine
from config.settings import get_settings
from exporters.json_exporter import JSONExporter
from models.trend import Trend
from sources import ALL_SCRAPERS, BaseScraper
from utils.logger import setup_logging


class ViralScopeEngine:
    """Main orchestrator for the trend intelligence pipeline."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.scoring_engine = ScoringEngine()
        self.content_generator = ContentGenerator()
        self.exporter = JSONExporter()

    async def run_pipeline(self) -> dict[str, Any]:
        """Execute the full scrape → analyze → score → export pipeline."""
        start = datetime.now(timezone.utc)
        logger.info("=" * 60)
        logger.info("ViralScope Engine pipeline started (free / rule-based)")
        logger.info("=" * 60)

        # Phase 1: Scrape
        raw_trends, scraper_stats = await self._run_scrapers()
        logger.info(f"Collected {len(raw_trends)} raw trend signals")

        # Phase 2: Deduplicate and merge cross-source signals
        trends = self._deduplicate(raw_trends)
        logger.info(f"After deduplication: {len(trends)} unique trends")

        # Phase 3: Score
        trends = self.scoring_engine.score_trends(trends)
        analytics = self.scoring_engine.generate_analytics_summary(trends)
        logger.info(
            f"Scoring complete — avg viral score: {analytics.get('avg_viral_score', 0)}"
        )

        # Phase 4: Rule-based content enrichment
        trends = self.content_generator.enrich_trends(trends)
        logger.info("Content enrichment complete")

        # Phase 5: Export
        export_paths = self.exporter.export_all(
            trends,
            analytics=analytics,
            scraper_stats=scraper_stats,
        )

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        summary = {
            "success": True,
            "total_trends": len(trends),
            "elapsed_seconds": round(elapsed, 2),
            "exports": {k: str(v) for k, v in export_paths.items()},
            "analytics": analytics,
            "scraper_stats": scraper_stats,
        }

        logger.info(f"Pipeline completed in {elapsed:.1f}s — {len(trends)} trends exported")
        return summary

    async def _run_scrapers(self) -> tuple[list[Trend], dict[str, Any]]:
        """Run all scrapers concurrently with isolated error handling."""
        scrapers: list[BaseScraper] = [cls() for cls in ALL_SCRAPERS]
        semaphore = asyncio.Semaphore(self.settings.scraping.concurrent_requests)

        async def run_with_limit(scraper: BaseScraper):
            async with semaphore:
                return await scraper.run()

        results = await asyncio.gather(
            *[run_with_limit(s) for s in scrapers],
            return_exceptions=True,
        )

        all_trends: list[Trend] = []
        stats: dict[str, Any] = {
            "total_sources": len(scrapers),
            "successful": 0,
            "failed": 0,
            "sources": {},
        }

        for scraper, result in zip(scrapers, results):
            source = scraper.source_name
            if isinstance(result, Exception):
                stats["failed"] += 1
                stats["sources"][source] = {
                    "success": False,
                    "error": str(result),
                    "trends_count": 0,
                }
                logger.error(f"Scraper {source} raised exception: {result}")
            elif result.success:
                stats["successful"] += 1
                stats["sources"][source] = {
                    "success": True,
                    "trends_count": len(result.trends),
                }
                all_trends.extend(result.trends)
            else:
                stats["failed"] += 1
                stats["sources"][source] = {
                    "success": False,
                    "error": result.error,
                    "trends_count": 0,
                }

        return all_trends, stats

    def _normalize_key(self, title: str) -> str:
        """Normalize title for fuzzy deduplication."""
        key = title.lower().strip()
        key = re.sub(r"[^\w\s]", "", key)
        return " ".join(key.split())

    def _deduplicate(self, trends: list[Trend]) -> list[Trend]:
        """Merge duplicate trends and aggregate cross-source signals."""
        merged: dict[str, Trend] = {}

        for trend in trends:
            key = self._normalize_key(trend.title)
            if len(key) <= 2:
                continue

            if key not in merged:
                trend.raw_signals["source_mentions"] = 1
                trend.raw_signals.setdefault("merged_sources", [trend.source])
                merged[key] = trend
                continue

            existing = merged[key]
            existing.raw_signals["source_mentions"] = (
                existing.raw_signals.get("source_mentions", 1) + 1
            )
            sources = existing.raw_signals.setdefault("merged_sources", [existing.source])
            if trend.source not in sources:
                sources.append(trend.source)

            # Keep richer engagement signals
            for field in ("score", "num_comments", "google_rank", "feed_position"):
                new_val = trend.raw_signals.get(field)
                old_val = existing.raw_signals.get(field)
                if new_val is not None and (old_val is None or new_val > old_val):
                    existing.raw_signals[field] = new_val

            if len(trend.description) > len(existing.description):
                existing.description = trend.description

        return list(merged.values())


def run_once() -> dict[str, Any]:
    """Run the pipeline once synchronously."""
    engine = ViralScopeEngine()
    return asyncio.run(engine.run_pipeline())


def start_scheduler() -> None:
    """Start the 6-hour automation scheduler."""
    settings = get_settings()
    interval = settings.scheduler.interval_hours

    logger.info(f"Scheduler started — running every {interval} hours")

    if settings.scheduler.run_on_startup:
        logger.info("Running initial pipeline on startup...")
        run_once()

    schedule.every(interval).hours.do(run_once)

    stop = False

    def handle_signal(signum: int, frame: Any) -> None:
        nonlocal stop
        logger.info("Shutdown signal received — stopping scheduler")
        stop = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while not stop:
        schedule.run_pending()
        time.sleep(30)

    logger.info("Scheduler stopped")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ViralScope Engine — Viral content trend intelligence"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "schedule", "export-sample"],
        help="Command: run (once), schedule (daemon), export-sample (demo data)",
    )
    return parser.parse_args()


def export_sample() -> None:
    """Generate sample exports without scraping (for development/demo)."""
    from models.trend import TrendCategory, GrowthVelocity, CompetitionLevel, SaturationRisk

    sample_trends = [
        Trend(
            title="AI Avatar Story Channels",
            category=TrendCategory.CREATOR,
            description="Faceless AI-generated narrative channels exploding on YouTube Shorts",
            source="sample",
            viral_score=94,
            confidence_score=89,
            growth_velocity=GrowthVelocity.EXTREME,
            competition_level=CompetitionLevel.LOW,
            saturation_risk=SaturationRisk.LOW,
            best_platform="YouTube Shorts",
            thumbnail_text="AI STORIES GO VIRAL",
            hashtags=["#AIStories", "#FacelessYouTube", "#Shorts", "#ViralAI"],
            hook_ideas=[
                "This AI channel got 1M views in 30 days — here's how",
                "I built an AI avatar channel in one weekend",
                "Why faceless AI content is the next gold rush",
            ],
            ai_analysis=(
                "AI avatar storytelling represents an extreme-growth opportunity with "
                "low competition. Early movers are capturing massive view counts with "
                "minimal production costs."
            ),
            creator_insights=[
                "Launch within 2 weeks before saturation increases",
                "Focus on emotional storytelling hooks",
                "Cross-post to TikTok for maximum reach",
            ],
        ),
        Trend(
            title="Micro SaaS Build in Public",
            category=TrendCategory.TECHNOLOGY,
            description="Developers documenting tiny SaaS products gaining loyal audiences",
            source="sample",
            viral_score=87,
            confidence_score=82,
            growth_velocity=GrowthVelocity.HIGH,
            competition_level=CompetitionLevel.MEDIUM,
            saturation_risk=SaturationRisk.LOW,
            best_platform="YouTube",
            thumbnail_text="I BUILT A $1K/MO APP",
            hashtags=["#BuildInPublic", "#MicroSaaS", "#IndieHacker", "#SideProject"],
            hook_ideas=[
                "I built a $1K/month app in 48 hours — full breakdown",
                "The micro SaaS nobody is building (but should)",
                "From zero to $500 MRR: my 30-day build journey",
            ],
            ai_analysis=(
                "Build-in-public content continues strong growth with medium competition. "
                "Authentic revenue milestones drive engagement and community building."
            ),
            creator_insights=[
                "Share real revenue numbers for credibility",
                "Document failures alongside wins",
                "Engage in indie hacker communities for cross-promotion",
            ],
        ),
        Trend(
            title="Oddly Satisfying Process Videos",
            category=TrendCategory.SHORT_FORM,
            description="ASMR-adjacent process content with loop-worthy appeal on Reels",
            source="sample",
            viral_score=91,
            confidence_score=85,
            growth_velocity=GrowthVelocity.EXTREME,
            competition_level=CompetitionLevel.MEDIUM,
            saturation_risk=SaturationRisk.MEDIUM,
            best_platform="Instagram Reels",
            thumbnail_text="SO SATISFYING",
            hashtags=["#OddlySatisfying", "#ASMR", "#Reels", "#Viral"],
            hook_ideas=[
                "Watch this for 10 seconds — you won't look away",
                "The most satisfying process you've ever seen",
                "This video has a 95% replay rate — here's why",
            ],
            ai_analysis=(
                "Satisfying process content maintains extreme growth velocity on short-form "
                "platforms. High replay rates boost algorithmic distribution significantly."
            ),
            creator_insights=[
                "Invest in macro lens for close-up shots",
                "Keep videos under 15 seconds for max replays",
                "Post during evening hours for peak engagement",
            ],
        ),
        Trend(
            title="Budget Solo Travel Vlogs",
            category=TrendCategory.LIFESTYLE,
            description="Affordable solo travel content targeting Gen Z wanderlust",
            source="sample",
            viral_score=78,
            confidence_score=74,
            growth_velocity=GrowthVelocity.HIGH,
            competition_level=CompetitionLevel.LOW,
            saturation_risk=SaturationRisk.LOW,
            best_platform="TikTok",
        ),
        Trend(
            title="ADHD Productivity Frameworks",
            category=TrendCategory.EDUCATION,
            description="Neurodivergent-friendly productivity systems gaining traction",
            source="sample",
            viral_score=83,
            confidence_score=80,
            growth_velocity=GrowthVelocity.HIGH,
            competition_level=CompetitionLevel.LOW,
            saturation_risk=SaturationRisk.LOW,
            best_platform="YouTube",
        ),
    ]

    scoring = ScoringEngine()
    scored = scoring.score_trends(sample_trends)
    enriched = ContentGenerator().enrich_trends(scored)
    analytics = scoring.generate_analytics_summary(enriched)

    exporter = JSONExporter()
    paths = exporter.export_all(enriched, analytics=analytics, scraper_stats={"mode": "sample"})
    logger.info(f"Sample exports generated: {paths}")


def main() -> None:
    setup_logging()
    args = parse_args()

    try:
        if args.command == "run":
            result = run_once()
            if not result.get("success"):
                sys.exit(1)
        elif args.command == "schedule":
            start_scheduler()
        elif args.command == "export-sample":
            export_sample()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
