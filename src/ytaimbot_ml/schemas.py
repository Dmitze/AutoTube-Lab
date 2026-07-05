"""Data classes for the ytaimbot_ml pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

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
class VideoAsset:
    """Assembled video file produced by VideoAssembler.

    Parameters
    ----------
    plan_id:
        trend_id of the source ContentPlan.
    video_path:
        Absolute path to the MP4 file.
    thumbnail_path:
        Absolute path to the 1280×720 PNG thumbnail.
    subtitle_path:
        Absolute path to the SRT subtitle file (or empty string if none).
    duration_seconds:
        Video duration in seconds (0.0 if not yet assembled).
    thumbnail_score:
        ThumbnailScorer.score().total value in [0, 1].

    Complexity
    ----------
    O(1) — pure data container
    """

    plan_id: str
    video_path: str = ""
    thumbnail_path: str = ""
    subtitle_path: str = ""
    duration_seconds: float = 0.0
    thumbnail_score: float = 0.0

    @property
    def ready(self) -> bool:
        """True if both video and thumbnail files are specified."""
        return bool(self.video_path and self.thumbnail_path)


# ---------------------------------------------------------------------------
# Phase 5 schemas — Publishing + Analytics
# ---------------------------------------------------------------------------


class PrivacyStatus:
    """YouTube privacy status constants.

    Values align with the YouTube Data API v3 ``status.privacyStatus`` field.

    Examples
    --------
    >>> PrivacyStatus.UNLISTED
    'unlisted'
    >>> PrivacyStatus.PUBLIC
    'public'
    """

    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


@dataclass
class UploadResult:
    """Result of a successful YouTube video upload.

    Parameters
    ----------
    plan_id:
        trend_id of the source ContentPlan.
    video_id:
        YouTube video ID (e.g. ``"dQw4w9WgXcQ"``).
    url:
        Full watch URL (``https://youtu.be/{video_id}``).
    privacy_status:
        Current privacy status (``PrivacyStatus.*``).
    quota_used:
        YouTube API quota units consumed by this upload.
    upload_time:
        UTC timestamp when the upload completed.

    Complexity
    ----------
    O(1) — pure data container

    Examples
    --------
    >>> r = UploadResult(plan_id="t1", video_id="abc123", url="https://youtu.be/abc123")
    >>> r.quota_used
    1600
    """

    plan_id: str
    video_id: str = ""
    url: str = ""
    privacy_status: str = PrivacyStatus.UNLISTED
    quota_used: int = 1600
    upload_time: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def success(self) -> bool:
        """True if a video_id was assigned."""
        return bool(self.video_id)


@dataclass
class ChannelStats:
    """Aggregated YouTube channel metrics for a single video.

    Parameters
    ----------
    video_id:
        YouTube video ID.
    views:
        Total view count.
    ctr:
        Click-through rate (impressions → clicks) in [0, 1].
    retention_30s:
        Percentage of viewers who watched past 30 seconds, in [0, 1].
    likes:
        Total like count.
    comments:
        Total comment count.
    fetched_at:
        UTC timestamp of the most recent analytics fetch.

    Complexity
    ----------
    O(1) — pure data container

    Examples
    --------
    >>> s = ChannelStats(video_id="abc", views=1000, ctr=0.07, retention_30s=0.72)
    >>> s.ctr_pct
    7.0
    """

    video_id: str
    views: int = 0
    ctr: float = 0.0
    retention_30s: float = 0.0
    likes: int = 0
    comments: int = 0
    fetched_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def ctr_pct(self) -> float:
        """CTR as a percentage (e.g. 0.07 → 7.0)."""
        return round(self.ctr * 100, 2)

    @property
    def meets_targets(self) -> bool:
        """True if CTR ≥ 6% and 30s retention ≥ 70% (pipeline KPIs)."""
        return self.ctr >= 0.06 and self.retention_30s >= 0.70


@dataclass
class MetricsSnapshot:
    """Historical snapshot of video metrics (time-series).

    Parameters
    ----------
    video_id:
        YouTube video ID.
    views:
        Total view count.
    ctr:
        Click-through rate in [0, 1].
    retention_30s:
        Percentage of viewers who watched past 30 seconds, in [0, 1].
    rpm:
        Revenue per 1,000 views (approximate).
    watch_time_h:
        Total watch time in hours.
    collected_at:
        UTC timestamp when the metrics were collected.
    """

    video_id: str
    views: int = 0
    ctr: float = 0.0
    retention_30s: float = 0.0
    rpm: float = 0.0
    watch_time_h: float = 0.0
    collected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class ABTestResult:
    """Result of a statistical A/B test between two variants."""
    video_id: str
    variant_type: str
    winner: str = "inconclusive"
    p_value: float = 1.0
    significant: bool = False


@dataclass
class DriftReport:
    """Result of a distribution drift detection (KS-test)."""
    statistic: float
    p_value: float
    drift_detected: bool
    action: str = "continue"


@dataclass
class ContentState:
    """State vector for the PPO policy optimizer."""
    features: np.ndarray


@dataclass
class ContentAction:
    """Action vector for the PPO policy optimizer."""
    params: dict


@dataclass
class PipelineResult:
    """Aggregated result of a full pipeline run.

    Parameters
    ----------
    run_id:
        Unique identifier for this pipeline run.
    script_path:
        Path to the generated script file (set after Stage 7 SCRIPT). T-151
    audio_path:
        Path to the synthesized audio file (set after Stage 8 AUDIO). T-151

    Complexity
    ----------
    O(1) — pure data container

    Examples
    --------
    >>> r = PipelineResult(run_id="run_001")
    >>> r.status
    'pending'
    >>> r.script_path is None
    True
    """

    run_id: str
    rankings: list[TrendRanking] = field(default_factory=list)
    plans: list[ContentPlan] = field(default_factory=list)
    compliance_reports: list[ComplianceReport] = field(default_factory=list)
    scripts: list[Script] = field(default_factory=list)
    videos: list[VideoAsset] = field(default_factory=list)
    uploads: list[UploadResult] = field(default_factory=list)
    status: str = "pending"  # "ok" | "blocked" | "error"
    # T-151: Phase 2 integration fields
    script_path: str | None = None   # path to generated .txt script file
    audio_path: str | None = None    # path to synthesized .mp3 audio file
    # T-304: Phase 4 publishing fields
    video_id: str | None = None          # YouTube video_id after upload
    published_at: str | None = None      # ISO-8601 timestamp of publication
    audit_entry: dict | None = None      # AuditLog entry for this run


@dataclass(order=True)
class UploadJob:
    """Represents a video upload task in the queue."""
    scheduled_at: float  # Unix timestamp
    plan_id: str = field(compare=False)
    video_path: str = field(compare=False)
    thumbnail_path: str | None = field(default=None, compare=False)
    title: str = field(default="", compare=False)
    description: str = field(default="", compare=False)
    tags: list[str] = field(default_factory=list, compare=False)
