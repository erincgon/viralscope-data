"""Reddit trending discussions via public JSON endpoints."""

from __future__ import annotations

from config.settings import get_settings
from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class RedditTrendingScraper(BaseScraper):
    """Scrape Reddit hot posts via public .json endpoints (respects rate limits)."""

    source_name = "reddit_trending"

    BASE_URL = "https://www.reddit.com/r/{subreddit}/hot.json"

    SUBREDDIT_CATEGORIES: dict[str, str] = {
        "popular": "General",
        "videos": "Entertainment",
        "TikTokCringe": "Short-Form",
        "YouTube": "Creator",
        "ContentCreation": "Creator",
        "socialmedia": "Creator",
    }

    async def scrape(self) -> ScraperResult:
        settings = get_settings()
        subreddits = settings.scraping.reddit_subreddits
        trends = []

        headers = {"User-Agent": "ViralScopeEngine/1.0 (trend research bot)"}

        async with AsyncHTTPClient() as client:
            for subreddit in subreddits:
                category = self.SUBREDDIT_CATEGORIES.get(subreddit, "General")
                url = self.BASE_URL.format(subreddit=subreddit)

                try:
                    data = await client.get_json(
                        url,
                        params={"limit": 5},
                        headers=headers,
                    )
                    posts = data.get("data", {}).get("children", [])

                    for post in posts[:5]:
                        post_data = post.get("data", {})
                        title = post_data.get("title", "").strip()
                        if not title or post_data.get("stickied"):
                            continue

                        score = post_data.get("score", 0)
                        num_comments = post_data.get("num_comments", 0)
                        subreddit_name = post_data.get("subreddit", subreddit)

                        trends.append(
                            self._build_trend(
                                title=title,
                                category=category,
                                description=(
                                    f"Trending on r/{subreddit_name} with "
                                    f"{score:,} upvotes and {num_comments:,} comments"
                                ),
                                best_platform="Reddit",
                                raw_signals={
                                    "subreddit": subreddit_name,
                                    "score": score,
                                    "num_comments": num_comments,
                                    "upvote_ratio": post_data.get("upvote_ratio", 0),
                                    "signal_type": "community_discussion",
                                },
                            )
                        )
                except Exception:
                    continue

        return ScraperResult(source=self.source_name, trends=trends)
