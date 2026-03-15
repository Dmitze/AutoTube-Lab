"""E2E full pipeline tests with mocked external integrations.

Roadmap: T-581 (Phase 9 E2E Testing)
Seed: 42

These tests validate end-to-end orchestration behavior using synthetic trends
and fake adapters only (no network, no real YouTube/LLM/TTS calls).
"""

from __future__ import annotations

from pathlib import Path

from modules.adapters.base import LLMAdapter, PublisherAdapter, TTSAdapter
from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource
from modules.orchestrator import Pipeline
from ytaimbot_ml.schemas import ComplianceReport, ContentPlan


class _FakePublisher(PublisherAdapter):
    """Publisher test double that records publish attempts."""

    def __init__(self) -> None:
        self.published: list[tuple[ContentPlan, ComplianceReport]] = []

    def publish(self, plan: ContentPlan, compliance_report: ComplianceReport) -> bool:
        self.published.append((plan, compliance_report))
        return True


class _FakeLLM(LLMAdapter):
    """LLM test double returning deterministic text."""

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self._fail:
            raise RuntimeError("mock llm timeout")
        # Keep output long enough for ScriptGenerator's 500-word minimum.
        return " ".join(["word"] * 120)


class _FakeTTS(TTSAdapter):
    """TTS test double that writes a placeholder MP3 path."""

    def speak(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-mp3")
        return output_path


def test_full_pipeline_with_all_stages(tmp_path: Path) -> None:
    """Pipeline completes with mocked LLM/TTS/publisher and performs publishes."""
    source = SyntheticTrendSource(seed=42)
    storage = InMemoryStorage()
    publisher = _FakePublisher()
    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
        publisher=publisher,
        llm=_FakeLLM(),
        tts=_FakeTTS(),
        dry_run=False,
        seed=42,
        audio_dir=tmp_path / "audio",
    )

    result = pipeline.run(run_id="e2e-full-001")

    assert result.status == "ok"
    assert len(result.rankings) >= 5
    assert len(result.plans) == 5
    assert len(result.compliance_reports) == 5
    assert len(result.scripts) >= 1
    assert len(publisher.published) >= 1


def test_full_pipeline_fail_closed(tmp_path: Path) -> None:
    """If compliance gate fails, publish stage must not be called."""
    source = SyntheticTrendSource(seed=42)
    storage = InMemoryStorage()
    publisher = _FakePublisher()
    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
        publisher=publisher,
        llm=_FakeLLM(),
        tts=_FakeTTS(),
        dry_run=False,
        seed=42,
        audio_dir=tmp_path / "audio",
    )

    # Force all plans to fail compliance to test fail-closed publish behavior.
    pipeline._gate_all = lambda plans: [  # type: ignore[method-assign]
        ComplianceReport(
            content_hash=f"hash-{i}",
            similarity_score=1.0,
            bayes_p_bad=0.99,
            decision="fail",
            reasons=["forced test fail"],
        )
        for i, _ in enumerate(plans)
    ]

    result = pipeline.run(run_id="e2e-full-fail-closed")

    assert result.status == "ok"
    assert all(report.decision == "fail" for report in result.compliance_reports)
    assert len(publisher.published) == 0


def test_full_pipeline_recovery_from_llm_error(tmp_path: Path) -> None:
    """LLM generation failures are isolated; pipeline still completes fail-safe."""
    source = SyntheticTrendSource(seed=42)
    storage = InMemoryStorage()
    publisher = _FakePublisher()
    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
        publisher=publisher,
        llm=_FakeLLM(fail=True),
        tts=_FakeTTS(),
        dry_run=False,
        seed=42,
        audio_dir=tmp_path / "audio",
    )

    result = pipeline.run(run_id="e2e-full-llm-error")

    # Current orchestrator design: script errors are logged and skipped, run stays OK.
    assert result.status == "ok"
    assert len(result.scripts) == 0
    # No script -> no TTS artifact; publish may still happen for approved plans.
    assert len(result.plans) == 5
