"""Creator economy and tech trend signals from public RSS (no AI APIs)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class AICreatorTrendsScraper(BaseScraper):
    """Aggregate creator-economy trends from public RSS feeds (HN, curated)."""

    source_name = "ai_creator_trends"

    RSS_FEEDS: list[tuple[str, str]] = [
        ("https://hnrss.org/newest?q=AI+video+OR+AI+content+OR+faceless+channel", "Creator"),
        ("https://hnrss.org/newest?q=creator+economy+OR+YouTube+Shorts+OR+monetization", "Creator"),
        ("https://hnrss.org/newest?q=Midjourney+OR+Runway+OR+Sora+OR+CapCut", "Technology"),
        ("https://hnrss.org/newest?q=UGC+OR+brand+deal+OR+sponsorship+creator", "Creator"),
    ]

    CURATED_SIGNALS: list[tuple[str, str, str, str]] = [
        (
            "AI Avatar Channels",
            "Faceless AI-generated presenter channels gaining traction",
            "YouTube Shorts",
            "extreme",
        ),
        (
            "ChatGPT Workflow Tutorials",
            "Step-by-step AI productivity content for creators",
            "TikTok",
            "high",
        ),
        (
            "AI Thumbnail A/B Testing",
            "Creators using automation to optimize click-through rates",
            "YouTube",
            "high",
        ),
        (
            "Synthetic Voice Narration",
            "AI voiceover replacing traditional narration in shorts",
            "Short-Form",
            "high",
        ),
        (
            "Prompt Engineering for Creators",
            "Teaching audiences how to use AI tools effectively",
            "Education",
            "moderate",
        ),
        (
            "UGC Brand Deal Negotiation",
            "Creators sharing sponsorship rate transparency",
            "TikTok",
            "high",
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
                                    else "Creator economy trend signal"
                                ),
                                best_platform="Multi-Platform",
                                raw_signals={
                                    "signal_type": "ai_news",
                                    "feed": feed_url,
                                    "velocity_hint": "moderate",
                                },
                            )
                        )
                except Exception:
                    continue

        for title, desc, platform, velocity in self.CURATED_SIGNALS:
            trends.append(
                self._build_trend(
                    title=title,
                    category="Creator",
                    description=desc,
                    best_platform=platform,
                    raw_signals={
                        "signal_type": "curated_ai_trend",
                        "velocity_hint": velocity,
                    },
                )
            )

        return ScraperResult(source=self.source_name, trends=trends[:18])
