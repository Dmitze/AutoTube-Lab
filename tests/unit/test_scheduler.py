"""Unit tests for UploadScheduler (priority queue).

Roadmap tasks: T-300 through T-303 (EPIC 4.5)
"""

import time
from unittest.mock import MagicMock

import pytest

from modules.scheduler import UploadScheduler
from ytaimbot_ml.schemas import UploadJob


@pytest.fixture
def scheduler():
    return UploadScheduler(max_per_day=6)


def test_schedule_and_next_due(scheduler):
    """Test scheduling and retrieving due jobs (T-301)."""
    now = time.time()
    
    # Job 1: due now
    job1 = UploadJob(scheduled_at=now - 10, plan_id="p1", video_path="v1.mp4")
    # Job 2: due in the future
    job2 = UploadJob(scheduled_at=now + 100, plan_id="p2", video_path="v2.mp4")
    
    scheduler.schedule(job1)
    scheduler.schedule(job2)
    
    # First call should return job1 (it's due)
    due = scheduler.next_due()
    assert due is not None
    assert due.plan_id == "p1"
    
    # Second call should return None (job2 is not due yet)
    due = scheduler.next_due()
    assert due is None


def test_priority_order(scheduler):
    """Test that jobs are returned in order of scheduled_at."""
    now = time.time()
    
    job_late = UploadJob(scheduled_at=now - 10, plan_id="late", video_path="v.mp4")
    job_early = UploadJob(scheduled_at=now - 50, plan_id="early", video_path="v.mp4")
    
    # Schedule in "wrong" order
    scheduler.schedule(job_late)
    scheduler.schedule(job_early)
    
    # Should get 'early' first
    assert scheduler.next_due().plan_id == "early"
    assert scheduler.next_due().plan_id == "late"


def test_max_uploads_per_day_limit():
    """T-302: Test that MAX_UPLOADS_PER_DAY blocks further uploads."""
    scheduler = UploadScheduler(max_per_day=1)
    now = time.time()
    
    job1 = UploadJob(scheduled_at=now - 100, plan_id="p1", video_path="/v1")
    job2 = UploadJob(scheduled_at=now - 50, plan_id="p2", video_path="/v2")
    
    scheduler.schedule(job1)
    scheduler.schedule(job2)
    
    # First job should be due
    due_job = scheduler.next_due()
    assert due_job is not None
    assert due_job.plan_id == "p1"
    
    # Second job should be blocked because max_per_day is 1
    blocked_job = scheduler.next_due()
    assert blocked_job is None


def test_queue_persists_across_restarts():
    """T-303: Test that queue restores state via storage adapter."""
    mock_storage = MagicMock()
    now = time.time()
    job1 = UploadJob(scheduled_at=now - 10, plan_id="p1", video_path="/v1")
    job2 = UploadJob(scheduled_at=now + 10, plan_id="p2", video_path="/v2")
    
    # Setup mock to return these jobs when load_upload_queue is called
    mock_storage.load_upload_queue.return_value = [job1, job2]
    
    # Init scheduler with mock storage (simulates restart)
    scheduler = UploadScheduler(storage=mock_storage, max_per_day=10)
    
    # load_upload_queue should have been called during __init__
    mock_storage.load_upload_queue.assert_called_once()
    
    # next_due should pop job1
    due_job = scheduler.next_due()
    assert due_job is not None
    assert due_job.plan_id == "p1"
    
    # next_due should return None for job2 (it's in the future)
    assert scheduler.next_due() is None
    
    # After pop, the job should be removed from storage
    mock_storage.delete_upload_job.assert_called_with("p1")
