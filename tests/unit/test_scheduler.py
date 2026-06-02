"""Unit tests for UploadScheduler (priority queue).

Roadmap tasks: T-300 through T-303 (EPIC 4.5)
"""

import time
import pytest
from modules.scheduler import UploadScheduler, UploadJob

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
