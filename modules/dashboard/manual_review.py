"""Manual review gate for first-N published videos (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from modules.dashboard.audit_log import AuditEntry, AuditLog
from ytaimbot_ml.schemas import ComplianceReport, ContentPlan


@dataclass(frozen=True)
class ReviewDecision:
    """Manual review decision for one content plan.

    Complexity: O(1).
    """

    trend_id: str
    decision: str  # "approve" | "reject"
    reason: str


class ManualReviewCLI:
    """Interactive human-in-the-loop publish gate.

    Strategy
    --------
    - First ``manual_quota`` decisions require human approval.
    - After quota is reached, decisions auto-approve (unless explicitly disabled).
    - All decisions are persisted to ``AuditLog``.

    Complexity
    ----------
    review(): O(n) due to reading decision count from JSONL log.

    Examples
    --------
    >>> gate = ManualReviewCLI(AuditLog(path="data/audit/test.jsonl"), input_fn=lambda _: "a", output_fn=lambda _: None)
    >>> gate.manual_quota >= 1
    True
    """

    def __init__(
        self,
        audit_log: AuditLog,
        manual_quota: int = 50,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
        auto_approve_after_quota: bool = True,
        operator: str = "human",
    ) -> None:
        self._audit_log = audit_log
        self._manual_quota = manual_quota
        self._input_fn = input_fn
        self._output_fn = output_fn
        self._auto_after_quota = auto_approve_after_quota
        self._operator = operator

    @property
    def manual_quota(self) -> int:
        """Manual-review quota size. O(1)."""
        return self._manual_quota

    def needs_manual_review(self) -> bool:
        """Return True while logged decisions are below quota. O(n)."""
        return self._audit_log.count_decisions() < self._manual_quota

    def review(
        self,
        plan: ContentPlan,
        report: ComplianceReport,
        run_id: str,
    ) -> ReviewDecision:
        """Review one plan and return approve/reject decision.

        Fail-closed behavior:
        - If compliance report is not ``pass``, always reject.
        - If interactive input is unavailable (EOFError), reject.

        Complexity: O(n)
        """
        if report.decision != "pass":
            decision = ReviewDecision(plan.trend_id, "reject", "compliance_fail")
            self._record(run_id, decision)
            return decision

        if not self.needs_manual_review() and self._auto_after_quota:
            decision = ReviewDecision(plan.trend_id, "approve", "auto_after_quota")
            self._record(run_id, decision)
            return decision

        self._output_fn(f"[ManualReview] trend={plan.trend_id}")
        self._output_fn(f"Title: {plan.title}")
        self._output_fn("Decision? [a]pprove / [r]eject")
        try:
            action = self._prompt_decision()
        except EOFError:
            # Non-interactive environment: fail-closed.
            decision = ReviewDecision(plan.trend_id, "reject", "manual_input_unavailable")
            self._record(run_id, decision)
            return decision

        decision = (
            ReviewDecision(plan.trend_id, "approve", "manual_approved")
            if action == "a"
            else ReviewDecision(plan.trend_id, "reject", "manual_rejected")
        )
        self._record(run_id, decision)
        return decision

    def _prompt_decision(self) -> str:
        """Prompt until valid input is received. O(k) for retries."""
        while True:
            value = self._input_fn("> ").strip().lower()
            if value in {"a", "approve"}:
                return "a"
            if value in {"r", "reject"}:
                return "r"
            self._output_fn("Invalid input. Use 'a' or 'r'.")

    def _record(self, run_id: str, decision: ReviewDecision) -> None:
        """Persist decision to audit log. O(1)."""
        self._audit_log.append(
            AuditEntry(
                run_id=run_id,
                trend_id=decision.trend_id,
                decision=decision.decision,
                reason=decision.reason,
                operator=self._operator,
            )
        )

