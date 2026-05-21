"""Reddit trending discussions via public JSON or optional PRAW (free API)."""

from __future__ import annotations

from loguru import logger

from config.settings import get_settings
from sources.base import BaseScraper, ScraperResult
from utils.http_client import AsyncHTTPClient


class RedditTrendingScraper(BaseScraper):
    """Scrape Reddit hot posts via public .json or PRAW when credentials are set."""

    source_name = "reddit_trending"

    BASE_URL = "https://www.reddit.com/r/{subreddit}/hot.json"

    SUBREDDIT_CATEGORIES: dict[str, str] = {
        "popular": "General",
        "videos": "Entertainment",
        "TikTokCringe": "Short-Form",
        "YouTube": "Creator",
        "ContentCreation": "Creator",
        "socialmedia": "Creator",
        "TikTok": "Short-Form",
        "Instagram": "Creator",
    }

    async def scrape(self) -> ScraperResult:
        settings = get_settings()
        trends: list = []

        if settings.scraping.reddit_client_id and settings.scraping.reddit_client_secret:
            try:
                trends = await self._scrape_praw(settings)
            except Exception as exc:
                logger.warning(f"PRAW scrape failed, falling back to public JSON: {exc}")

        if not trends:
            trends = await self._scrape_public_json(settings)

        return ScraperResult(source=self.source_name, trends=trends)

    async def _scrape_praw(self, settings) -> list:
        import asyncio

        def _fetch():
            import praw

            reddit = praw.Reddit(
                client_id=settings.scraping.reddit_client_id,
                client_secret=settings.scraping.reddit_client_secret,
                user_agent=settings.scraping.reddit_user_agent,
            )
            collected = []
            for subreddit_name in settings.scraping.reddit_subreddits:
                category = self.SUBREDDIT_CATEGORIES.get(subreddit_name, "General")
                sub = reddit.subreddit(subreddit_name)
                for post in sub.hot(limit=5):
                    if post.stickied:
                        continue
                    collected.append(
                        self._build_trend(
                            title=post.title.strip(),
                            category=category,
                            description=(
                                f"Trending on r/{post.subreddit.display_name} — "
                                f"{post.score:,} upvotes, {post.num_comments:,} comments"
                            ),
                            best_platform="Reddit",
                            raw_signals={
                                "subreddit": str(post.subreddit),
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "upvote_ratio": getattr(post, "upvote_ratio", 0.9),
                                "signal_type": "community_discussion",
                                "praw": True,
                            },
                        )
                    )
            return collected

        return await asyncio.to_thread(_fetch)

    async def _scrape_public_json(self, settings) -> list:
        trends = []
        headers = {"User-Agent": settings.scraping.reddit_user_agent}

        async with AsyncHTTPClient() as client:
            for subreddit in settings.scraping.reddit_subreddits:
                category = self.SUBREDDIT_CATEGORIES.get(subreddit, "General")
                url = self.BASE_URL.format(subreddit=subreddit)

                try:
                    data = await client.get_json(
                        url,
                        params={"limit": 6},
                        headers=headers,
                    )
                    posts = data.get("data", {}).get("children", [])

                    for post in posts[:6]:
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

        return trends
