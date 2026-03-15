"""Extended E2E scenario matrix for pipeline orchestration (Phase 9)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from modules.adapters.base import TTSAdapter
from modules.adapters.tts.free_tier_chain import FreeTierTTSChain
from modules.dashboard.audit_log import AuditLog
from ytaimbot_ml.quality.evidence import EvidenceArtifact, EvidenceChain
from ytaimbot_ml.schemas import ComplianceReport


def test_e2e_happy_path_publishes(full_mock_pipeline) -> None:
    """Happy path: dry_run=False with passing gate publishes at least one plan."""
    pipeline = full_mock_pipeline(dry_run=False)
    result = pipeline.run("e2e-happy-path")
    assert result.status == "ok"
    assert len(result.plans) == 5
    assert len(pipeline._publisher.published) >= 1  # noqa: SLF001


def test_e2e_dry_run_skips_publish(full_mock_pipeline) -> None:
    """Dry run should never invoke publisher."""
    pipeline = full_mock_pipeline(dry_run=True)
    result = pipeline.run("e2e-dry-run")
    assert result.status == "ok"
    assert len(result.plans) == 5
    assert len(pipeline._publisher.published) == 0  # noqa: SLF001


def test_e2e_bayes_fail_blocks_publish(full_mock_pipeline) -> None:
    """If all compliance reports fail, publish stage is fail-closed."""
    pipeline = full_mock_pipeline(dry_run=False)
    pipeline._gate_all = lambda plans: [  # type: ignore[method-assign]
        ComplianceReport(
            content_hash=f"forced-{i}",
            similarity_score=1.0,
            bayes_p_bad=0.99,
            decision="fail",
            reasons=["forced gate fail"],
        )
        for i, _ in enumerate(plans)
    ]
    result = pipeline.run("e2e-bayes-fail")
    assert result.status == "ok"
    assert all(r.decision == "fail" for r in result.compliance_reports)
    assert len(pipeline._publisher.published) == 0  # noqa: SLF001


def test_e2e_similarity_like_fail_blocks_publish(full_mock_pipeline) -> None:
    """Duplicate/similarity-style fail should block publish in fail-closed stage."""
    pipeline = full_mock_pipeline(dry_run=False)
    pipeline._gate_all = lambda plans: [  # type: ignore[method-assign]
        ComplianceReport(
            content_hash=f"dup-{i}",
            similarity_score=0.96,
            bayes_p_bad=0.05,
            decision="fail",
            reasons=["similarity above threshold"],
        )
        for i, _ in enumerate(plans)
    ]
    result = pipeline.run("e2e-similarity-fail")
    assert result.status == "ok"
    assert all(r.decision == "fail" for r in result.compliance_reports)
    assert any("similarity" in " ".join(r.reasons).lower() for r in result.compliance_reports)
    assert len(pipeline._publisher.published) == 0  # noqa: SLF001


def test_e2e_llm_down_degrades_gracefully(full_mock_pipeline) -> None:
    """LLM failure is isolated; pipeline completes with no scripts."""
    pipeline = full_mock_pipeline(dry_run=False, llm_fail=True)
    result = pipeline.run("e2e-llm-down")
    assert result.status == "ok"
    assert len(result.scripts) == 0
    assert len(result.plans) == 5


def test_e2e_tts_down_pipeline_continues(full_mock_pipeline, tmp_path: Path) -> None:
    """TTS failures are isolated per script and do not fail the full run."""
    class _FailingTTS(TTSAdapter):
        def speak(self, text: str, output_path: Path) -> Path:
            raise RuntimeError("mock tts failure")

    pipeline = full_mock_pipeline(dry_run=False, tts=_FailingTTS())
    result = pipeline.run("e2e-tts-down")
    assert result.status == "ok"
    assert len(result.scripts) >= 1
    run_audio_dir = tmp_path / "audio" / "e2e-tts-down"
    assert len(list(run_audio_dir.glob("*.mp3"))) == 0


def test_e2e_quota_exceeded_tts_fallback_works(
    full_mock_pipeline,
    tmp_path: Path,
) -> None:
    """When primary TTS quota is exhausted, chain falls back to next adapter."""

    class _QuotaTracker:
        def check_available(self, service: str, amount: int) -> bool:
            return service != "svc-exhausted"

        def remaining(self, service: str) -> int:
            return 0 if service == "svc-exhausted" else -1

        def summary(self) -> dict[str, dict]:
            return {}

    class _NeverCalledAdapter(TTSAdapter):
        def speak(self, text: str, output_path: Path) -> Path:
            raise RuntimeError("should not be called when quota is exhausted")

    class _FallbackAdapter(TTSAdapter):
        def speak(self, text: str, output_path: Path) -> Path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fallback-mp3")
            return output_path

    chain = FreeTierTTSChain(
        chain=[("svc-exhausted", _NeverCalledAdapter()), ("edge-tts", _FallbackAdapter())],
        tracker=_QuotaTracker(),  # type: ignore[arg-type]
    )
    pipeline = full_mock_pipeline(dry_run=False, tts=chain)
    result = pipeline.run("e2e-tts-quota-fallback")

    assert result.status == "ok"
    assert len(result.scripts) >= 1
    audio_files = list((tmp_path / "audio" / "e2e-tts-quota-fallback").glob("*.mp3"))
    assert len(audio_files) >= 1


def test_e2e_source_failure_sets_error(full_mock_pipeline) -> None:
    """Source hard failure should set pipeline status='error'."""
    class _FailingTrendSource:
        def fetch(self):
            raise RuntimeError("source unavailable")

    pipeline = full_mock_pipeline(dry_run=False, source=_FailingTrendSource())
    result = pipeline.run("e2e-source-fail")
    assert result.status == "error"


def test_e2e_manual_review_writes_audit_log(full_mock_pipeline, tmp_path: Path) -> None:
    """Manual-review mode should create append-only audit entries."""
    pipeline = full_mock_pipeline(dry_run=False, with_manual_review=True)
    result = pipeline.run("e2e-manual-review")
    assert result.status == "ok"
    log = AuditLog(path=tmp_path / "audit" / "review.jsonl")
    # fixture uses same tmp_path root; log should contain decisions for pass attempts
    assert log.path.exists()
    assert len(log.read_all()) >= 1


def test_e2e_evidence_chain_verifies_after_run(full_mock_pipeline) -> None:
    """Evidence chain built from approved publish attempts remains valid."""
    pipeline = full_mock_pipeline(dry_run=False)
    result = pipeline.run("e2e-evidence-chain")
    assert result.status == "ok"

    scripts_by_plan = {script.plan_id: script.full_text for script in result.scripts}
    chain = EvidenceChain()

    for plan, report in zip(result.plans, result.compliance_reports):
        if report.decision != "pass":
            continue
        text = scripts_by_plan.get(plan.trend_id, plan.title)
        artifact = EvidenceArtifact.create(
            video_id=f"{result.run_id}:{plan.trend_id}",
            script_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            similarity_score=report.similarity_score,
            bayes_score=report.bayes_p_bad,
            operator_decision="approve",
            previous_hash=chain.last_hash,
        )
        chain.append(artifact)

    assert len(chain) >= 1
    assert chain.verify_chain() is True

