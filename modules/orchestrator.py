"""MVP pipeline orchestrator.

Stages
------
1. ingest    — fetch TrendSignals from source adapter
2. featurize — (handled inside TrendAnalyzer.analyze)
3. reduce    — SVD/PCA dimensionality reduction (inside TrendAnalyzer)
4. score     — rank trends by magnitude
5. plan      — generate stub ContentPlans for top-N trends
6. gate      — compliance check via BayesQualityFilter
7. publish   — publish plans that passed the gate (skip in dry_run)

Fail-closed design: publish is NEVER called unless a ComplianceReport
with decision="pass" exists for the plan.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from modules.adapters.base import PublisherAdapter, StorageAdapter, TrendSourceAdapter
from ytaimbot_ml.quality.bayes_filter import BayesQualityFilter
from ytaimbot_ml.schemas import (
    ComplianceReport,
    ContentPlan,
    PipelineResult,
    TrendRanking,
    TrendSignal,
)
from ytaimbot_ml.trend_analyzer import TrendAnalyzer
from ytaimbot_ml.utils.random import make_rng

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the full trend-to-publish pipeline.

    Parameters
    ----------
    trend_source:
        Adapter that provides TrendSignal objects.
    storage:
        Adapter that persists run artefacts.
    publisher:
        Optional adapter for publishing approved content.  When omitted
        (or dry_run=True) publish calls are skipped entirely.
    dry_run:
        When ``True`` (default), no actual publishing occurs — all stages
        run but stage 7 is a no-op.
    seed:
        Integer seed for the ML components.  Defaults to 42.
    """

    _TOP_N = 5  # number of top trends to plan content for

    def __init__(
        self,
        trend_source: TrendSourceAdapter,
        storage: StorageAdapter,
        publisher: Optional[PublisherAdapter] = None,
        dry_run: bool = True,
        seed: int = 42,
    ) -> None:
        self._source = trend_source
        self._storage = storage
        self._publisher = publisher
        self._dry_run = dry_run
        self._analyzer = TrendAnalyzer(rng=make_rng(seed))
        self._gate = BayesQualityFilter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, run_id: str | None = None) -> PipelineResult:
        """Execute all pipeline stages and return a PipelineResult.

        Parameters
        ----------
        run_id:
            Unique identifier for this run.  Auto-generated if omitted.

        Returns
        -------
        PipelineResult
            Contains rankings, content plans, compliance reports, and
            overall status.
        """
        run_id = run_id or str(uuid.uuid4())
        logger.info("Pipeline run %s started (dry_run=%s)", run_id, self._dry_run)

        result = PipelineResult(run_id=run_id)

        try:
            # Stage 1: ingest
            signals = self._ingest()
            self._storage.save_trends(run_id, signals)

            # Stages 2–4: featurize → reduce → score (inside analyzer)
            rankings = self._score(signals)
            result.rankings = rankings

            # Stage 5: plan
            plans = self._plan(rankings)
            result.plans = plans

            # Stage 6: gate
            reports = self._gate_all(plans)
            result.compliance_reports = reports
            self._storage.save_compliance(run_id, reports)

            # Stage 7: publish (fail-closed)
            if not self._dry_run and self._publisher is not None:
                self._publish_approved(plans, reports)

            result.status = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline run %s failed: %s", run_id, exc)
            result.status = "error"

        self._storage.save_run(run_id, result.status)
        logger.info("Pipeline run %s finished with status=%s", run_id, result.status)
        return result

    # ------------------------------------------------------------------
    # Private stage implementations
    # ------------------------------------------------------------------

    def _ingest(self) -> list[TrendSignal]:
        signals = self._source.fetch()
        logger.debug("Ingested %d signals", len(signals))
        return signals

    def _score(self, signals: list[TrendSignal]) -> list[TrendRanking]:
        rankings = self._analyzer.analyze(signals)
        logger.debug("Scored %d trends", len(rankings))
        return rankings

    def _plan(self, rankings: list[TrendRanking]) -> list[ContentPlan]:
        top = rankings[: self._TOP_N]
        plans = [
            ContentPlan(
                trend_id=r.trend_id,
                title=f"Video about {r.trend_id}",
                outline=[
                    "Introduction",
                    "Main content",
                    "Call to action",
                ],
                keywords=[r.trend_id, "youtube", "2026"],
            )
            for r in top
        ]
        logger.debug("Generated %d content plans", len(plans))
        return plans

    def _gate_all(self, plans: list[ContentPlan]) -> list[ComplianceReport]:
        reports: list[ComplianceReport] = []
        for plan in plans:
            features = _plan_to_features(plan)
            report = self._gate.decide(features)
            reports.append(report)
            logger.debug(
                "Compliance gate for %s → %s (p_bad=%.3f)",
                plan.trend_id,
                report.decision,
                report.bayes_p_bad,
            )
        return reports

    def _publish_approved(
        self,
        plans: list[ContentPlan],
        reports: list[ComplianceReport],
    ) -> None:
        """Publish only plans whose compliance report has decision="pass"."""
        assert self._publisher is not None  # guaranteed by caller
        for plan, report in zip(plans, reports):
            if report.decision == "pass":
                ok = self._publisher.publish(plan, report)
                logger.info("Published %s → %s", plan.trend_id, ok)
            else:
                logger.info(
                    "Skipped publish for %s (compliance failed)", plan.trend_id
                )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plan_to_features(plan: ContentPlan) -> dict[str, float]:
    """Convert a ContentPlan to a feature dict for the Bayes gate.

    All features are normalised to [0, 1].  In production these would
    come from a real quality-scoring model.
    """
    title_len = min(len(plan.title) / 100.0, 1.0)
    n_keywords = min(len(plan.keywords) / 10.0, 1.0)
    n_outline = min(len(plan.outline) / 10.0, 1.0)
    return {
        "title_length_norm": title_len,
        "keyword_density": n_keywords,
        "outline_depth": n_outline,
    }


# ---------------------------------------------------------------------------
# Module entry-point for quick sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource

    source = SyntheticTrendSource(seed=42)
    storage = InMemoryStorage()
    pipeline = Pipeline(trend_source=source, storage=storage, dry_run=True)

    result = pipeline.run(run_id="demo-run-001")
    print(f"Status : {result.status}")
    print(f"Rankings: {len(result.rankings)}")
    print(f"Plans   : {len(result.plans)}")
    print(f"Reports : {len(result.compliance_reports)}")
    sys.exit(0 if result.status == "ok" else 1)
