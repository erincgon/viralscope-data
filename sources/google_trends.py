"""Google Trends daily trending searches via public RSS feed."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from config.settings import get_settings
from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class GoogleTrendsScraper(BaseScraper):
    """Scrape Google Trends daily RSS (public, no auth required)."""

    source_name = "google_trends"

    RSS_URL = "https://trends.google.com/trending/rss"

    async def scrape(self) -> ScraperResult:
        settings = get_settings()
        geo = settings.scraping.google_trends_geo
        trends = []

        async with AsyncHTTPClient() as client:
            xml_text = await client.get(self.RSS_URL, params={"geo": geo})
            root = ET.fromstring(xml_text)

            for item in root.findall(".//item")[:15]:
                title_el = item.find("title")
                desc_el = item.find("description")
                link_el = item.find("link")

                if title_el is None or not title_el.text:
                    continue

                title = title_el.text.strip()
                description = (
                    desc_el.text.strip()
                    if desc_el is not None and desc_el.text
                    else f"Trending on Google in {geo}"
                )

                trends.append(
                    self._build_trend(
                        title=title,
                        category="News",
                        description=description,
                        best_platform="YouTube",
                        raw_signals={
                            "link": link_el.text if link_el is not None else "",
                            "geo": geo,
                            "signal_type": "search_spike",
                        },
                    )
                )

        return ScraperResult(source=self.source_name, trends=trends)
