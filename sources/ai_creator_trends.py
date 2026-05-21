"""AI and tech creator trend signals from public sources."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class AICreatorTrendsScraper(BaseScraper):
    """Aggregate AI creator trends from public RSS feeds and tech news."""

    source_name = "ai_creator_trends"

    RSS_FEEDS: list[tuple[str, str]] = [
        ("https://hnrss.org/newest?q=AI+video+OR+AI+content+OR+ChatGPT", "Technology"),
        ("https://hnrss.org/newest?q=creator+economy+OR+YouTube+Shorts", "Creator"),
        ("https://hnrss.org/newest?q=Midjourney+OR+Runway+OR+Sora", "Technology"),
    ]

    CURATED_SIGNALS: list[tuple[str, str, str]] = [
        (
            "AI Avatar Channels",
            "Faceless AI-generated presenter channels gaining traction",
            "YouTube",
        ),
        (
            "ChatGPT Workflow Tutorials",
            "Step-by-step AI productivity content for creators",
            "TikTok",
        ),
        (
            "AI Thumbnail A/B Testing",
            "Creators using AI to optimize click-through rates",
            "YouTube",
        ),
        (
            "Synthetic Voice Narration",
            "AI voiceover replacing traditional narration in shorts",
            "Short-Form",
        ),
        (
            "Prompt Engineering for Creators",
            "Teaching audiences how to use AI tools effectively",
            "Education",
        ),
    ]

    async def scrape(self) -> ScraperResult:
        trends = []

        async with AsyncHTTPClient() as client:
            for feed_url, category in self.RSS_FEEDS:
                try:
                    xml_text = await client.get(feed_url)
                    root = ET.fromstring(xml_text)

                    for item in root.findall(".//item")[:4]:
                        title_el = item.find("title")
                        desc_el = item.find("description")
                        if title_el is None or not title_el.text:
                            continue

                        trends.append(
                            self._build_trend(
                                title=title_el.text.strip()[:120],
                                category=category,
                                description=(
                                    desc_el.text.strip()[:200]
                                    if desc_el is not None and desc_el.text
                                    else "AI creator economy signal"
                                ),
                                best_platform="Multi-Platform",
                                raw_signals={"signal_type": "ai_news", "feed": feed_url},
                            )
                        )
                except Exception:
                    continue

        for title, desc, platform in self.CURATED_SIGNALS:
            trends.append(
                self._build_trend(
                    title=title,
                    category="Creator",
                    description=desc,
                    best_platform=platform,
                    raw_signals={"signal_type": "curated_ai_trend"},
                )
            )

        return ScraperResult(source=self.source_name, trends=trends[:15])
