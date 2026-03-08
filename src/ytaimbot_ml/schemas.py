"""Data classes for the ytaimbot_ml pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
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


@dataclass
class PipelineResult:
    """Aggregated result of a full pipeline run."""

    run_id: str
    rankings: list[TrendRanking] = field(default_factory=list)
    plans: list[ContentPlan] = field(default_factory=list)
    compliance_reports: list[ComplianceReport] = field(default_factory=list)
    status: str = "pending"  # "ok" | "blocked" | "error"
