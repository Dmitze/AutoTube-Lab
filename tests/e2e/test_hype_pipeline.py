"""E2E dry-run test for hype-focused pipeline path (P13, T-954)."""

from __future__ import annotations

from modules.adapters.base import TrendSourceAdapter
from modules.adapters.synthetic import InMemoryStorage, StubPublisher
from modules.orchestrator import Pipeline
from ytaimbot_ml.schemas import TrendSignal


class HypeTrendSource(TrendSourceAdapter):
    """Deterministic trend source emphasizing hype-character topics."""

    def fetch(self) -> list[TrendSignal]:
        return [
            TrendSignal("hype_judy_hopps", "Judy Hopps Zootopia 2", 0.98, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_nick_wilde", "Nick Wilde arc", 0.95, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_batman", "Batman comeback", 0.92, "youtube_search", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_spiderman", "Spider Man trending", 0.90, "youtube_search", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_naruto", "Naruto return", 0.88, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_goku", "Goku new form", 0.85, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_elsa", "Elsa fan story", 0.82, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_anna", "Anna drama", 0.80, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_skibidi", "Skibidi titan", 0.79, "google_trends", "2026-01-01T00:00:00Z"),
            TrendSignal("hype_multiverse", "multiverse clash", 0.77, "youtube_search", "2026-01-01T00:00:00Z"),
        ]


def test_hype_pipeline_dry_run_seed_42() -> None:
    """Pipeline runs successfully on hype trends with dry_run=True, seed=42."""
    source = HypeTrendSource()
    storage = InMemoryStorage()
    publisher = StubPublisher()
    from unittest.mock import MagicMock
    from ytaimbot_ml.schemas import VideoAsset
    video_assembler = MagicMock()
    video_assembler.assemble.return_value = VideoAsset(plan_id="e2e", video_path="mock.mp4", thumbnail_path="mock.png")
    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
        publisher=publisher,
        video_assembler=video_assembler,
        dry_run=True,
        seed=42,
    )

    result = pipeline.run(run_id="e2e-hype-001")

    assert result.status == "ok"
    assert len(result.rankings) >= 5
    assert len(result.plans) == 1
    assert len(result.compliance_reports) == 1
    assert all("hype_" in plan.trend_id for plan in result.plans)
    assert len(publisher.published) == 0  # dry-run fail-closed for publish side effects
