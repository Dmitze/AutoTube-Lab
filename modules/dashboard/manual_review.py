"""Phase 4 — ManualReviewCLI: Human-in-the-loop review system.

Roadmap tasks: T-281 through T-293 (EPIC 4.4 Manual Review CLI)

Algorithm
---------
1. Dashboard: Display plan metadata, compliance scores, and similarity results.
2. Interaction: Wait for user input (a = approve, r = reject).
3. Logic: Automatically approve if upload_count >= 50 (T-288).
4. Audit: Append each decision to AuditLog (O(1) write).
"""

from __future__ import annotations

import datetime
import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Literal, Optional

if TYPE_CHECKING:
    from ytaimbot_ml.schemas import ContentPlan, PipelineResult
    from ytaimbot_ml.quality.similarity_gate import SimilarityReport

logger = logging.getLogger(__name__)

from modules.dashboard.audit_log import AuditEntry, AuditLog


class ManualReviewCLI:
    """CLI dashboard for human content review.

    Parameters
    ----------
    audit_log:
        AuditLog instance for persisting decisions.
    upload_threshold:
        Number of manual reviews required before switching to full auto.
    """

    def __init__(
        self,
        audit_log: AuditLog | None = None,
        upload_threshold: int = 50,
        manual_quota: int = 50,
        input_fn=input,
        output_fn=print,
    ) -> None:
        self.audit_log = audit_log or AuditLog()
        self.threshold = manual_quota if manual_quota != 50 else upload_threshold
        self.input_fn = input_fn
        self.output_fn = output_fn

    def review(
        self,
        plan: ContentPlan,
        similarity: SimilarityReport,
        upload_count: int,
        compliance_score: float = 0.0,
    ) -> Literal["approve", "reject"]:
        """Display content and prompt for approval or reject.

        Algorithm: O(1) decision.

        Parameters
        ----------
        plan:
            The content plan to review.
        similarity:
            SimilarityReport with scores and hash.
        upload_count:
            Total videos uploaded so far.
        compliance_score:
            Score from Bayes quality filter.

        Returns
        -------
        Literal["approve", "reject"]
            The decision.
        """
        # Automatic approval after threshold (T-288)
        if upload_count >= self.threshold:
            logger.info("ManualReviewCLI: auto-approving (count=%d)", upload_count)
            self._log_decision(plan, similarity, compliance_score, "ai_agent", "approve")
            return "approve"

        # Display dashboard (T-287)
        self.output_fn("\n" + "=" * 60)
        self.output_fn(f" 📺 CONTENT REVIEW (Upload #{upload_count + 1})")
        self.output_fn("=" * 60)
        self.output_fn(f" Title:      {plan.title}")
        self.output_fn(f" Trend ID:   {plan.trend_id}")
        self.output_fn(f" Keywords:   {', '.join(plan.keywords[:5])}")
        self.output_fn("-" * 60)
        self.output_fn(f" Quality (Bayes): {compliance_score:.2f}")
        sim_score = getattr(similarity, "score", getattr(similarity, "similarity_score", 0.0))
        self.output_fn(f" Similarity:      {sim_score:.2f} ({similarity.decision})")
        self.output_fn(f" Content Hash:    {similarity.content_hash[:16]}...")
        self.output_fn("=" * 60)

        # Interaction (T-286)
        while True:
            choice = ""
            try:
                choice = self.input_fn("\n[A]pprove | [R]eject | [Q]uit: ").lower().strip()
            except EOFError:
                self._log_decision(plan, similarity, compliance_score, "human", "reject", "EOF")
                return "reject"
                
            if choice == "a":
                self._log_decision(plan, similarity, compliance_score, "human", "approve")
                return "approve"
            elif choice == "r":
                reason = ""
                try:
                    reason = self.input_fn("Reason for rejection: ")
                except EOFError:
                    pass
                self._log_decision(plan, similarity, compliance_score, "human", "reject", reason)
                return "reject"
            elif choice == "q":
                logger.info("ManualReviewCLI: user quit")
                raise KeyboardInterrupt()
            else:
                self.output_fn("Invalid choice, please enter 'a', 'r', or 'q'.")

    def _log_decision(
        self,
        plan: ContentPlan,
        similarity: SimilarityReport,
        compliance_score: float,
        operator: Literal["human", "ai_agent"],
        decision: Literal["approve", "reject"],
        reason: str = "",
    ) -> None:
        """Helper to append a decision to the audit log."""
        entry = AuditEntry(
            run_id=plan.trend_id,  # Run ID not available here, so we use trend_id as fallback
            trend_id=plan.trend_id,
            decision=decision,
            reason=reason,
            operator=operator,
        )
        self.audit_log.append(entry)
