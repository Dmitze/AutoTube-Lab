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

_DEFAULT_AUDIT_LOG = Path("data/audit_log.jsonl")


@dataclass
class AuditEntry:
    """Record of a manual or automatic review decision."""
    timestamp: str
    video_id: str
    title: str
    operator: Literal["human", "ai_agent"]
    decision: Literal["approve", "reject"]
    compliance_score: float
    similarity_score: float
    content_hash: str
    reason: str = ""


class AuditLog:
    """Append-only storage for review decisions using JSON Lines format.

    Complexity: O(1) write, O(n) read.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else _DEFAULT_AUDIT_LOG
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: AuditEntry) -> None:
        """Add an entry to the log file.  O(1)."""
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def read_all(self) -> List[AuditEntry]:
        """Read all entries from the log.  O(n)."""
        if not self.path.exists():
            return []
        
        entries = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(AuditEntry(**json.loads(line)))
        return entries


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
    ) -> None:
        self.audit_log = audit_log or AuditLog()
        self.threshold = upload_threshold

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
        print("\n" + "=" * 60)
        print(f" 📺 CONTENT REVIEW (Upload #{upload_count + 1})")
        print("=" * 60)
        print(f" Title:      {plan.title}")
        print(f" Trend ID:   {plan.trend_id}")
        print(f" Keywords:   {', '.join(plan.keywords[:5])}")
        print("-" * 60)
        print(f" Quality (Bayes): {compliance_score:.2f}")
        print(f" Similarity:      {similarity.score:.2f} ({similarity.decision})")
        print(f" Content Hash:    {similarity.content_hash[:16]}...")
        print("=" * 60)

        # Interaction (T-286)
        while True:
            choice = input("\n[A]pprove | [R]eject | [Q]uit: ").lower().strip()
            if choice == "a":
                self._log_decision(plan, similarity, compliance_score, "human", "approve")
                return "approve"
            elif choice == "r":
                reason = input("Reason for rejection: ")
                self._log_decision(plan, similarity, compliance_score, "human", "reject", reason)
                return "reject"
            elif choice == "q":
                logger.info("ManualReviewCLI: user quit")
                raise KeyboardInterrupt()
            else:
                print("Invalid choice, please enter 'a', 'r', or 'q'.")

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
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            video_id=plan.trend_id,  # Use trend_id as temporary ID
            title=plan.title,
            operator=operator,
            decision=decision,
            compliance_score=compliance_score,
            similarity_score=similarity.score,
            content_hash=similarity.content_hash,
            reason=reason,
        )
        self.audit_log.append(entry)
