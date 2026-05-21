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

    TRENDING_CHANNELS: dict[str, tuple[str, str]] = {
        "UCBJycsmduvYEL83R_U4JriQ": ("Technology", "YouTube"),
        "UCX6OQ3DkcsbYNE6H8uQQuVA": ("Entertainment", "YouTube"),
        "UC-lHJZR3Gqxm24_Vd_AJ5Yw": ("Gaming", "YouTube"),
        "UC8butISFwT-Wl7EV0hUK0BQ": ("Education", "YouTube"),
        "UCq-Fj5jknLsUf-MWSy4_brA": ("Short-Form", "YouTube Shorts"),
        "UCsBjURrPoezykLs9EqgamOA": ("Creator", "YouTube"),
    }

    async def scrape(self) -> ScraperResult:
        settings = get_settings()
        region = settings.scraping.youtube_region
        trends = []

        async with AsyncHTTPClient() as client:
            for channel_id, (category, platform) in self.TRENDING_CHANNELS.items():
                try:
                    xml_text = await client.get(
                        self.RSS_URL,
                        params={"channel_id": channel_id},
                    )
                    root = ET.fromstring(xml_text)
                    ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}

                    for position, entry in enumerate(root.findall("atom:entry", ns)[:4], start=1):
                        title_el = entry.find("atom:title", ns)
                        if title_el is None or not title_el.text:
                            continue

                        title = title_el.text.strip()
                        views_el = entry.find("yt:videoId", ns)

                        trends.append(
                            self._build_trend(
                                title=title,
                                category=category,
                                description=(
                                    f"YouTube viral signal — {category} creators "
                                    f"({region}), feed position #{position}"
                                ),
                                best_platform=platform,
                                raw_signals={
                                    "channel_id": channel_id,
                                    "region": region,
                                    "feed_position": position,
                                    "video_id": views_el.text if views_el is not None else "",
                                    "signal_type": "video_trend",
                                    "velocity_hint": "extreme" if position == 1 else "high",
                                },
                            )
                        )
                except Exception:
                    continue

        return ScraperResult(source=self.source_name, trends=trends)
