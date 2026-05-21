"""Trend scraping sources."""

from sources.base import BaseScraper, ScraperResult
from sources.google_trends import GoogleTrendsScraper
from sources.youtube_trending import YouTubeTrendingScraper
from sources.reddit_trending import RedditTrendingScraper
from sources.tiktok_discovery import TikTokDiscoveryScraper
from sources.ai_creator_trends import AICreatorTrendsScraper
from sources.shorts_reels_niches import ShortsReelsNichesScraper
from sources.emerging_creator_topics import EmergingCreatorTopicsScraper

__all__ = [
    "BaseScraper",
    "ScraperResult",
    "GoogleTrendsScraper",
    "YouTubeTrendingScraper",
    "RedditTrendingScraper",
    "TikTokDiscoveryScraper",
    "AICreatorTrendsScraper",
    "ShortsReelsNichesScraper",
    "EmergingCreatorTopicsScraper",
    "ALL_SCRAPERS",
]

ALL_SCRAPERS: list[type[BaseScraper]] = [
    GoogleTrendsScraper,
    YouTubeTrendingScraper,
    RedditTrendingScraper,
    TikTokDiscoveryScraper,
    AICreatorTrendsScraper,
    ShortsReelsNichesScraper,
    EmergingCreatorTopicsScraper,
]
