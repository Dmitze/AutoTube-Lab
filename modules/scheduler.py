"""Phase 4 — UploadScheduler: Priority-based persistent upload queue.

Roadmap tasks: T-294 through T-303 (EPIC 4.5 Upload Scheduler)

Algorithm
---------
1. Data Structure: Min-heap (heapq) based on scheduled_at timestamp.
2. Complexity: O(log n) push/pop, O(1) peek.
3. Persistence: Jobs are stored in SQLite (T-299) to survive restarts.
4. Scheduling: Respects MAX_UPLOADS_PER_DAY (T-298).
"""

from __future__ import annotations

import datetime
import heapq
import logging
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Tuple

from ytaimbot_ml.schemas import UploadJob

if TYPE_CHECKING:
    from ytaimbot_ml.schemas import ContentPlan, VideoAsset
    from modules.adapters.base import StorageAdapter

logger = logging.getLogger(__name__)


class UploadScheduler:
    """Priority queue (min-heap) for video uploads.

    Parameters
    ----------
    storage:
        Persistent storage adapter for queue recovery.
    max_per_day:
        Daily upload limit (T-298).
    """

    def __init__(
        self,
        storage: Optional[StorageAdapter] = None,
        max_per_day: int | None = None,
    ) -> None:
        self._heap: List[UploadJob] = []
        self._storage = storage
        self._max_per_day = max_per_day or int(os.environ.get("MAX_UPLOADS_PER_DAY", "1"))
        self._uploads_today = 0
        self._last_upload_date = None
        
        if self._storage:
            self._load_from_storage()

    def schedule(self, job: UploadJob) -> None:
        """Add a job to the queue.  O(log n).

        Parameters
        ----------
        job:
            The upload job to schedule.
        """
        heapq.heappush(self._heap, job)
        logger.info("Scheduler: job %s scheduled at %s", job.plan_id, datetime.datetime.fromtimestamp(job.scheduled_at))
        
        if self._storage:
            self._save_to_storage(job)

    def next_due(self) -> Optional[UploadJob]:
        """Get the next job that is due for upload.  O(log n) pop, O(1) peek.

        Returns
        -------
        Optional[UploadJob]
            The next job if its time has come, else None.
        """
        current_date = datetime.datetime.fromtimestamp(time.time()).date()
        if self._last_upload_date != current_date:
            self._uploads_today = 0
            self._last_upload_date = current_date
            
        if self._uploads_today >= self._max_per_day:
            return None
            
        if not self._heap:
            return None
        
        # Peek at the top of the heap
        if self._heap[0].scheduled_at <= time.time():
            job = heapq.heappop(self._heap)
            if self._storage:
                self._remove_from_storage(job)
            self._uploads_today += 1
            return job
        
        return None

    def _load_from_storage(self) -> None:
        """Restore queue from persistent storage (T-299).  O(n log n)."""
        if not self._storage:
            return
        try:
            jobs = self._storage.load_upload_queue()
            for job in jobs:
                heapq.heappush(self._heap, job)
        except Exception as exc:
            logger.warning("Scheduler: failed to load queue from storage: %s", exc)

    def _save_to_storage(self, job: UploadJob) -> None:
        """Persist a new job to storage.  O(1) storage write."""
        if not self._storage:
            return
        try:
            self._storage.save_upload_job(job)
        except Exception as exc:
            logger.warning("Scheduler: failed to save job to storage: %s", exc)

    def _remove_from_storage(self, job: UploadJob) -> None:
        """Remove a completed job from storage.  O(1) storage delete."""
        if not self._storage:
            return
        try:
            self._storage.delete_upload_job(job.plan_id)
        except Exception as exc:
            logger.warning("Scheduler: failed to delete job from storage: %s", exc)
