"""Unit tests for MetricsCollector (YouTube Analytics API integration).

Roadmap tasks: T-333 through T-337 (EPIC 5.2)
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from modules.metrics_collector import MetricsCollector, TooEarlyError
from ytaimbot_ml.schemas import MetricsSnapshot

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def collector(mock_storage):
    return MetricsCollector(storage=mock_storage)

def test_collect_too_early(collector):
    """Test that videos < 48h old raise TooEarlyError (T-334)."""
    pub_at = datetime.now(timezone.utc) - timedelta(hours=24)
    
    with pytest.raises(TooEarlyError):
        collector.collect("vid123", pub_at)

def test_collect_success(collector):
    """Test successful metrics collection with mocked API (T-335)."""
    pub_at = datetime.now(timezone.utc) - timedelta(hours=72)
    
    # Mock the API service chain
    mock_service = MagicMock()
    mock_query = mock_service.reports().query
    mock_query.return_value.execute.return_value = {
        "rows": [[1000, 2.5, 3600, 5.0]] # views, revenue, duration, ctr
    }
    
    with patch.object(collector, '_get_service', return_value=mock_service):
        snapshot = collector.collect("vid123", pub_at)
        
        assert snapshot.video_id == "vid123"
        assert snapshot.views == 1000
        assert snapshot.rpm == 2.5
        assert snapshot.watch_time_h == 1.0
        assert snapshot.ctr == 0.05

def test_collect_all_pending(collector, mock_storage):
    """Test batch collection logic (T-330, T-336)."""
    # 1. Mock storage to return 2 videos
    pub_old = datetime.now(timezone.utc) - timedelta(hours=100)
    pub_new = datetime.now(timezone.utc) - timedelta(hours=10)
    
    mock_storage.list_published_videos.return_value = [
        {"video_id": "old", "published_at": pub_old.timestamp()},
        {"video_id": "new", "published_at": pub_new.timestamp()},
    ]
    
    # 2. Mock collect() to succeed for old, fail for new
    def side_effect(vid, ts):
        if vid == "old":
            return MetricsSnapshot(video_id=vid)
        raise TooEarlyError("too new")

    with patch.object(collector, 'collect', side_effect=side_effect):
        snapshots = collector.collect_all_pending()
        
        assert len(snapshots) == 1
        assert snapshots[0].video_id == "old"
        assert mock_storage.save_metrics.called
