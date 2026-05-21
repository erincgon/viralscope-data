"""YouTube trending content via public RSS feeds."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from config.settings import get_settings
from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class YouTubeTrendingScraper(BaseScraper):
    """Scrape YouTube trending via public RSS (no API key required)."""

    source_name = "youtube_trending"

    RSS_URL = "https://www.youtube.com/feeds/videos.xml"

    # Public channel IDs for high-signal trending-adjacent content
    TRENDING_CHANNELS: dict[str, str] = {
        "UCBJycsmduvYEL83R_U4JriQ": "Technology",
        "UCX6OQ3DkcsbYNE6H8uQQuVA": "Entertainment",
        "UC-lHJZR3Gqxm24_Vd_AJ5Yw": "Gaming",
        "UC8butISFwT-Wl7EV0hUK0BQ": "Education",
    }

    async def scrape(self) -> ScraperResult:
        settings = get_settings()
        region = settings.scraping.youtube_region
        trends = []

        async with AsyncHTTPClient() as client:
            for channel_id, category in self.TRENDING_CHANNELS.items():
                try:
                    xml_text = await client.get(
                        self.RSS_URL,
                        params={"channel_id": channel_id},
                    )
                    root = ET.fromstring(xml_text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}

                    for entry in root.findall("atom:entry", ns)[:3]:
                        title_el = entry.find("atom:title", ns)
                        if title_el is None or not title_el.text:
                            continue

                        title = title_el.text.strip()
                        trends.append(
                            self._build_trend(
                                title=title,
                                category=category,
                                description=(
                                    f"Viral YouTube content signal from {category.lower()} "
                                    f"creators ({region})"
                                ),
                                best_platform="YouTube",
                                raw_signals={
                                    "channel_id": channel_id,
                                    "region": region,
                                    "signal_type": "video_trend",
                                },
                            )
                        )
                except Exception:
                    continue

        return ScraperResult(source=self.source_name, trends=trends)
