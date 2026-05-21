"""OpenAI-powered trend analysis and content generation."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger
from openai import AsyncOpenAI, OpenAIError

from config.settings import get_settings
from models.trend import Trend


class AIAnalyzer:
    """Enrich trends with AI-generated insights using OpenAI."""

    SYSTEM_PROMPT = """You are ViralScope AI, an expert viral content strategist for creators.
Analyze trends and generate actionable creator intelligence.
Respond ONLY with valid JSON matching the requested schema.
Be specific, creative, and data-driven. Focus on short-form and long-form creator opportunities."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: AsyncOpenAI | None = None

        if self.settings.ai.enabled and self.settings.ai.api_key:
            self._client = AsyncOpenAI(api_key=self.settings.ai.api_key)

    @property
    def is_enabled(self) -> bool:
        return self._client is not None

    async def enrich_trends(self, trends: list[Trend]) -> list[Trend]:
        """Apply AI analysis to all trends in batches."""
        if not self.is_enabled:
            logger.warning("AI analysis disabled — skipping enrichment")
            return [self._apply_fallback(t) for t in trends]

        batch_size = self.settings.ai.batch_size
        enriched: list[Trend] = []

        for i in range(0, len(trends), batch_size):
            batch = trends[i : i + batch_size]
            tasks = [self._analyze_single(trend) for trend in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for trend, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"AI analysis failed for '{trend.title}': {result}")
                    enriched.append(self._apply_fallback(trend))
                else:
                    enriched.append(result)

        return enriched

    async def _analyze_single(self, trend: Trend) -> Trend:
        """Run OpenAI analysis on a single trend."""
        if not self._client:
            return self._apply_fallback(trend)

        prompt = self._build_prompt(trend)

        try:
            response = await self._client.chat.completions.create(
                model=self.settings.ai.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.settings.ai.max_tokens,
                temperature=self.settings.ai.temperature,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            return self._merge_ai_data(trend, data)

        except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
            logger.error(f"OpenAI API error for '{trend.title}': {exc}")
            return self._apply_fallback(trend)

    def _build_prompt(self, trend: Trend) -> str:
        return f"""Analyze this viral trend signal for content creators:

Title: {trend.title}
Category: {trend.category.value}
Description: {trend.description}
Platform: {trend.best_platform}
Viral Score: {trend.viral_score}
Growth Velocity: {trend.growth_velocity.value}
Competition: {trend.competition_level.value}
Saturation Risk: {trend.saturation_risk.value}
Source: {trend.source}

Return JSON with this exact schema:
{{
  "viral_potential_summary": "2-3 sentence analysis of viral potential",
  "hook_ideas": ["hook 1", "hook 2", "hook 3"],
  "viral_titles": ["title 1", "title 2", "title 3"],
  "thumbnail_text": "BOLD THUMBNAIL TEXT",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "creator_insights": ["insight 1", "insight 2", "insight 3"],
  "best_posting_strategy": "1-2 sentence posting strategy"
}}"""

    def _merge_ai_data(self, trend: Trend, data: dict[str, Any]) -> Trend:
        """Merge AI response into trend object."""
        trend.ai_analysis = data.get("viral_potential_summary", "")
        trend.hook_ideas = data.get("hook_ideas", [])[:5]
        trend.thumbnail_text = data.get("thumbnail_text", "")[:60]
        trend.hashtags = data.get("hashtags", [])[:10]
        trend.creator_insights = data.get("creator_insights", [])[:5]

        viral_titles = data.get("viral_titles", [])
        if viral_titles and not trend.thumbnail_text:
            trend.thumbnail_text = viral_titles[0][:60]

        posting = data.get("best_posting_strategy", "")
        if posting:
            trend.creator_insights.append(f"Strategy: {posting}")

        return trend

    def _apply_fallback(self, trend: Trend) -> Trend:
        """Generate rule-based fallback when AI is unavailable."""
        title_words = trend.title.split()[:4]
        short_title = " ".join(title_words)

        trend.ai_analysis = (
            f"'{trend.title}' shows {trend.growth_velocity.value.lower()} growth potential "
            f"on {trend.best_platform} with {trend.competition_level.value.lower()} competition. "
            f"Saturation risk is {trend.saturation_risk.value.lower()} — "
            f"{'act fast' if trend.growth_velocity.value in ('Extreme', 'High') else 'monitor closely'}."
        )
        trend.hook_ideas = [
            f"Nobody is talking about {short_title} — here's why you should",
            f"I tried {short_title} for 7 days — the results shocked me",
            f"The {short_title} trend creators don't want you to know about",
        ]
        trend.thumbnail_text = short_title.upper()[:40]
        trend.hashtags = [
            f"#{word.replace(' ', '')}" for word in title_words[:3]
        ] + ["#viral", "#trending", f"#{trend.category.value.replace(' ', '')}"]
        trend.creator_insights = [
            f"Best platform: {trend.best_platform}",
            f"Optimal timing: Post within 48h while velocity is {trend.growth_velocity.value}",
            f"Differentiation: Add unique POV to stand out in {trend.competition_level.value} competition niche",
        ]
        return trend
