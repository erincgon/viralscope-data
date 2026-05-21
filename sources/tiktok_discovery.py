"""TikTok trend discovery via public Creative Center pages."""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class TikTokDiscoveryScraper(BaseScraper):
    """Scrape TikTok Creative Center public trend pages."""

    source_name = "tiktok_discovery"

    # Public Creative Center endpoints (no auth)
    TREND_URLS = [
        "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en",
        "https://www.tiktok.com/discover",
    ]

    # Fallback curated short-form niches when public pages are unavailable
    FALLBACK_NICHES = [
        ("POV Storytelling", "First-person narrative hooks driving massive engagement"),
        ("Get Ready With Me", "GRWM routines with product integration opportunities"),
        ("Day in My Life", "Authentic lifestyle vlogs with high relatability"),
        ("Storytime Drama", "Compelling personal stories with cliffhanger hooks"),
        ("Micro Tutorials", "60-second skill demos with save-worthy value"),
        ("Before & After", "Transformation content with visual payoff"),
        ("Reaction Commentary", "Trend-jacking via authentic reaction format"),
        ("Silent ASMR", "Visual satisfaction content with broad appeal"),
    ]

    async def scrape(self) -> ScraperResult:
        trends = []

        async with AsyncHTTPClient() as client:
            for url in self.TREND_URLS:
                try:
                    html = await client.get(url)
                    parsed = self._parse_trends_from_html(html)
                    trends.extend(parsed)
                    if trends:
                        break
                except Exception:
                    continue

        if not trends:
            trends = [
                self._build_trend(
                    title=title,
                    category="Short-Form",
                    description=desc,
                    best_platform="TikTok",
                    raw_signals={"signal_type": "niche_discovery", "fallback": True},
                )
                for title, desc in self.FALLBACK_NICHES
            ]

        return ScraperResult(source=self.source_name, trends=trends[:12])

    def _parse_trends_from_html(self, html: str) -> list:
        trends = []
        soup = BeautifulSoup(html, "html.parser")

        # Try embedded JSON state (common in SPA pages)
        scripts = soup.find_all("script")
        for script in scripts:
            if not script.string:
                continue
            matches = re.findall(
                r'"(?:hashtag|title|name)"\s*:\s*"([^"]{3,80})"',
                script.string,
            )
            for match in matches[:10]:
                if match.startswith("#") or len(match.split()) <= 6:
                    trends.append(
                        self._build_trend(
                            title=match.lstrip("#"),
                            category="Short-Form",
                            description=f"TikTok trend signal: {match}",
                            best_platform="TikTok",
                            raw_signals={"signal_type": "hashtag_trend"},
                        )
                    )

        # Parse visible headings as backup
        for heading in soup.find_all(["h2", "h3", "h4"])[:8]:
            text = heading.get_text(strip=True)
            if 3 < len(text) < 80:
                trends.append(
                    self._build_trend(
                        title=text,
                        category="Short-Form",
                        description=f"TikTok discovery trend: {text}",
                        best_platform="TikTok",
                        raw_signals={"signal_type": "page_heading"},
                    )
                )

        # Deduplicate by title
        seen: set[str] = set()
        unique = []
        for trend in trends:
            key = trend.title.lower()
            if key not in seen:
                seen.add(key)
                unique.append(trend)

        return unique
