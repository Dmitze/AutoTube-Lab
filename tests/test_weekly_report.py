"""Tests for WeeklyReportGenerator (T-368 – T-371).

All tests use InMemoryStorage — no real SQLite or network calls.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from modules.reporting.weekly_report import WeeklyReportGenerator, ascii_bar


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_storage(n_videos: int = 5):
    """Return InMemoryStorage pre-populated with fake video data."""
    from modules.adapters.synthetic import InMemoryStorage
    storage = InMemoryStorage()
    for i in range(n_videos):
        storage.save_video(
            video_id=f"vid_{i:03d}",
            trend_id=f"trend_{i}",
            title=f"Test Video {i}: Amazing Content About Topic {i}",
            privacy_status="public",
        )
        # Inject metrics directly into the storage
        storage._videos[f"vid_{i:03d}"].update({
            "ctr": 0.05 + i * 0.01,
            "retention_30s": 0.55 + i * 0.05,
            "rpm": 2.0 + i * 1.5,
            "views": 1000 * (i + 1),
        })
    return storage


# ---------------------------------------------------------------------------
# T-365: ascii_bar
# ---------------------------------------------------------------------------

def test_ascii_bar_full():
    """T-365: ascii_bar with value == max_val fills the bar completely."""
    result = ascii_bar(10.0, 10.0, width=10)
    assert result.startswith("|")
    assert "█" * 10 in result
    assert "10.00" in result


def test_ascii_bar_empty():
    """T-365: ascii_bar with value == 0 shows empty bar."""
    result = ascii_bar(0.0, 10.0, width=10)
    assert "▛" * 10 in result
    assert "0.00" in result


def test_ascii_bar_half():
    """T-365: ascii_bar with value == max/2 fills half the bar."""
    result = ascii_bar(5.0, 10.0, width=10)
    assert result.count("█") == 5
    assert result.count("▛") == 5


def test_ascii_bar_zero_max():
    """T-365: ascii_bar with max_val=0 returns empty bar (no division by zero)."""
    result = ascii_bar(10.0, 0.0, width=10)
    assert "▛" * 10 in result


def test_ascii_bar_proportional():
    """T-365: ascii_bar filled count is proportional to value/max_val."""
    for pct in [0.0, 0.25, 0.5, 0.75, 1.0]:
        result = ascii_bar(pct * 100, 100.0, width=20)
        expected_filled = int(pct * 20)
        assert result.count("█") == expected_filled


# ---------------------------------------------------------------------------
# T-369: generate() returns non-empty markdown
# ---------------------------------------------------------------------------

def test_generate_returns_nonempty_markdown():
    """T-369: generate() returns a non-empty Markdown string."""
    storage = _make_storage(n_videos=5)
    gen = WeeklyReportGenerator(storage=storage)
    report = gen.generate(week=25, year=2026)

    assert isinstance(report, str)
    assert len(report) > 100
    assert "YTAIMBot Weekly Report" in report
    assert "2026 W25" in report


def test_generate_with_no_videos():
    """T-369: generate() works even with no published videos."""
    from modules.adapters.synthetic import InMemoryStorage
    storage = InMemoryStorage()
    gen = WeeklyReportGenerator(storage=storage)
    report = gen.generate(week=1, year=2026)

    assert isinstance(report, str)
    assert "No videos published yet" in report or "No data yet" in report


# ---------------------------------------------------------------------------
# T-370: report contains top/bottom/recommendations sections
# ---------------------------------------------------------------------------

def test_generate_contains_required_sections():
    """T-370: Report contains Summary, Top 5, Bottom 5, Recommendations."""
    storage = _make_storage(n_videos=8)
    gen = WeeklyReportGenerator(storage=storage)
    report = gen.generate(week=10, year=2026)

    assert "## 📊 Summary" in report
    assert "## 🏆 Top 5 Videos" in report
    assert "## ⚠️ Bottom 5 Videos" in report
    assert "## 💡 Recommendations" in report


def test_generate_top_videos_sorted_by_rpm():
    """T-370: Top videos are sorted by RPM descending."""
    storage = _make_storage(n_videos=6)
    gen = WeeklyReportGenerator(storage=storage)
    videos = storage.list_published_videos(limit=200)
    top = gen._top_videos(videos, n=3)

    rpms = [v.get("rpm", 0.0) for v in top]
    assert rpms == sorted(rpms, reverse=True)


def test_generate_bottom_videos_sorted_by_retention():
    """T-370: Bottom videos are sorted by retention ascending."""
    storage = _make_storage(n_videos=6)
    gen = WeeklyReportGenerator(storage=storage)
    videos = storage.list_published_videos(limit=200)
    bottom = gen._bottom_videos(videos, n=3)

    rets = [v.get("retention_30s", 0.0) for v in bottom]
    assert rets == sorted(rets)


def test_recommendations_low_ctr():
    """T-370: Low CTR triggers thumbnail recommendation."""
    from modules.adapters.synthetic import InMemoryStorage
    storage = InMemoryStorage()
    for i in range(5):
        storage.save_video(f"v{i}", f"t{i}", f"Title {i}")
        storage._videos[f"v{i}"].update({"ctr": 0.02, "retention_30s": 0.6, "rpm": 3.0, "views": 500})

    gen = WeeklyReportGenerator(storage=storage)
    videos = storage.list_published_videos()
    recs = gen._recommendations(videos)

    assert any("CTR" in r for r in recs)
    assert any("thumbnail" in r.lower() or "title" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# T-367: save() writes file to correct path
# ---------------------------------------------------------------------------

def test_save_writes_to_correct_path(tmp_path):
    """T-367: save() writes report to YYYY-WNN.md in reports_dir."""
    storage = _make_storage(n_videos=3)
    gen = WeeklyReportGenerator(storage=storage, reports_dir=tmp_path / "reports")
    report = gen.generate(week=22, year=2026)
    path = gen.save(report, week=22, year=2026)

    assert path.exists()
    assert path.name == "2026-W22.md"
    content = path.read_text(encoding="utf-8")
    assert "YTAIMBot Weekly Report" in content


def test_generate_and_save_roundtrip(tmp_path):
    """T-367: generate_and_save() creates file with correct content."""
    storage = _make_storage(n_videos=4)
    gen = WeeklyReportGenerator(storage=storage, reports_dir=tmp_path)
    path = gen.generate_and_save(week=5, year=2026)

    assert path.exists()
    assert "2026-W05" in path.name
