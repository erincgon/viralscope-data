"""TikTok trend discovery via public Creative Center and discover pages."""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup
from loguru import logger

from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class TikTokDiscoveryScraper(BaseScraper):
    """Scrape TikTok public trend pages for hashtag popularity signals."""

    source_name = "tiktok_discovery"

    TREND_URLS = [
        "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en",
        "https://www.tiktok.com/discover",
    ]

    FALLBACK_NICHES = [
        ("POV Storytelling", "First-person narrative hooks driving massive engagement", "extreme"),
        ("Get Ready With Me", "GRWM routines with product integration opportunities", "high"),
        ("Day in My Life", "Authentic lifestyle vlogs with high relatability", "high"),
        ("Storytime Drama", "Compelling personal stories with cliffhanger hooks", "high"),
        ("Micro Tutorials", "60-second skill demos with save-worthy value", "moderate"),
        ("Before & After", "Transformation content with visual payoff", "high"),
        ("Reaction Commentary", "Trend-jacking via authentic reaction format", "high"),
        ("Silent ASMR", "Visual satisfaction content with broad appeal", "extreme"),
        ("Creator Economy Tips", "Monetization and growth advice for new creators", "moderate"),
        ("Street Interview", "Spontaneous public Q&A driving comment engagement", "high"),
    ]

    HASHTAG_BLOCKLIST = frozenset(
        {"login", "sign up", "discover", "trending", "popular", "home", "about"}
    )

    async def scrape(self) -> ScraperResult:
        trends = []

        async with AsyncHTTPClient() as client:
            for url in self.TREND_URLS:
                try:
                    html = await client.get(url)
                    parsed = self._parse_trends_from_html(html)
                    trends.extend(parsed)
                    if len(trends) >= 8:
                        break
                except Exception as exc:
                    logger.debug(f"TikTok URL {url} failed: {exc}")
                    continue

        if not trends:
            logger.info("TikTok public pages unavailable — using curated niche fallback")
            trends = [
                self._build_trend(
                    title=title,
                    category="Short-Form",
                    description=desc,
                    best_platform="TikTok",
                    raw_signals={
                        "signal_type": "niche_discovery",
                        "velocity_hint": velocity,
                        "fallback": True,
                    },
                )
                for title, desc, velocity in self.FALLBACK_NICHES
            ]

        return ScraperResult(source=self.source_name, trends=trends[:14])

    def _parse_trends_from_html(self, html: str) -> list:
        trends = []
        soup = BeautifulSoup(html, "html.parser")

        for script in soup.find_all("script"):
            if not script.string:
                continue

            # Embedded JSON state
            for match in re.findall(
                r'"(?:hashtag|hashtagName|title|name)"\s*:\s*"([^"]{3,60})"',
                script.string,
            ):
                clean = match.lstrip("#").strip()
                if clean.lower() in self.HASHTAG_BLOCKLIST:
                    continue
                if len(clean.split()) > 6:
                    continue
                trends.append(
                    self._build_trend(
                        title=clean,
                        category="Short-Form",
                        description=f"TikTok hashtag trend: #{clean}",
                        best_platform="TikTok",
                        raw_signals={
                            "signal_type": "hashtag_trend",
                            "velocity_hint": "high",
                        },
                    )
                )

            # View counts when present in JSON blobs
            view_matches = re.findall(
                r'"(?:videoViews|viewCount|views)"\s*:\s*"?(\d+)"?',
                script.string,
            )
            if view_matches and trends:
                try:
                    trends[-1].raw_signals["hashtag_views"] = int(view_matches[0])
                except ValueError:
                    pass

        for heading in soup.find_all(["h2", "h3", "h4", "span"])[:12]:
            text = heading.get_text(strip=True)
            if not (3 < len(text) < 60):
                continue
            if text.lower() in self.HASHTAG_BLOCKLIST:
                continue
            if text.startswith("#"):
                text = text[1:]
            trends.append(
                self._build_trend(
                    title=text,
                    category="Short-Form",
                    description=f"TikTok discovery trend: {text}",
                    best_platform="TikTok",
                    raw_signals={"signal_type": "page_heading"},
                )
            )

        seen: set[str] = set()
        unique = []
        for trend in trends:
            key = trend.title.lower()
            if key not in seen:
                seen.add(key)
                unique.append(trend)

        return unique
