"""Google Trends daily trending searches via public RSS + optional pytrends."""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET

from loguru import logger

from config.settings import get_settings
from models.trend import TrendCategory
from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class GoogleTrendsScraper(BaseScraper):
    """Scrape Google Trends daily RSS (public, no auth required)."""

    source_name = "google_trends"

    RSS_URL = "https://trends.google.com/trending/rss"

    async def scrape(self) -> ScraperResult:
        settings = get_settings()
        geo = settings.scraping.google_trends_geo
        trends: list = []

        async with AsyncHTTPClient() as client:
            xml_text = await client.get(self.RSS_URL, params={"geo": geo})
            root = ET.fromstring(xml_text)

            for rank, item in enumerate(root.findall(".//item")[:20], start=1):
                title_el = item.find("title")
                desc_el = item.find("description")
                link_el = item.find("link")
                traffic_el = item.find(
                    "{https://trends.google.com/trending/rss}approx_traffic"
                )

                if title_el is None or not title_el.text:
                    continue

                title = title_el.text.strip()
                description = (
                    desc_el.text.strip()
                    if desc_el is not None and desc_el.text
                    else f"Trending on Google Search in {geo} (rank #{rank})"
                )

                traffic = (
                    traffic_el.text.strip()
                    if traffic_el is not None and traffic_el.text
                    else ""
                )

                trends.append(
                    self._build_trend(
                        title=title,
                        category=self._categorize(title),
                        description=description,
                        best_platform="YouTube",
                        raw_signals={
                            "link": link_el.text if link_el is not None else "",
                            "geo": geo,
                            "google_rank": rank,
                            "traffic": traffic,
                            "signal_type": "search_spike",
                            "velocity_hint": "extreme" if rank <= 3 else "high",
                        },
                    )
                )

        if settings.scraping.use_pytrends and len(trends) < 8:
            try:
                extra = await asyncio.to_thread(self._fetch_pytrends, geo)
                trends = self._merge_pytrends(trends, extra)
            except Exception as exc:
                logger.debug(f"pytrends supplement skipped: {exc}")

        return ScraperResult(source=self.source_name, trends=trends[:18])

    def _categorize(self, title: str) -> str:
        lower = title.lower()
        words = set(re.findall(r"\w+", lower))
        if words & {"game", "gaming", "xbox", "playstation", "nintendo"}:
            return TrendCategory.GAMING.value
        if words & {"stock", "crypto", "bitcoin", "market", "earnings"}:
            return TrendCategory.FINANCE.value
        if words & {"ai", "tech", "iphone", "android", "chatgpt", "openai"}:
            return TrendCategory.TECHNOLOGY.value
        return TrendCategory.NEWS.value

    def _fetch_pytrends(self, geo: str) -> list[dict]:
        """Sync pytrends fetch (runs in thread pool for CI compatibility)."""
        from pytrends.request import TrendReq

        pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        df = pt.trending_searches(pn=geo if geo != "US" else "united_states")
        results: list[dict] = []
        for idx, row in df.head(10).iterrows():
            title = str(row[0]) if hasattr(row, "__getitem__") else str(row)
            results.append({"title": title.strip(), "rank": int(idx) + 1})
        return results

    def _merge_pytrends(self, trends: list, extra: list[dict]) -> list:
        seen = {t.title.lower() for t in trends}
        for item in extra:
            title = item["title"]
            if title.lower() in seen:
                continue
            trends.append(
                self._build_trend(
                    title=title,
                    category=self._categorize(title),
                    description=f"Google Trends realtime signal (rank #{item['rank']})",
                    best_platform="YouTube",
                    raw_signals={
                        "google_rank": item["rank"],
                        "signal_type": "search_spike",
                        "pytrends": True,
                        "velocity_hint": "high",
                    },
                )
            )
            seen.add(title.lower())
        return trends
