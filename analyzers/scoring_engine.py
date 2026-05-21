"""Custom scoring engine for viral trend signals."""

from __future__ import annotations

import hashlib
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

    Computes viral probability, saturation risk, engagement potential,
    competition level, and creator opportunity score.
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

    def score_trends(self, trends: list[Trend]) -> list[Trend]:
        """Score and rank all trends."""
        if not trends:
            return []

        scored = [self._score_single(trend) for trend in trends]
        scored.sort(key=lambda t: t.viral_score, reverse=True)
        return scored

    def _score_single(self, trend: Trend) -> Trend:
        """Apply scoring model to a single trend."""
        signals = trend.raw_signals
        source_weight = self.SOURCE_WEIGHTS.get(trend.source, 0.7)
        platform_mult = self.PLATFORM_MULTIPLIERS.get(trend.best_platform, 1.0)

        engagement = self._engagement_score(signals)
        growth = self._growth_score(signals)
        competition = self._competition_score(trend, signals)
        saturation = self._saturation_score(trend, signals)
        opportunity = self._opportunity_score(engagement, growth, competition, saturation)

        viral_score = int(
            min(99, max(10, (engagement * 0.35 + growth * 0.35 + opportunity * 0.30)
                * source_weight * platform_mult))
        )
        confidence = int(
            min(99, max(20, viral_score * 0.7 + source_weight * 25 + self._signal_depth(signals) * 5))
        )

        trend.viral_score = viral_score
        trend.confidence_score = confidence
        trend.growth_velocity = self._classify_velocity(growth)
        trend.competition_level = self._classify_competition(competition)
        trend.saturation_risk = self._classify_saturation(saturation)

        trend.raw_signals["scoring"] = {
            "engagement_potential": round(engagement, 1),
            "growth_score": round(growth, 1),
            "competition_score": round(competition, 1),
            "saturation_score": round(saturation, 1),
            "creator_opportunity_score": round(opportunity, 1),
        }

        return trend

    def _engagement_score(self, signals: dict[str, Any]) -> float:
        """Estimate engagement potential from raw signals."""
        base = 55.0

        score = signals.get("score", 0)
        comments = signals.get("num_comments", 0)
        upvote_ratio = signals.get("upvote_ratio", 0)

        if score:
            base += min(25, (score / 1000) * 5)
        if comments:
            base += min(15, (comments / 500) * 5)
        if upvote_ratio:
            base += upvote_ratio * 10

        velocity_hint = signals.get("velocity_hint", "")
        velocity_boost = {"extreme": 20, "high": 12, "moderate": 5}.get(velocity_hint, 0)
        base += velocity_boost

        if signals.get("signal_type") == "search_spike":
            base += 15
        if signals.get("signal_type") == "emerging_curated":
            base += 10

        return min(99, base)

    def _growth_score(self, signals: dict[str, Any]) -> float:
        """Estimate growth velocity score."""
        base = 50.0

        signal_type = signals.get("signal_type", "")
        growth_map = {
            "search_spike": 85,
            "hashtag_trend": 80,
            "video_trend": 70,
            "community_discussion": 65,
            "emerging_curated": 90,
            "emerging_news": 88,
            "curated_niche": 75,
            "ai_news": 60,
        }
        base = growth_map.get(signal_type, base)

        if signals.get("fallback"):
            base *= 0.85

        return min(99, base)

    def _competition_score(self, trend: Trend, signals: dict[str, Any]) -> float:
        """Higher score = more competition (bad for creators)."""
        base = 50.0

        saturated_categories = {"Entertainment", "Beauty", "Gaming", "News"}
        if trend.category.value in saturated_categories:
            base += 20

        if trend.source in ("google_trends", "reddit_trending"):
            base += 15  # Mainstream sources = higher competition

        if signals.get("signal_type") in ("emerging_curated", "emerging_news"):
            base -= 25

        return max(5, min(95, base))

    def _saturation_score(self, trend: Trend, signals: dict[str, Any]) -> float:
        """Higher score = more saturated market."""
        base = 45.0

        if trend.source == "emerging_creator_topics":
            base -= 20
        if trend.source == "google_trends":
            base += 25
        if signals.get("signal_type") == "curated_niche":
            base += 10
        if signals.get("signal_type") == "emerging_curated":
            base -= 30

        # Deterministic variance based on title hash
        title_hash = int(hashlib.md5(trend.title.encode()).hexdigest()[:4], 16)
        base += (title_hash % 20) - 10

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
        return min(5, len(signals) / 3)

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
        }
