"""Synthetic (in-memory) adapters for dry-run and testing.

These adapters produce deterministic fake data and store everything in
memory.  They never make network calls.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

from modules.adapters.base import PublisherAdapter, StorageAdapter, TrendSourceAdapter
from ytaimbot_ml.schemas import (
    ABTestResult,
    ComplianceReport,
    ContentPlan,
    MetricsSnapshot,
    TrendSignal,
)


class SyntheticMetricsCollector:
    """Mock metrics collector that returns data from storage or generated values."""

    def __init__(self, storage: InMemoryStorage) -> None:
        self._storage = storage

    def collect(self, video_id: str, published_at: datetime) -> MetricsSnapshot:
        # Check storage first
        for m in self._storage._metrics:
            if m.video_id == video_id:
                return m
        # Default mock
        return MetricsSnapshot(
            video_id=video_id,
            views=1000,
            ctr=0.05,
            retention_30s=0.7,
            collected_at=datetime.now(timezone.utc)
        )


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
        self._videos: dict[str, dict] = {}
        self._metrics: list[MetricsSnapshot] = []
        self._niche_arms: dict[str, dict] = {}
        self._niche_weights: dict[str, float] = {}
        self._ppo_transitions: dict[str, dict] = {}

    # --- StorageAdapter interface ---

    def save_run(self, run_id: str, status: str) -> None:
        self._runs[run_id] = status

    def save_trends(self, run_id: str, trends: list[TrendSignal]) -> None:
        self._trends[run_id] = list(trends)

    def save_compliance(
        self, run_id: str, reports: list[ComplianceReport]
    ) -> None:
        self._compliance[run_id] = list(reports)

    def save_video(self, video_id: str, trend_id: str, title: str, privacy_status: str = "unlisted", published_at: float | None = None) -> None:
        self._videos[video_id] = {
            "video_id": video_id,
            "trend_id": trend_id,
            "title": title,
            "privacy_status": privacy_status,
            "published_at": published_at if published_at is not None else time.time(),
        }

    def save_metrics(self, metrics: MetricsSnapshot) -> None:
        self._metrics.append(metrics)

    def load_archive(self) -> dict[str, str]:
        return {r.content_hash: " ".join(r.reasons) for reports in self._compliance.values() for r in reports}

    def get_upload_count(self) -> int:
        return len(self._videos)

    def list_published_videos(self, limit: int = 100) -> list[dict]:
        return sorted(self._videos.values(), key=lambda v: v["published_at"], reverse=True)[:limit]

    def load_niche_weights(self) -> dict[str, float]:
        return self._niche_weights

    def save_niche_weights(self, weights: dict[str, float]) -> None:
        self._niche_weights.update(weights)

    def load_bandit_state(self) -> dict[str, dict]:
        return self._niche_arms

    def save_bandit_state(self, arm_id: str, n_pulls: int, total_reward: float, last_reward: float) -> None:
        self._niche_arms[arm_id] = {
            "arm_id": arm_id,
            "n_pulls": n_pulls,
            "total_reward": total_reward,
            "last_reward": last_reward,
            "updated_at": time.time(),
        }

    # Backward compatibility aliases for existing orchestrator calls if needed
    def load_niche_arms(self) -> list[dict[str, Any]]:
        return list(self._niche_arms.values())

    def upsert_niche_arm(self, arm_id: str, n_pulls: int, total_reward: float, last_reward: float) -> None:
        self.save_bandit_state(arm_id, n_pulls, total_reward, last_reward)

    def save_ppo_transition(self, video_id: str, state: list[float], action_idx: int, prob: float) -> None:
        self._ppo_transitions[video_id] = {
            "video_id": video_id,
            "state_json": json.dumps(state),
            "action_idx": action_idx,
            "prob": prob,
        }

    def load_ppo_transitions(self) -> list[dict]:
        return list(self._ppo_transitions.values())

    def clear_ppo_transitions(self) -> None:
        self._ppo_transitions.clear()

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
