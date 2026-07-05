"""Phase 4 — Publisher adapters sub-package.

Re-exports publisher adapters and provides factory functions consumed by
``modules.orchestrator.build_youtube_uploader`` and
``modules.orchestrator.build_manual_reviewer``.

Adapters
--------
YouTubeUploadAdapter  : OAuth2 resumable upload to YouTube Data API v3
QuotaGuard            : Token Bucket rate limiter (max_per_day uploads)
ManualReviewPublisher : Wraps ManualReviewCLI as a PublisherAdapter (first 50
                        uploads go to human review; auto-approves thereafter)

Factory
-------
build_youtube_uploader(config) → PublisherAdapter
    Returns YouTubeUploadAdapter configured from env vars.
    Respects YTAIMBOT_DRY_RUN=true (fail-closed for safety).

build_manual_reviewer(config) → PublisherAdapter
    Returns ManualReviewPublisher; used for the first UPLOAD_REVIEW_THRESHOLD
    uploads before auto-approval kicks in.

Safety rules
------------
- YTAIMBOT_DRY_RUN=true  → QuotaGuard.allow() always returns False
- ComplianceReport.decision must be "pass" before any upload attempt
- Unlisted first (24 h) → set to public via scheduled update

Status: ✅ Phase 4, EPIC 4.1 (T-263–T-280) + factory functions added 2026-06-26
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from modules.adapters.base import PublisherAdapter
from modules.adapters.publisher.quota_guard import QuotaExhaustedError, QuotaGuard
from modules.adapters.publisher.youtube_upload import DryRunError, YouTubeUploadAdapter

logger = logging.getLogger(__name__)

__all__ = [
    "YouTubeUploadAdapter",
    "QuotaGuard",
    "QuotaExhaustedError",
    "DryRunError",
    "ManualReviewPublisher",
    "build_youtube_uploader",
    "build_manual_reviewer",
]


# ---------------------------------------------------------------------------
# ManualReviewPublisher — bridges ManualReviewCLI into PublisherAdapter ABC
# ---------------------------------------------------------------------------


class ManualReviewPublisher(PublisherAdapter):
    """Thin adapter that gates every publish attempt through ManualReviewCLI.

    For the first ``upload_threshold`` videos the operator is prompted for
    approval; after that, uploads are auto-approved (T-288).

    Parameters
    ----------
    upload_threshold:
        Number of uploads requiring human review before auto-approval.
        Defaults to ``UPLOAD_REVIEW_THRESHOLD`` env var or 50.
    dry_run:
        When ``True``, ``publish()`` logs the decision but does NOT call the
        real YouTube uploader. Defaults to ``YTAIMBOT_DRY_RUN`` env var.

    Complexity
    ----------
    publish(): O(1) decision path (human I/O dominated in review mode).

    Examples
    --------
    >>> import os; os.environ["YTAIMBOT_DRY_RUN"] = "true"
    >>> pub = ManualReviewPublisher(upload_threshold=0)
    >>> pub.dry_run
    True
    """

    def __init__(
        self,
        upload_threshold: int | None = None,
        dry_run: bool | None = None,
    ) -> None:
        from modules.dashboard.manual_review import AuditLog, ManualReviewCLI  # noqa: PLC0415

        threshold = upload_threshold if upload_threshold is not None else int(
            os.environ.get("UPLOAD_REVIEW_THRESHOLD", "50")
        )
        self._cli = ManualReviewCLI(audit_log=AuditLog(), upload_threshold=threshold)

        if dry_run is not None:
            self.dry_run = dry_run
        else:
            self.dry_run = os.environ.get("YTAIMBOT_DRY_RUN", "true").lower() != "false"

    # PublisherAdapter ABC ---------------------------------------------------

    def publish(self, plan: Any, compliance_report: Any) -> bool:  # type: ignore[override]
        """Gate upload through ManualReviewCLI; return True on approval.

        Parameters
        ----------
        plan:
            ContentPlan approved by the quality filters.
        compliance_report:
            ComplianceReport; ``decision`` must be ``"pass"``.

        Returns
        -------
        bool
            ``True`` if the review decision is ``"approve"`` and
            ``dry_run`` is ``False``.  ``False`` otherwise.

        Examples
        --------
        >>> import os; os.environ["YTAIMBOT_DRY_RUN"] = "true"
        >>> pub = ManualReviewPublisher(upload_threshold=0)
        >>> pub.publish(None, None)
        False
        """
        if self.dry_run:
            logger.info("ManualReviewPublisher: DRY_RUN=true — skipping review prompt")
            return False

        if plan is None or compliance_report is None:
            logger.warning("ManualReviewPublisher: received None plan/report — rejecting")
            return False

        # Build a synthetic SimilarityReport stub so ManualReviewCLI can display it
        from src.ytaimbot_ml.quality.similarity_gate import SimilarityReport  # noqa: PLC0415

        similarity_stub = SimilarityReport(
            decision="pass",
            score=getattr(compliance_report, "similarity_score", 0.0),
            content_hash=getattr(compliance_report, "content_hash", ""),
            matches=[],
        )
        compliance_score = getattr(compliance_report, "score", 0.0)
        upload_count = 0  # will be overridden when storage is wired

        try:
            decision = self._cli.review(
                plan=plan,
                similarity=similarity_stub,
                upload_count=upload_count,
                compliance_score=compliance_score,
            )
            approved = decision == "approve"
            logger.info("ManualReviewPublisher: decision=%s", decision)
            return approved
        except KeyboardInterrupt:
            logger.info("ManualReviewPublisher: operator quit — rejecting")
            return False


# ---------------------------------------------------------------------------
# Factory functions (called by modules/orchestrator.py)
# ---------------------------------------------------------------------------


def build_youtube_uploader(config: dict[str, Any]) -> PublisherAdapter:
    """Build and return a configured YouTubeUploadAdapter.

    Reads the following keys from ``config`` (all fall back to env vars):

    ========================  =============================================
    Key                       Env var / Default
    ========================  =============================================
    YOUTUBE_CLIENT_SECRET_PATH  YOUTUBE_CLIENT_SECRET_PATH / data/client_secret.json
    YOUTUBE_TOKEN_PATH          YOUTUBE_TOKEN_PATH / data/token.json
    YOUTUBE_CATEGORY_ID         YOUTUBE_CATEGORY_ID / "28"
    YOUTUBE_DEFAULT_LANGUAGE    YOUTUBE_DEFAULT_LANGUAGE / "uk"
    MAX_UPLOADS_PER_DAY         MAX_UPLOADS_PER_DAY / 6
    YTAIMBOT_DRY_RUN            YTAIMBOT_DRY_RUN / "true"
    ========================  =============================================

    Parameters
    ----------
    config:
        Application configuration dict from env vars.

    Returns
    -------
    PublisherAdapter
        Ready-to-use YouTubeUploadAdapter.

    Complexity: O(1)

    Examples
    --------
    >>> import os; os.environ["YTAIMBOT_DRY_RUN"] = "true"
    >>> pub = build_youtube_uploader({})
    >>> pub.dry_run
    True
    """
    max_uploads = int(config.get("MAX_UPLOADS_PER_DAY") or os.environ.get("MAX_UPLOADS_PER_DAY", "6"))
    guard = QuotaGuard(max_per_day=max_uploads)

    dry_run_str = config.get("YTAIMBOT_DRY_RUN") or os.environ.get("YTAIMBOT_DRY_RUN", "true")
    dry_run = dry_run_str.lower() != "false"

    adapter = YouTubeUploadAdapter(
        quota_guard=guard,
        client_secret_path=config.get("YOUTUBE_CLIENT_SECRET_PATH"),
        token_path=config.get("YOUTUBE_TOKEN_PATH"),
        category_id=config.get("YOUTUBE_CATEGORY_ID"),
        language=config.get("YOUTUBE_DEFAULT_LANGUAGE"),
        dry_run=dry_run,
    )
    logger.info(
        "build_youtube_uploader: dry_run=%s, max_uploads/day=%d",
        dry_run, max_uploads,
    )
    return adapter


def build_manual_reviewer(config: dict[str, Any]) -> PublisherAdapter:
    """Build and return a configured ManualReviewPublisher.

    Parameters
    ----------
    config:
        Application configuration dict. Reads:
        - ``UPLOAD_REVIEW_THRESHOLD`` (default 50)
        - ``YTAIMBOT_DRY_RUN`` (default "true")

    Returns
    -------
    PublisherAdapter
        Ready-to-use ManualReviewPublisher.

    Complexity: O(1)

    Examples
    --------
    >>> import os; os.environ["YTAIMBOT_DRY_RUN"] = "true"
    >>> pub = build_manual_reviewer({})
    >>> pub.dry_run
    True
    """
    threshold = int(
        config.get("UPLOAD_REVIEW_THRESHOLD")
        or os.environ.get("UPLOAD_REVIEW_THRESHOLD", "50")
    )
    dry_run_str = config.get("YTAIMBOT_DRY_RUN") or os.environ.get("YTAIMBOT_DRY_RUN", "true")
    dry_run = dry_run_str.lower() != "false"

    publisher = ManualReviewPublisher(upload_threshold=threshold, dry_run=dry_run)
    logger.info(
        "build_manual_reviewer: dry_run=%s, review_threshold=%d",
        dry_run, threshold,
    )
    return publisher
