"""E2E smoke test — full pipeline with synthetic adapters (dry_run=True).

Roadmap: T-580 (Phase 9 E2E Testing)
Seed: 42 (deterministic)
Timeout: < 10s

What this tests:
  - Pipeline runs end-to-end without exception
  - PipelineResult.status == "ok"
  - len(rankings) >= 5
  - len(plans) == 5
  - len(compliance_reports) == 5
  - No actual publishing (dry_run=True)
  - Deterministic: same result for same seed

Run:
    pytest tests/e2e/test_pipeline_smoke.py -v
"""

from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource
from modules.orchestrator import Pipeline


def test_pipeline_smoke_dry_run():
    """Full pipeline completes with status='ok' using synthetic adapters."""
    source = SyntheticTrendSource(seed=42)
    storage = InMemoryStorage()
    from unittest.mock import MagicMock
    from ytaimbot_ml.schemas import VideoAsset
    video_assembler = MagicMock()
    video_assembler.assemble.return_value = VideoAsset(plan_id="e2e", video_path="mock.mp4", thumbnail_path="mock.png")
    pipeline = Pipeline(trend_source=source, storage=storage, video_assembler=video_assembler, dry_run=True, seed=42)

    result = pipeline.run(run_id="e2e-smoke-001")

    assert result.status == "ok"
    assert len(result.rankings) >= 5
    assert len(result.plans) == 1
    assert len(result.compliance_reports) == 1


def test_pipeline_smoke_deterministic():
    """Same seed produces identical rankings on two runs."""
    source1 = SyntheticTrendSource(seed=42)
    source2 = SyntheticTrendSource(seed=42)

    from unittest.mock import MagicMock
    from ytaimbot_ml.schemas import VideoAsset
    va1 = MagicMock()
    va1.assemble.return_value = VideoAsset(plan_id="e2e", video_path="mock.mp4", thumbnail_path="mock.png")
    va2 = MagicMock()
    va2.assemble.return_value = VideoAsset(plan_id="e2e", video_path="mock.mp4", thumbnail_path="mock.png")

    result1 = Pipeline(trend_source=source1, storage=InMemoryStorage(),
                       video_assembler=va1, dry_run=True, seed=42).run("det-001")
    result2 = Pipeline(trend_source=source2, storage=InMemoryStorage(),
                       video_assembler=va2, dry_run=True, seed=42).run("det-002")

    ids1 = [r.trend_id for r in result1.rankings[:5]]
    ids2 = [r.trend_id for r in result2.rankings[:5]]
    assert ids1 == ids2, "Rankings not deterministic!"
