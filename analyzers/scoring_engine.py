"""Rule-based scoring engine for viral trend signals."""

from __future__ import annotations

import hashlib
import re
from typing import Any

import pandas as pd

from models.trend import (
    Trend,
    GrowthVelocity,
    CompetitionLevel,
    SaturationRisk,
)


class ScoringEngine:
    """
    Betting/trading-style scoring engine for creator trend signals.

    Combines keyword popularity, trend velocity, Reddit engagement,
    YouTube position, Google Trends rank, and TikTok hashtag signals.
    """

    SOURCE_WEIGHTS: dict[str, float] = {
        "google_trends": 1.0,
        "youtube_trending": 0.95,
        "reddit_trending": 0.85,
        "tiktok_discovery": 0.90,
        "ai_creator_trends": 0.80,
        "shorts_reels_niches": 0.88,
        "emerging_creator_topics": 0.92,
    }

    PLATFORM_MULTIPLIERS: dict[str, float] = {
        "TikTok": 1.15,
        "YouTube Shorts": 1.10,
        "Instagram Reels": 1.08,
        "YouTube": 1.0,
        "Multi-Platform": 1.05,
        "Reddit": 0.75,
    }

    SIGNAL_GROWTH: dict[str, float] = {
        "search_spike": 88,
        "hashtag_trend": 82,
        "video_trend": 72,
        "community_discussion": 68,
        "emerging_curated": 91,
        "emerging_news": 86,
        "curated_niche": 76,
        "curated_ai_trend": 74,
        "ai_news": 62,
        "niche_discovery": 70,
        "reddit_shorts": 73,
        "page_heading": 65,
    }

    def score_trends(self, trends: list[Trend]) -> list[Trend]:
        """Score and rank all trends."""
        if not trends:
            return []

        scored = [self._score_single(trend) for trend in trends]
        scored.sort(key=lambda t: (t.viral_score, t.confidence_score), reverse=True)
        return scored

    def _score_single(self, trend: Trend) -> Trend:
        """Apply multi-signal scoring model to a single trend."""
        signals = trend.raw_signals
        source_weight = self.SOURCE_WEIGHTS.get(trend.source, 0.7)
        platform_mult = self.PLATFORM_MULTIPLIERS.get(trend.best_platform, 1.0)

        keyword_pop = self._keyword_popularity(trend.title, signals)
        velocity = self._trend_velocity(signals)
        reddit = self._reddit_signal(signals)
        youtube = self._youtube_signal(signals)
        google = self._google_trends_signal(signals)
        tiktok = self._tiktok_signal(signals)
        cross_source = self._cross_source_boost(signals)

        engagement = self._engagement_score(signals, reddit, keyword_pop)
        growth = self._growth_score(signals, velocity, google, youtube, tiktok)
        competition = self._competition_score(trend, signals)
        saturation = self._saturation_score(trend, signals)
        opportunity = self._opportunity_score(engagement, growth, competition, saturation)

        base_viral = (
            engagement * 0.22
            + growth * 0.28
            + opportunity * 0.25
            + keyword_pop * 0.10
            + reddit * 0.05
            + youtube * 0.05
            + google * 0.05
        )
        viral_score = int(
            min(99, max(10, base_viral * source_weight * platform_mult + cross_source))
        )

        signal_depth = self._signal_depth(signals)
        confidence = int(
            min(
                99,
                max(
                    20,
                    viral_score * 0.55
                    + source_weight * 20
                    + signal_depth * 8
                    + cross_source * 0.5
                    + (15 if signals.get("source_mentions", 1) > 1 else 0),
                ),
            )
        )

        trend.viral_score = viral_score
        trend.confidence_score = confidence
        trend.growth_velocity = self._classify_velocity(growth)
        trend.competition_level = self._classify_competition(competition)
        trend.saturation_risk = self._classify_saturation(saturation)

        trend.raw_signals["scoring"] = {
            "keyword_popularity": round(keyword_pop, 1),
            "trend_velocity": round(velocity, 1),
            "reddit_engagement": round(reddit, 1),
            "youtube_position": round(youtube, 1),
            "google_trends_rank": round(google, 1),
            "tiktok_hashtag": round(tiktok, 1),
            "engagement_potential": round(engagement, 1),
            "growth_score": round(growth, 1),
            "competition_score": round(competition, 1),
            "saturation_score": round(saturation, 1),
            "creator_opportunity_score": round(opportunity, 1),
            "cross_source_boost": round(cross_source, 1),
        }

        return trend

    def _keyword_popularity(self, title: str, signals: dict[str, Any]) -> float:
        """Score title keyword strength and search intent."""
        base = 50.0
        words = [w for w in re.findall(r"\w+", title.lower()) if len(w) > 3]
        base += min(20, len(words) * 4)

        if signals.get("signal_type") == "search_spike":
            base += 18
        rank = signals.get("google_rank")
        if rank is not None:
            base += max(0, 22 - int(rank) * 1.5)

        return min(99, base)

    def _trend_velocity(self, signals: dict[str, Any]) -> float:
        """Estimate raw velocity from signal metadata."""
        signal_type = signals.get("signal_type", "")
        base = self.SIGNAL_GROWTH.get(signal_type, 52.0)

        hint = signals.get("velocity_hint", "").lower()
        hint_boost = {"extreme": 18, "high": 12, "moderate": 6, "low": 0}.get(hint, 0)
        base += hint_boost

        if signals.get("pytrends_growth"):
            base += min(15, float(signals["pytrends_growth"]) * 0.15)

        if signals.get("fallback"):
            base *= 0.88

        return min(99, base)

    def _reddit_signal(self, signals: dict[str, Any]) -> float:
        """Reddit mention strength from score and comments."""
        score = signals.get("score", 0) or 0
        comments = signals.get("num_comments", 0) or 0
        ratio = signals.get("upvote_ratio", 0) or 0

        if not score and not comments:
            return 45.0 if signals.get("signal_type") != "community_discussion" else 55.0

        base = 48.0
        base += min(28, (score / 2000) * 12)
        base += min(18, (comments / 800) * 8)
        base += ratio * 12
        return min(99, base)

    def _youtube_signal(self, signals: dict[str, Any]) -> float:
        """YouTube trending position — earlier entries score higher."""
        position = signals.get("feed_position")
        if position is None:
            return 50.0 if signals.get("signal_type") == "video_trend" else 45.0
        return min(99, max(40, 95 - int(position) * 8))

    def _google_trends_signal(self, signals: dict[str, Any]) -> float:
        """Google Trends RSS rank and optional pytrends growth."""
        rank = signals.get("google_rank")
        if rank is None:
            return 55.0 if signals.get("signal_type") == "search_spike" else 48.0

        base = max(35, 92 - int(rank) * 4)
        if signals.get("traffic"):
            base += min(10, 5)
        return min(99, base)

    def _tiktok_signal(self, signals: dict[str, Any]) -> float:
        """TikTok hashtag / discovery popularity proxy."""
        signal_type = signals.get("signal_type", "")
        type_scores = {
            "hashtag_trend": 82,
            "niche_discovery": 68,
            "page_heading": 58,
        }
        base = type_scores.get(signal_type, 48.0)
        if signals.get("hashtag_views"):
            base += min(15, int(signals["hashtag_views"]) / 1_000_000)
        return min(99, base)

    def _cross_source_boost(self, signals: dict[str, Any]) -> float:
        """Boost trends validated by multiple independent sources."""
        mentions = signals.get("source_mentions", 1)
        if mentions >= 3:
            return 8.0
        if mentions == 2:
            return 4.0
        return 0.0

    def _engagement_score(
        self, signals: dict[str, Any], reddit: float, keyword_pop: float
    ) -> float:
        """Estimate engagement potential from combined signals."""
        base = 52.0
        base += (reddit - 45) * 0.35
        base += (keyword_pop - 50) * 0.25

        if signals.get("signal_type") == "search_spike":
            base += 12
        if signals.get("signal_type") == "emerging_curated":
            base += 10

        return min(99, max(10, base))

    def _growth_score(
        self,
        signals: dict[str, Any],
        velocity: float,
        google: float,
        youtube: float,
        tiktok: float,
    ) -> float:
        """Composite growth score."""
        base = velocity * 0.45 + google * 0.2 + youtube * 0.15 + tiktok * 0.2
        return min(99, max(10, base))

    def _competition_score(self, trend: Trend, signals: dict[str, Any]) -> float:
        """Higher score = more competition (bad for creators)."""
        base = 50.0

        saturated_categories = {"Entertainment", "Beauty", "Gaming", "News"}
        if trend.category.value in saturated_categories:
            base += 18

        if trend.source in ("google_trends", "reddit_trending"):
            base += 12

        if signals.get("signal_type") in ("emerging_curated", "emerging_news"):
            base -= 22

        if signals.get("source_mentions", 1) > 2:
            base += 8  # mainstream cross-validation = more competition

        return max(5, min(95, base))

    def _saturation_score(self, trend: Trend, signals: dict[str, Any]) -> float:
        """Higher score = more saturated market."""
        base = 45.0

        if trend.source == "emerging_creator_topics":
            base -= 18
        if trend.source == "google_trends":
            base += 20
        if signals.get("signal_type") == "curated_niche":
            base += 8
        if signals.get("signal_type") == "emerging_curated":
            base -= 28

        title_hash = int(hashlib.md5(trend.title.encode()).hexdigest()[:4], 16)
        base += (title_hash % 16) - 8

        return max(5, min(95, base))

    def _opportunity_score(
        self,
        engagement: float,
        growth: float,
        competition: float,
        saturation: float,
    ) -> float:
        """Creator opportunity = high engagement/growth, low competition/saturation."""
        return min(
            99,
            max(
                10,
                (engagement * 0.25 + growth * 0.35)
                + ((100 - competition) * 0.20)
                + ((100 - saturation) * 0.20),
            ),
        )

    def _signal_depth(self, signals: dict[str, Any]) -> float:
        """Reward richer signal data with higher confidence."""
        core_keys = {
            k
            for k in signals
            if k not in ("scoring", "merged_sources")
        }
        return min(5, len(core_keys) / 4)

    def _classify_velocity(self, score: float) -> GrowthVelocity:
        if score >= 85:
            return GrowthVelocity.EXTREME
        if score >= 70:
            return GrowthVelocity.HIGH
        if score >= 50:
            return GrowthVelocity.MODERATE
        if score >= 30:
            return GrowthVelocity.LOW
        return GrowthVelocity.STAGNANT

    def _classify_competition(self, score: float) -> CompetitionLevel:
        if score >= 80:
            return CompetitionLevel.VERY_HIGH
        if score >= 65:
            return CompetitionLevel.HIGH
        if score >= 45:
            return CompetitionLevel.MEDIUM
        if score >= 25:
            return CompetitionLevel.LOW
        return CompetitionLevel.VERY_LOW

    def _classify_saturation(self, score: float) -> SaturationRisk:
        if score >= 80:
            return SaturationRisk.VERY_HIGH
        if score >= 65:
            return SaturationRisk.HIGH
        if score >= 45:
            return SaturationRisk.MEDIUM
        if score >= 25:
            return SaturationRisk.LOW
        return SaturationRisk.VERY_LOW

    def generate_analytics_summary(self, trends: list[Trend]) -> dict[str, Any]:
        """Generate dashboard-style analytics summary."""
        if not trends:
            return {"total_trends": 0}

        df = pd.DataFrame([t.to_dict() for t in trends])

        return {
            "total_trends": len(trends),
            "avg_viral_score": round(df["viral_score"].mean(), 1),
            "avg_confidence_score": round(df["confidence_score"].mean(), 1),
            "top_category": df["category"].mode().iloc[0] if len(df) else "N/A",
            "top_platform": df["best_platform"].mode().iloc[0] if len(df) else "N/A",
            "extreme_growth_count": int(
                (df["growth_velocity"] == GrowthVelocity.EXTREME.value).sum()
            ),
            "low_competition_count": int(
                df["competition_level"].isin(
                    [CompetitionLevel.LOW.value, CompetitionLevel.VERY_LOW.value]
                ).sum()
            ),
            "engine": "rule_based",
        }
