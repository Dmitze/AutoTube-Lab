"""Shared fixtures for E2E pipeline tests (Phase 9)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from modules.adapters.base import LLMAdapter, PublisherAdapter, TrendSourceAdapter, TTSAdapter
from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource
from modules.dashboard.audit_log import AuditLog
from modules.dashboard.manual_review import ManualReviewCLI
from modules.orchestrator import Pipeline
from ytaimbot_ml.schemas import ComplianceReport, ContentPlan, TrendSignal


class FakePublisher(PublisherAdapter):
    """Publisher test-double that records publish calls."""

    def __init__(self) -> None:
        self.published: list[tuple[ContentPlan, ComplianceReport]] = []

    def publish(self, plan: ContentPlan, compliance_report: ComplianceReport) -> bool:
        self.published.append((plan, compliance_report))
        return True


class FakeLLM(LLMAdapter):
    """LLM test-double returning deterministic section text."""

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self._fail:
            raise RuntimeError("mock llm failure")
        return " ".join(["word"] * 120)


class FakeTTS(TTSAdapter):
    """TTS test-double writing placeholder MP3 bytes."""

    def speak(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-mp3")
        return output_path


class FailingTTS(TTSAdapter):
    """TTS test-double that always fails (to validate fail-open behavior)."""

    def speak(self, text: str, output_path: Path) -> Path:
        raise RuntimeError("mock tts failure")


class FailingTrendSource(TrendSourceAdapter):
    """Trend source that raises to test pipeline error path."""

    def fetch(self) -> list[TrendSignal]:
        raise RuntimeError("source unavailable")


@pytest.fixture
def full_mock_pipeline(tmp_path: Path) -> Callable[..., Pipeline]:
    """Build fully mocked Pipeline instance for E2E scenarios.

    Returns a factory to customize dry-run mode, LLM behavior, and trend source.
    """

    def _factory(
        *,
        dry_run: bool = False,
        llm_fail: bool = False,
        source: TrendSourceAdapter | None = None,
        with_manual_review: bool = False,
        tts: TTSAdapter | None = None,
    ) -> Pipeline:
        publisher = FakePublisher()
        manual_reviewer = None
        if with_manual_review:
            manual_reviewer = ManualReviewCLI(
                audit_log=AuditLog(path=tmp_path / "audit" / "review.jsonl"),
                input_fn=lambda _: "a",
                output_fn=lambda _: None,
                manual_quota=50,
            )
        return Pipeline(
            trend_source=source or SyntheticTrendSource(seed=42),
            storage=InMemoryStorage(),
            publisher=publisher,
            manual_reviewer=manual_reviewer,
            llm=FakeLLM(fail=llm_fail),
            tts=FakeTTS() if tts is None else tts,
            dry_run=dry_run,
            seed=42,
            audio_dir=tmp_path / "audio",
        )

    return _factory

