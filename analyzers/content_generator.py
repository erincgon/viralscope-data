"""Rule-based trend intelligence and content generation (no AI APIs)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from models.trend import (
    Trend,
    GrowthVelocity,
    CompetitionLevel,
    SaturationRisk,
)


class ContentGenerator:
    """
    Template-driven hooks, hashtags, thumbnails, and creator insights.

    Uses keyword extraction, engagement patterns, and viral content formulas.
    """

    HOOK_TEMPLATES: tuple[str, ...] = (
        "POV: {keyword} changed everything",
        "Nobody expected {keyword} to explode",
        "This {keyword} trend is everywhere",
        "I tried {keyword} for 7 days — here's what happened",
        "Why {keyword} is blowing up right now",
        "The {keyword} trend creators don't want you to miss",
        "Stop scrolling — {keyword} is the next viral wave",
    )

    THUMBNAIL_TEMPLATES: tuple[str, ...] = (
        "THIS IS BLOWING UP",
        "NEW VIRAL TREND",
        "EVERYONE IS TRYING THIS",
        "YOU NEED TO SEE THIS",
        "TREND ALERT",
        "GOING VIRAL NOW",
        "{keyword_upper}",
    )

    INSIGHT_TEMPLATES: dict[str, tuple[str, ...]] = {
        "velocity": (
            "Growth velocity is {velocity} — publish within 48h to ride the wave",
            "Momentum is {velocity}; batch 3–5 pieces while interest spikes",
        ),
        "competition": (
            "Competition is {competition} — differentiate with a unique POV or niche angle",
            "Stand out in a {competition} competition field with authentic storytelling",
        ),
        "saturation": (
            "Saturation risk is {saturation} — {action}",
            "Market saturation: {saturation}. {action}",
        ),
        "platform": (
            "Primary platform signal: {platform} — optimize format for that algorithm",
            "Cross-post to {platform} first, then repurpose to Shorts/Reels within 24h",
        ),
    }

    CATEGORY_HASHTAGS: dict[str, list[str]] = {
        "Creator": ["#ContentCreator", "#CreatorEconomy", "#GoViral"],
        "Short-Form": ["#Shorts", "#Reels", "#FYP", "#Viral"],
        "Technology": ["#TechTok", "#Innovation", "#TechTrend"],
        "Education": ["#LearnOnTikTok", "#EduTok", "#HowTo"],
        "Entertainment": ["#Entertainment", "#ViralVideo", "#Trending"],
        "Lifestyle": ["#Lifestyle", "#DayInMyLife", "#Aesthetic"],
        "Finance": ["#MoneyTok", "#FinanceTips", "#WealthBuilding"],
        "Fitness": ["#FitTok", "#Workout", "#FitnessMotivation"],
        "Food": ["#FoodTok", "#Recipe", "#Cooking"],
        "Beauty": ["#BeautyTok", "#GRWM", "#Makeup"],
        "Gaming": ["#Gaming", "#Gamer", "#Gameplay"],
        "Emerging": ["#EmergingTrend", "#EarlyMover", "#NicheContent"],
    }

    def enrich_trends(self, trends: list[Trend]) -> list[Trend]:
        """Apply rule-based enrichment to all trends."""
        return [self._enrich_single(trend) for trend in trends]

    def _enrich_single(self, trend: Trend) -> Trend:
        keyword = self._extract_keyword(trend.title)
        seed = int(hashlib.md5(trend.title.encode()).hexdigest()[:8], 16)

        trend.hook_ideas = self._generate_hooks(keyword, trend, seed)
        trend.thumbnail_text = self._generate_thumbnail(keyword, trend, seed)
        trend.hashtags = self._generate_hashtags(keyword, trend, seed)
        trend.creator_insights = self._generate_insights(trend)
        trend.ai_analysis = self._generate_analysis_summary(trend, keyword)
        return trend

    def _extract_keyword(self, title: str) -> str:
        """Extract a short viral keyword phrase from the title."""
        cleaned = re.sub(r"[^\w\s-]", "", title)
        words = [w for w in cleaned.split() if len(w) > 2][:4]
        if not words:
            return title[:40].strip() or "this trend"
        return " ".join(words[:3])

    def _generate_hooks(self, keyword: str, trend: Trend, seed: int) -> list[str]:
        hooks: list[str] = []
        templates = list(self.HOOK_TEMPLATES)
        start = seed % len(templates)

        for i in range(3):
            template = templates[(start + i) % len(templates)]
            hooks.append(template.format(keyword=keyword))

        if trend.growth_velocity == GrowthVelocity.EXTREME:
            hooks[0] = f"🚨 {hooks[0]}"
        return hooks[:5]

    def _generate_thumbnail(self, keyword: str, trend: Trend, seed: int) -> str:
        template = self.THUMBNAIL_TEMPLATES[seed % len(self.THUMBNAIL_TEMPLATES)]
        text = template.format(keyword_upper=keyword.upper()[:35])
        if trend.viral_score >= 90:
            return text if "{" not in text else "THIS IS BLOWING UP"
        return text[:60]

    def _generate_hashtags(self, keyword: str, trend: Trend, seed: int) -> list[str]:
        tags: list[str] = []
        for word in keyword.split()[:3]:
            tag = "#" + re.sub(r"[^a-zA-Z0-9]", "", word)
            if len(tag) > 2:
                tags.append(tag)

        category_tags = self.CATEGORY_HASHTAGS.get(
            trend.category.value, ["#Viral", "#Trending", "#FYP"]
        )
        tags.extend(category_tags)

        platform_tag = {
            "TikTok": "#TikTok",
            "YouTube Shorts": "#YouTubeShorts",
            "Instagram Reels": "#Reels",
            "YouTube": "#YouTube",
        }.get(trend.best_platform, "#ContentCreator")

        tags.append(platform_tag)
        tags.append("#ViralScope")

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for tag in tags:
            key = tag.lower()
            if key not in seen:
                seen.add(key)
                unique.append(tag)

        return unique[:10]

    def _generate_insights(self, trend: Trend) -> list[str]:
        saturation_action = (
            "move fast before the niche fills up"
            if trend.saturation_risk in (SaturationRisk.LOW, SaturationRisk.VERY_LOW)
            else "find a micro-niche sub-angle to avoid saturation"
        )

        insights = [
            self.INSIGHT_TEMPLATES["velocity"][0].format(
                velocity=trend.growth_velocity.value
            ),
            self.INSIGHT_TEMPLATES["competition"][0].format(
                competition=trend.competition_level.value
            ),
            self.INSIGHT_TEMPLATES["saturation"][0].format(
                saturation=trend.saturation_risk.value,
                action=saturation_action,
            ),
            self.INSIGHT_TEMPLATES["platform"][0].format(platform=trend.best_platform),
        ]

        scoring = trend.raw_signals.get("scoring", {})
        opportunity = scoring.get("creator_opportunity_score", 0)
        if opportunity >= 75:
            insights.append(
                f"Opportunity score {opportunity:.0f}/99 — high-confidence creator signal"
            )
        elif trend.confidence_score >= 80:
            insights.append(
                f"Confidence {trend.confidence_score}% — strong multi-signal validation"
            )

        return insights[:5]

    def _generate_analysis_summary(self, trend: Trend, keyword: str) -> str:
        """Rule-based trend intelligence summary (stored in ai_analysis for schema compat)."""
        signals = trend.raw_signals
        source_count = signals.get("source_mentions", 1)

        parts = [
            f"'{keyword}' shows {trend.growth_velocity.value.lower()} growth on "
            f"{trend.best_platform} with viral score {trend.viral_score}/99.",
            f"Competition is {trend.competition_level.value.lower()} and saturation risk "
            f"is {trend.saturation_risk.value.lower()}.",
        ]

        if source_count > 1:
            parts.append(
                f"Cross-validated across {source_count} independent trend signals."
            )

        if trend.growth_velocity in (GrowthVelocity.EXTREME, GrowthVelocity.HIGH):
            parts.append("Act within 48–72 hours to capture peak algorithmic lift.")
        else:
            parts.append("Monitor momentum and test 2–3 content angles before scaling.")

        return " ".join(parts)
