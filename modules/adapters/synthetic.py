"""Synthetic (in-memory) adapters for dry-run and testing.

These adapters produce deterministic fake data and store everything in
memory.  They never make network calls.
"""

from __future__ import annotations

import numpy as np

from modules.adapters.base import PublisherAdapter, StorageAdapter, TrendSourceAdapter
from ytaimbot_ml.schemas import ComplianceReport, ContentPlan, TrendSignal


class SyntheticTrendSource(TrendSourceAdapter):
    """Generates 10 synthetic trend signals using a seeded RNG.

    Parameters
    ----------
    seed:
        Integer seed for reproducibility.  Defaults to 0.
    """

    _KEYWORDS = [
        "ai_automation", "passive_income", "crypto_2026", "youtube_shorts",
        "side_hustle", "stock_tips", "niche_cooking", "travel_hacks",
        "fitness_ai", "coding_bootcamp",
    ]

    def __init__(self, seed: int = 0) -> None:
        self._rng = np.random.default_rng(seed)

    def fetch(self) -> list[TrendSignal]:
        """Return exactly 10 synthetic TrendSignal objects."""
        scores = self._rng.uniform(0.1, 1.0, size=len(self._KEYWORDS))
        return [
            TrendSignal(
                trend_id=f"synthetic_{i:02d}",
                keyword=kw,
                raw_score=float(scores[i]),
                source="synthetic",
                timestamp="2026-01-01T00:00:00Z",
            )
            for i, kw in enumerate(self._KEYWORDS)
        ]


class InMemoryStorage(StorageAdapter):
    """Stores pipeline artefacts in plain Python dicts.

    Useful for dry-run pipelines and unit tests.
    """

    def __init__(self) -> None:
        self._runs: dict[str, str] = {}
        self._trends: dict[str, list[TrendSignal]] = {}
        self._compliance: dict[str, list[ComplianceReport]] = {}

    # --- StorageAdapter interface ---

    def save_run(self, run_id: str, status: str) -> None:
        self._runs[run_id] = status

    def save_trends(self, run_id: str, trends: list[TrendSignal]) -> None:
        self._trends[run_id] = list(trends)

    def save_compliance(
        self, run_id: str, reports: list[ComplianceReport]
    ) -> None:
        self._compliance[run_id] = list(reports)

    # --- Inspection helpers (not part of the ABC) ---

    def get_run_status(self, run_id: str) -> str | None:
        return self._runs.get(run_id)

    def get_trends(self, run_id: str) -> list[TrendSignal]:
        return self._trends.get(run_id, [])

    def get_compliance(self, run_id: str) -> list[ComplianceReport]:
        return self._compliance.get(run_id, [])


class StubPublisher(PublisherAdapter):
    """Records publish calls without actually publishing anything."""

    def __init__(self) -> None:
        self.published: list[tuple[ContentPlan, ComplianceReport]] = []

    def publish(self, plan: ContentPlan, compliance_report: ComplianceReport) -> bool:
        self.published.append((plan, compliance_report))
        return True
