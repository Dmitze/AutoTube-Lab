"""Locust load-test scaffold for pipeline orchestration (Phase 9).

Targets roadmap tasks T-561/T-562 with a dry-run pipeline user profile.
The workload avoids external network calls by relying on synthetic adapters.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from locust import User, between, task

from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource
from modules.orchestrator import Pipeline


@dataclass(frozen=True)
class LoadConfig:
    """Load profile constants used by ``PipelineUser``.

    Complexity
    ----------
    O(1)
    """

    min_wait_seconds: int = 60
    max_wait_seconds: int = 300
    user_count: int = 10
    ramp_up_seconds: int = 60


class PipelineUser(User):
    """Locust user that executes deterministic dry-run pipeline invocations.

    Each task run emits a Locust request event for success/failure accounting.

    Complexity
    ----------
    O(n) where n = number of generated trends/plans in one pipeline run.
    """

    wait_time = between(LoadConfig.min_wait_seconds, LoadConfig.max_wait_seconds)

    def on_start(self) -> None:
        """Initialize a mock-only pipeline instance once per user. O(1)."""
        self._pipeline = Pipeline(
            trend_source=SyntheticTrendSource(seed=42),
            storage=InMemoryStorage(),
            dry_run=True,
            seed=42,
        )

    @task
    def run_pipeline(self) -> None:
        """Execute one pipeline run and report latency/error metrics. O(n)."""
        start = time.perf_counter()
        exc: Exception | None = None
        try:
            result = self._pipeline.run(run_id=f"locust-{time.time_ns()}")
            if result.status == "error":
                exc = RuntimeError("pipeline returned error status")
        except Exception as err:  # noqa: BLE001
            exc = err
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.environment.events.request.fire(
            request_type="pipeline",
            name="run",
            response_time=elapsed_ms,
            response_length=0,
            exception=exc,
        )
