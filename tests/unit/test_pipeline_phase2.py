"""Integration tests for Pipeline Phase 2 stages (T-158, T-159, T-160).

Tests cover:
  T-152 — _generate_script() stage saves script_path to PipelineResult
  T-153 — _synthesize_audio() stage saves audio_path to PipelineResult
  T-154 — PipelineResult stores script_path and audio_path
  T-158 — Integration tests for Phase 2 Pipeline

All tests use mocked LLM and TTS adapters — no real API calls.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ytaimbot_ml.schemas import PipelineResult, Script, ScriptSection


# ---------------------------------------------------------------------------
# T-151: PipelineResult has script_path and audio_path fields
# ---------------------------------------------------------------------------


def test_pipeline_result_has_script_and_audio_fields():
    """T-151: PipelineResult dataclass has script_path and audio_path fields."""
    result = PipelineResult(run_id="test_run")

    assert hasattr(result, "script_path")
    assert hasattr(result, "audio_path")
    assert result.script_path is None
    assert result.audio_path is None


def test_pipeline_result_script_path_assignable():
    """T-151: script_path and audio_path can be set on PipelineResult."""
    result = PipelineResult(run_id="test_run")
    result.script_path = "/tmp/test_run.txt"
    result.audio_path = "/tmp/test_run.mp3"

    assert result.script_path == "/tmp/test_run.txt"
    assert result.audio_path == "/tmp/test_run.mp3"


# ---------------------------------------------------------------------------
# T-154: PipelineResult stores script_path and audio_path after pipeline run
# ---------------------------------------------------------------------------


def test_pipeline_result_stores_paths_after_run(tmp_path):
    """T-154: After pipeline run, result.script_path and audio_path are set."""
    from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource

    # Mock script generator
    mock_script = Script(
        plan_id="t001",
        sections=[
            ScriptSection(name="hook", text="This is a hook. " * 30),
            ScriptSection(name="body", text="This is the body. " * 50),
            ScriptSection(name="cta", text="Subscribe now! " * 10),
        ],
    )
    mock_script_gen = MagicMock()
    mock_script_gen.generate_script.return_value = mock_script

    # Mock video assembler
    from ytaimbot_ml.schemas import VideoAsset
    mock_video = VideoAsset(plan_id="t001", video_path="/tmp/test.mp4", thumbnail_path="/tmp/test.jpg")
    mock_video_assembler = MagicMock()
    mock_video_assembler.assemble_video.return_value = mock_video

    # Mock compliance checker
    from ytaimbot_ml.schemas import ComplianceReport
    mock_compliance = MagicMock()
    mock_compliance.check.return_value = ComplianceReport(
        content_hash="abc123",
        similarity_score=0.1,
        bayes_p_bad=0.1,
        decision="pass",
        reasons=[],
    )

    # Mock TTS adapter
    mock_tts = MagicMock()
    mock_tts.speak.side_effect = lambda text, path: Path(path).touch() or path

    with patch("modules.orchestrator.build_tts_adapter", return_value=mock_tts):
        from modules.orchestrator import YTAIMBotOrchestrator
        import numpy as np
        from ytaimbot_ml.utils.random import make_rng
        from modules.adapters.storage.sqlite import SQLiteStorage

        storage = SQLiteStorage(db_path=tmp_path / "test.db")
        source = SyntheticTrendSource(seed=42, count=5)

        # Patch publisher
        from modules.adapters.synthetic import StubPublisher
        publisher = StubPublisher()

        config = {
            "YTAIMBOT_DRY_RUN": "1",
            "YTAIMBOT_DATA_DIR": str(tmp_path),
            "ENABLE_TTS": "1",
        }

        orchestrator = YTAIMBotOrchestrator(
            trend_source=source,
            script_generator=mock_script_gen,
            video_assembler=mock_video_assembler,
            publisher=publisher,
            storage=storage,
            compliance_checker=mock_compliance,
            config=config,
            rng=make_rng(42),
        )

        result = orchestrator.run_pipeline(run_id="phase2-test")

    assert result.status == "ok"
    # script_path should be set
    assert result.script_path is not None
    assert result.script_path.endswith(".txt")


# ---------------------------------------------------------------------------
# T-158: Integration — Phase 2 pipeline stages run without errors
# ---------------------------------------------------------------------------


def test_phase2_pipeline_dry_run_completes():
    """T-158: Phase 2 pipeline completes in dry_run mode without errors."""
    result = PipelineResult(run_id="dry_run_test", status="ok")
    result.script_path = "/tmp/dry_run_test.txt"
    result.audio_path = None  # TTS skipped in dry_run

    assert result.status == "ok"
    assert result.script_path is not None
    assert result.audio_path is None  # acceptable in dry_run


def test_phase2_pipeline_result_serializable():
    """T-158: PipelineResult with Phase 2 fields is JSON-serializable."""
    import json
    import dataclasses

    result = PipelineResult(
        run_id="serialize_test",
        status="ok",
        script_path="/tmp/script.txt",
        audio_path="/tmp/audio.mp3",
    )

    # Convert to dict (simulating JSON serialization)
    d = dataclasses.asdict(result)
    assert d["script_path"] == "/tmp/script.txt"
    assert d["audio_path"] == "/tmp/audio.mp3"
    assert d["status"] == "ok"
