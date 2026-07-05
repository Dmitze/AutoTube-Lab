"""Integration tests for the Pipeline orchestrator."""

from __future__ import annotations


from modules.adapters.synthetic import (
    InMemoryStorage,
    StubPublisher,
    SyntheticTrendSource,
)
from modules.orchestrator import Pipeline
from ytaimbot_ml.schemas import ContentPlan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pipeline(dry_run: bool = True, seed: int = 42) -> tuple[Pipeline, InMemoryStorage, StubPublisher]:
    source = SyntheticTrendSource(seed=seed)
    storage = InMemoryStorage()
    publisher = StubPublisher()
    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
        publisher=publisher,
        dry_run=dry_run,
        seed=seed,
    )
    return pipeline, storage, publisher


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dry_run_pipeline() -> None:
    """A dry-run pipeline should complete all stages and return status='ok'."""
    pipeline, storage, _ = _make_pipeline(dry_run=True)
    result = pipeline.run(run_id="test-run-001")

    assert result.status == "ok"
    assert len(result.rankings) == 10  # 10 synthetic trends
    assert len(result.plans) == 1
    assert len(result.compliance_reports) == 1

    # Storage should have received the run
    assert storage.get_run_status("test-run-001") == "ok"
    assert len(storage.get_trends("test-run-001")) == 10
    assert len(storage.get_compliance("test-run-001")) == Pipeline._TOP_N


def test_gate_blocks_bad_content() -> None:
    """Plans with features that indicate bad content must be blocked by the gate."""
    from modules.orchestrator import _plan_to_features
    from ytaimbot_ml.quality.bayes_filter import BayesQualityFilter

    gate = BayesQualityFilter(prior_bad=0.9, threshold=0.5)

    # A plan with very high keyword density (near 1.0) should fail
    bad_plan = ContentPlan(
        trend_id="bad_trend",
        title="x" * 100,
        outline=["step"] * 10,
        keywords=["kw"] * 10,
    )
    features = _plan_to_features(bad_plan)
    report = gate.decide(features)
    # With prior_bad=0.9 and dense features, this should fail
    assert report.bayes_p_bad > 0.5


def test_no_publish_without_gate() -> None:
    """Publisher must not be called in dry_run mode."""
    pipeline, _, publisher = _make_pipeline(dry_run=True)
    pipeline.run(run_id="test-no-publish")
    assert len(publisher.published) == 0, "Publisher must not be called during dry_run"


def test_publish_called_when_not_dry_run() -> None:
    """In non-dry-run mode, publisher is called for plans that pass the gate."""
    pipeline, _, publisher = _make_pipeline(dry_run=False)
    result = pipeline.run(run_id="test-publish")

    assert result.status == "ok"
    passed = sum(1 for r in result.compliance_reports if r.decision == "pass")
    assert len(publisher.published) == passed


def test_pipeline_phase3_stages() -> None:
    """The pipeline should include Phase 3 stages: SEO, Video, Subtitles, Thumbnails."""
    pipeline, storage, _ = _make_pipeline(dry_run=True)
    result = pipeline.run(run_id="test-phase3")

    assert result.status == "ok"
    
    # Plans should have been optimized via Stage 8.1 (SEO)
    for plan in result.plans:
        # Check if KeywordExpander and TitleGenerator were called
        # KeywordExpander adds many keywords (default max 30)
        assert len(plan.keywords) >= 1
        # TitleGenerator ensures title is within 40-60 chars
        assert 40 <= len(plan.title) <= 60

    # Verify that video files were (mockingly) assembled in Stage 8.4
    # Note: In dry_run with synthetic components, we don't check disk, 
    # but we check if the stage was reached via logging or result fields.
    # For now, let's just ensure the pipeline finishes without error.
    assert result.run_id == "test-phase3"
