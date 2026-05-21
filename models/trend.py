"""Trend domain model and related enums."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TrendCategory(str, Enum):
    """High-level trend categories."""

    ENTERTAINMENT = "Entertainment"
    EDUCATION = "Education"
    TECHNOLOGY = "Technology"
    LIFESTYLE = "Lifestyle"
    GAMING = "Gaming"
    FOOD = "Food"
    FITNESS = "Fitness"
    BEAUTY = "Beauty"
    FINANCE = "Finance"
    NEWS = "News"
    CREATOR = "Creator"
    SHORT_FORM = "Short-Form"
    EMERGING = "Emerging"
    GENERAL = "General"


class GrowthVelocity(str, Enum):
    """Trend growth velocity classification."""

    EXTREME = "Extreme"
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    STAGNANT = "Stagnant"


class CompetitionLevel(str, Enum):
    """Creator competition level for a trend niche."""

    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class SaturationRisk(str, Enum):
    """Market saturation risk for a trend."""

    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


@dataclass
class Trend:
    """Unified trend object consumed by analyzers and exporters."""

    title: str
    category: TrendCategory
    description: str
    source: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    viral_score: int = 0
    confidence_score: int = 0
    growth_velocity: GrowthVelocity = GrowthVelocity.MODERATE
    competition_level: CompetitionLevel = CompetitionLevel.MEDIUM
    saturation_risk: SaturationRisk = SaturationRisk.MEDIUM
    best_platform: str = "YouTube"
    thumbnail_text: str = ""
    hashtags: list[str] = field(default_factory=list)
    hook_ideas: list[str] = field(default_factory=list)
    ai_analysis: str = ""
    creator_insights: list[str] = field(default_factory=list)
    raw_signals: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize trend to a JSON-compatible dictionary."""
        data = asdict(self)
        data["category"] = self.category.value
        data["growth_velocity"] = self.growth_velocity.value
        data["competition_level"] = self.competition_level.value
        data["saturation_risk"] = self.saturation_risk.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trend:
        """Deserialize trend from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data["title"],
            category=TrendCategory(data.get("category", "General")),
            description=data.get("description", ""),
            source=data.get("source", "unknown"),
            viral_score=int(data.get("viral_score", 0)),
            confidence_score=int(data.get("confidence_score", 0)),
            growth_velocity=GrowthVelocity(data.get("growth_velocity", "Moderate")),
            competition_level=CompetitionLevel(
                data.get("competition_level", "Medium")
            ),
            saturation_risk=SaturationRisk(data.get("saturation_risk", "Medium")),
            best_platform=data.get("best_platform", "YouTube"),
            thumbnail_text=data.get("thumbnail_text", ""),
            hashtags=list(data.get("hashtags", [])),
            hook_ideas=list(data.get("hook_ideas", [])),
            ai_analysis=data.get("ai_analysis", ""),
            creator_insights=list(data.get("creator_insights", [])),
            raw_signals=dict(data.get("raw_signals", {})),
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
        )
