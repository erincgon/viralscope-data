"""Emerging creator topics from cross-platform public signals."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class EmergingCreatorTopicsScraper(BaseScraper):
    """Detect emerging creator topics before mainstream saturation."""

    source_name = "emerging_creator_topics"

    EMERGING_TOPICS: list[dict[str, str]] = [
        {
            "title": "Faceless Finance Channels",
            "description": "Anonymous personal finance content with screen recordings",
            "category": "Finance",
            "platform": "YouTube",
        },
        {
            "title": "Niche Language Learning",
            "description": "Ultra-specific language tips (business Spanish, anime Japanese)",
            "category": "Education",
            "platform": "TikTok",
        },
        {
            "title": "Retro Tech Restoration",
            "description": "Restoring vintage electronics with satisfying process videos",
            "category": "Technology",
            "platform": "YouTube Shorts",
        },
        {
            "title": "Micro SaaS Building",
            "description": "Building tiny software products in public",
            "category": "Technology",
            "platform": "YouTube",
        },
        {
            "title": "Solo Travel on Budget",
            "description": "Affordable solo travel vlogs targeting Gen Z wanderlust",
            "category": "Lifestyle",
            "platform": "Instagram Reels",
        },
        {
            "title": "Plant Parent Community",
            "description": "Indoor gardening tips with community-driven content",
            "category": "Lifestyle",
            "platform": "TikTok",
        },
        {
            "title": "ADHD Productivity Systems",
            "description": "Neurodivergent-friendly productivity frameworks",
            "category": "Education",
            "platform": "YouTube",
        },
        {
            "title": "Vintage Fashion Hauls",
            "description": "Thrift and vintage fashion with sustainability angle",
            "category": "Beauty",
            "platform": "Instagram Reels",
        },
    ]

    RSS_FEEDS = [
        "https://hnrss.org/newest?q=emerging+creator+OR+new+niche+OR+untapped",
        "https://hnrss.org/newest?q=faceless+channel+OR+passive+income+creator",
    ]

    async def scrape(self) -> ScraperResult:
        trends = []

        async with AsyncHTTPClient() as client:
            for feed_url in self.RSS_FEEDS:
                try:
                    xml_text = await client.get(feed_url)
                    root = ET.fromstring(xml_text)

                    for item in root.findall(".//item")[:3]:
                        title_el = item.find("title")
                        if title_el is None or not title_el.text:
                            continue

                        trends.append(
                            self._build_trend(
                                title=title_el.text.strip()[:100],
                                category="Emerging",
                                description="Early-stage creator opportunity signal",
                                best_platform="Multi-Platform",
                                raw_signals={
                                    "signal_type": "emerging_news",
                                    "feed": feed_url,
                                },
                            )
                        )
                except Exception:
                    continue

        for topic in self.EMERGING_TOPICS:
            trends.append(
                self._build_trend(
                    title=topic["title"],
                    category=topic["category"],
                    description=topic["description"],
                    best_platform=topic["platform"],
                    raw_signals={"signal_type": "emerging_curated"},
                )
            )

        return ScraperResult(source=self.source_name, trends=trends)
