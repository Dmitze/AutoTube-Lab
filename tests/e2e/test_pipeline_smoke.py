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
import pytest

from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource
from modules.orchestrator import Pipeline


def test_pipeline_smoke_dry_run():
    """Full pipeline completes with status='ok' using synthetic adapters."""
    source = SyntheticTrendSource(seed=42)
    storage = InMemoryStorage()
    pipeline = Pipeline(trend_source=source, storage=storage, dry_run=True, seed=42)

    result = pipeline.run(run_id="e2e-smoke-001")

    assert result.status == "ok"
    assert len(result.rankings) >= 5
    assert len(result.plans) == 5
    assert len(result.compliance_reports) == 5


def test_pipeline_smoke_deterministic():
    """Same seed produces identical rankings on two runs."""
    source1 = SyntheticTrendSource(seed=42)
    source2 = SyntheticTrendSource(seed=42)

    result1 = Pipeline(trend_source=source1, storage=InMemoryStorage(),
                       dry_run=True, seed=42).run("det-001")
    result2 = Pipeline(trend_source=source2, storage=InMemoryStorage(),
                       dry_run=True, seed=42).run("det-002")

    ids1 = [r.trend_id for r in result1.rankings[:5]]
    ids2 = [r.trend_id for r in result2.rankings[:5]]
    assert ids1 == ids2, "Rankings not deterministic!"
