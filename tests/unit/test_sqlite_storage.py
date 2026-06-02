"""Unit tests for SQLiteStorage (persistent storage).

Roadmap tasks: T-322 through T-325 (EPIC 5.1)
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from modules.adapters.storage.sqlite import SQLiteStorage
from ytaimbot_ml.schemas import MetricsSnapshot, ABTestResult

@pytest.fixture
def storage():
    # Use in-memory SQLite for tests
    return SQLiteStorage(db_path=Path(":memory:"))

def test_save_run_and_load_run(storage):
    """Test save_run and load_run (roundtrip)."""
    storage.save_run("run-1", "ok")
    
    run = storage.load_run("run-1")
    assert run["run_id"] == "run-1"
    assert run["status"] == "ok"
    assert "timestamp" in run

def test_save_video_and_get_upload_count(storage):
    """Test save_video and count (T-314)."""
    storage.save_video("v1", "t1", "Title 1")
    storage.save_video("v2", "t2", "Title 2")
    
    count = storage.get_upload_count()
    assert count == 2

def test_save_metrics_and_get_top(storage):
    """Test metrics persistence and top videos query (T-315, T-317)."""
    storage.save_video("v1", "t1", "Title 1")
    
    m1 = MetricsSnapshot(
        video_id="v1",
        views=1000,
        ctr=0.05,
        retention_30s=0.7,
        rpm=2.5,
        watch_time_h=10.5,
        collected_at=datetime.now(timezone.utc)
    )
    storage.save_metrics(m1)
    
    top = storage.get_top_videos(n=1, metric="views")
    assert len(top) == 1
    assert top[0]["video_id"] == "v1"
    assert top[0]["views"] == 1000

def test_metrics_unique_constraint(storage):
    """Test that UNIQUE(video_id, collected_at) works (T-324)."""
    storage.save_video("v1", "t1", "Title 1")
    ts = datetime.now(timezone.utc)
    
    m1 = MetricsSnapshot(video_id="v1", views=100, collected_at=ts)
    m2 = MetricsSnapshot(video_id="v1", views=200, collected_at=ts)
    
    storage.save_metrics(m1)
    # m2 should be ignored due to INSERT OR IGNORE
    storage.save_metrics(m2)
    
    top = storage.get_top_videos(n=10, metric="views")
    assert top[0]["views"] == 100

def test_save_ab_test(storage):
    """Test A/B test persistence (T-319)."""
    storage.save_video("v1", "t1", "Title 1")
    test = ABTestResult(
        video_id="v1",
        variant_type="title",
        winner="a",
        p_value=0.03,
        significant=True
    )
    storage.save_ab_test(test)
    
    # Verify by direct query
    cur = storage._conn.execute("SELECT * FROM ab_tests")
    row = cur.fetchone()
    assert row["video_id"] == "v1"
    assert row["winner"] == "a"
    assert row["significant"] == 1
