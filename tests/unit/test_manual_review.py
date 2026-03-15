"""Unit tests for ManualReviewCLI and AuditLog integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.adapters.synthetic import InMemoryStorage, StubPublisher, SyntheticTrendSource
from modules.dashboard.audit_log import AuditEntry, AuditLog
from modules.dashboard.manual_review import ManualReviewCLI
from modules.orchestrator import Pipeline
from ytaimbot_ml.schemas import ComplianceReport, ContentPlan


def _pass_report() -> ComplianceReport:
    return ComplianceReport(
        content_hash="abc",
        similarity_score=0.01,
        bayes_p_bad=0.01,
        decision="pass",
        reasons=[],
    )


def _plan() -> ContentPlan:
    return ContentPlan(
        trend_id="trend_1",
        title="Test title",
        outline=["a", "b"],
        keywords=["k1", "k2"],
    )


def test_audit_log_append_and_read(tmp_path: Path) -> None:
    """AuditLog writes and reads JSONL entries."""
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append(AuditEntry(run_id="r1", trend_id="t1", decision="approve", reason="ok"))
    rows = log.read_all()
    assert len(rows) == 1
    assert rows[0].decision == "approve"


def test_manual_review_approve_with_input(tmp_path: Path) -> None:
    """Interactive approve should log and return approve decision."""
    answers = iter(["a"])
    log = AuditLog(tmp_path / "audit.jsonl")
    gate = ManualReviewCLI(
        audit_log=log,
        input_fn=lambda _: next(answers),
        output_fn=lambda _: None,
    )
    decision = gate.review(_plan(), _pass_report(), run_id="r1")
    assert decision.decision == "approve"
    assert log.read_all()[0].reason == "manual_approved"


def test_manual_review_reject_with_input(tmp_path: Path) -> None:
    """Interactive reject should block publish path."""
    answers = iter(["r"])
    log = AuditLog(tmp_path / "audit.jsonl")
    gate = ManualReviewCLI(
        audit_log=log,
        input_fn=lambda _: next(answers),
        output_fn=lambda _: None,
    )
    decision = gate.review(_plan(), _pass_report(), run_id="r1")
    assert decision.decision == "reject"
    assert log.read_all()[0].reason == "manual_rejected"


def test_manual_review_invalid_then_valid(tmp_path: Path) -> None:
    """Invalid user input should reprompt until valid choice."""
    answers = iter(["x", "approve"])
    outputs: list[str] = []
    gate = ManualReviewCLI(
        audit_log=AuditLog(tmp_path / "audit.jsonl"),
        input_fn=lambda _: next(answers),
        output_fn=outputs.append,
    )
    decision = gate.review(_plan(), _pass_report(), run_id="r1")
    assert decision.decision == "approve"
    assert any("Invalid input" in msg for msg in outputs)


def test_manual_review_eof_is_fail_closed_reject(tmp_path: Path) -> None:
    """EOFError (non-interactive) must reject to stay fail-closed."""
    def _raise(_: str) -> str:
        raise EOFError

    log = AuditLog(tmp_path / "audit.jsonl")
    gate = ManualReviewCLI(audit_log=log, input_fn=_raise, output_fn=lambda _: None)
    decision = gate.review(_plan(), _pass_report(), run_id="r1")
    assert decision.decision == "reject"
    assert decision.reason == "manual_input_unavailable"


def test_manual_review_auto_approve_after_quota(tmp_path: Path) -> None:
    """After quota is reached, decisions auto-approve."""
    log = AuditLog(tmp_path / "audit.jsonl")
    # Pre-fill one decision to satisfy quota=1.
    log.append(AuditEntry(run_id="r0", trend_id="t0", decision="approve", reason="ok"))
    gate = ManualReviewCLI(
        audit_log=log,
        manual_quota=1,
        input_fn=lambda _: "r",
        output_fn=lambda _: None,
    )
    decision = gate.review(_plan(), _pass_report(), run_id="r2")
    assert decision.decision == "approve"
    assert decision.reason == "auto_after_quota"


def test_pipeline_publish_blocked_by_manual_reject(tmp_path: Path) -> None:
    """Pipeline publish stage must honor manual rejection."""
    publisher = StubPublisher()
    gate = ManualReviewCLI(
        audit_log=AuditLog(tmp_path / "audit.jsonl"),
        input_fn=lambda _: "r",
        output_fn=lambda _: None,
    )
    pipeline = Pipeline(
        trend_source=SyntheticTrendSource(seed=42),
        storage=InMemoryStorage(),
        publisher=publisher,
        manual_reviewer=gate,
        dry_run=False,
        seed=42,
    )
    pipeline._publish_approved([_plan()], [_pass_report()], run_id="run-x")
    assert len(publisher.published) == 0


def test_pipeline_publish_allowed_by_manual_approve(tmp_path: Path) -> None:
    """Pipeline publish stage proceeds when manual reviewer approves."""
    publisher = StubPublisher()
    gate = ManualReviewCLI(
        audit_log=AuditLog(tmp_path / "audit.jsonl"),
        input_fn=lambda _: "a",
        output_fn=lambda _: None,
    )
    pipeline = Pipeline(
        trend_source=SyntheticTrendSource(seed=42),
        storage=InMemoryStorage(),
        publisher=publisher,
        manual_reviewer=gate,
        dry_run=False,
        seed=42,
    )
    pipeline._publish_approved([_plan()], [_pass_report()], run_id="run-y")
    assert len(publisher.published) == 1

