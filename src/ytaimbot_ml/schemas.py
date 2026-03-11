"""Data classes for the ytaimbot_ml pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np


@dataclass
class TrendSignal:
    """Raw trend signal ingested from a source."""

    trend_id: str
    keyword: str
    raw_score: float
    source: str
    timestamp: str  # ISO-8601


@dataclass
class TrendFeatures:
    """Numeric feature vector derived from a TrendSignal."""

    trend_id: str
    features: np.ndarray


@dataclass
class TrendRanking:
    """Final ranked score assigned to a trend."""

    trend_id: str
    score: float


@dataclass
class ContentPlan:
    """Content plan generated for a trend."""

    trend_id: str
    title: str
    outline: list[str]
    keywords: list[str]


@dataclass
class ComplianceReport:
    """Result of the compliance/quality gate."""

    content_hash: str
    similarity_score: float
    bayes_p_bad: float
    decision: str  # "pass" | "fail"
    reasons: list[str]


# ---------------------------------------------------------------------------
# Phase 2 schemas — Script generation
# ---------------------------------------------------------------------------


@dataclass
class ScriptSection:
    """One section of a video script (hook / intro / body / cta).

    Parameters
    ----------
    name:
        Section identifier: "hook", "intro", "body_1"–"body_3", "cta".
    text:
        Generated or template-filled text for this section.
    keywords:
        Keywords injected into this section.
    word_count:
        Actual word count after generation.
    token_estimate:
        Estimated token usage (approx word_count × 1.3).
    """

    name: str
    text: str
    keywords: list[str] = field(default_factory=list)
    word_count: int = 0
    token_estimate: int = 0

    def __post_init__(self) -> None:
        if self.word_count == 0:
            self.word_count = len(self.text.split())
        if self.token_estimate == 0:
            self.token_estimate = int(self.word_count * 1.3)


@dataclass
class Script:
    """Full video script produced by ScriptGenerator.

    Parameters
    ----------
    plan_id:
        trend_id of the source ContentPlan.
    sections:
        Ordered list of ScriptSection objects.
    language:
        ISO 639-1 language code (e.g. "uk", "en").
    created_at:
        UTC timestamp of generation.

    Properties
    ----------
    total_words:
        Sum of word counts across all sections.
    total_tokens:
        Sum of token estimates across all sections.

    Complexity
    ----------
    O(n) where n = number of sections.

    Examples
    --------
    >>> s = Script(plan_id="t1", sections=[], language="uk")
    >>> s.total_words
    0
    """

    plan_id: str
    sections: list[ScriptSection] = field(default_factory=list)
    language: str = "uk"
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def total_words(self) -> int:
        """Sum of word counts across all sections. O(n)."""
        return sum(s.word_count for s in self.sections)

    @property
    def total_tokens(self) -> int:
        """Sum of token estimates. O(n)."""
        return sum(s.token_estimate for s in self.sections)

    @property
    def full_text(self) -> str:
        """All sections joined with double newline. O(n)."""
        return "\n\n".join(s.text for s in self.sections)


@dataclass
class PipelineResult:
    """Aggregated result of a full pipeline run."""

    run_id: str
    rankings: list[TrendRanking] = field(default_factory=list)
    plans: list[ContentPlan] = field(default_factory=list)
    compliance_reports: list[ComplianceReport] = field(default_factory=list)
    scripts: list[Script] = field(default_factory=list)
    status: str = "pending"  # "ok" | "blocked" | "error"

