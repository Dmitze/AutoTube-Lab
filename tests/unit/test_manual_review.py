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
    """ManualReviewCLI returns 'approve' when user inputs 'a'."""
    log = AuditLog(tmp_path / "audit.jsonl")
    gate = ManualReviewCLI(
        audit_log=log,
        input_fn=lambda _: "a",
        output_fn=lambda _: None,
    )
    decision = gate.review(_plan(), _pass_report(), upload_count=0)
    assert decision == "approve"
    
    entries = log.read_all()
    assert len(entries) == 1
    assert entries[0].decision == "approve"
    assert entries[0].operator == "human"


def test_manual_review_reject_with_input(tmp_path: Path) -> None:
    """ManualReviewCLI returns 'reject' when user inputs 'r'."""
    log = AuditLog(tmp_path / "audit.jsonl")
    
    inputs = iter(["r", "Too controversial"])
    gate = ManualReviewCLI(
        audit_log=log,
        input_fn=lambda _: next(inputs),
        output_fn=lambda _: None,
    )
    decision = gate.review(_plan(), _pass_report(), upload_count=0)
    assert decision == "reject"
    
    entries = log.read_all()
    assert entries[0].decision == "reject"
    assert entries[0].reason == "Too controversial"


def test_manual_review_invalid_then_valid(tmp_path: Path) -> None:
    """ManualReviewCLI ignores invalid input until 'a', 'r', or 'q' is given."""
    log = AuditLog(tmp_path / "audit.jsonl")
    
    inputs = iter(["x", "y", "", "a"])
    gate = ManualReviewCLI(
        audit_log=log,
        input_fn=lambda _: next(inputs),
        output_fn=lambda _: None,
    )
    decision = gate.review(_plan(), _pass_report(), upload_count=0)
    assert decision == "approve"


def test_manual_review_eof_is_fail_closed_reject(tmp_path: Path) -> None:
    """If stdin is closed (EOFError), the gate fails closed (rejects)."""
    log = AuditLog(tmp_path / "audit.jsonl")
    
    def _raise(*args):
        raise EOFError("No input")
        
    gate = ManualReviewCLI(audit_log=log, input_fn=_raise, output_fn=lambda _: None)
    decision = gate.review(_plan(), _pass_report(), upload_count=0)
    
    assert decision == "reject"
    entries = log.read_all()
    assert entries[0].reason == "EOF"


def test_manual_review_auto_approve_after_quota(tmp_path: Path) -> None:
    """ManualReviewCLI auto-approves once upload_count >= threshold."""
    log = AuditLog(tmp_path / "audit.jsonl")
    gate = ManualReviewCLI(
        audit_log=log,
        manual_quota=1,
        input_fn=lambda _: "r",
        output_fn=lambda _: None,
    )
    decision = gate.review(_plan(), _pass_report(), upload_count=1)
    assert decision == "approve"


def test_pipeline_publish_blocked_by_manual_reject(tmp_path: Path) -> None:
    """ManualReviewPublisher honors manual rejection."""
    from modules.adapters.publisher import ManualReviewPublisher
    pub = ManualReviewPublisher(upload_threshold=1, dry_run=False)
    # Patch the _cli inside pub
    pub._cli.input_fn = lambda _: "r"
    pub._cli.output_fn = lambda _: None
    
    assert pub.publish(_plan(), _pass_report()) is False


def test_pipeline_publish_allowed_by_manual_approve(tmp_path: Path) -> None:
    """ManualReviewPublisher proceeds when manual reviewer approves."""
    from modules.adapters.publisher import ManualReviewPublisher
    pub = ManualReviewPublisher(upload_threshold=1, dry_run=False)
    # Patch the _cli inside pub
    pub._cli.input_fn = lambda _: "a"
    pub._cli.output_fn = lambda _: None
    
    assert pub.publish(_plan(), _pass_report()) is True

