"""QuotaGuard: Token Bucket rate limiter for YouTube API uploads.

Roadmap tasks: T-401 through T-410 (EPIC 4.2 Rate Limiting)

Algorithm — Token Bucket
------------------------
State:      tokens (float),  last_refill (monotonic time)
Capacity:   max_per_day tokens
Refill:     rate = max_per_day / 86400 tokens/second (continuous)
allow():    lazy-refill then check tokens ≥ 1; consume 1 → O(1)

Token Bucket vs Sliding Window:
  Token Bucket    — allows short bursts, smooths long-term rate
  Sliding Window  — strict count in rolling window, no burst

Cost table (YouTube Data API v3 quota units):
  video.insert        → 1600 units
  thumbnails.set      →   50 units
  videos.list         →    1 unit
  channels.list       →    1 unit
  Daily free quota    → 10 000 units (1 full upload = 1650)

Safety rules:
  - YTAIMBOT_DRY_RUN=true  → allow() always returns False (fail-closed)
  - max_per_day=0          → allow() always returns False (disabled)
  - reset()                → restore to full capacity (test helper)
"""
from __future__ import annotations

import os
import time


class QuotaExhaustedError(Exception):
    """Raised when the Token Bucket is empty and the caller needs a hard fail.

    Examples
    --------
    >>> guard = QuotaGuard(max_per_day=0)
    >>> guard.allow()
    False
    """


class QuotaGuard:
    """Token Bucket rate limiter for YouTube upload scheduling.

    Parameters
    ----------
    max_per_day:
        Maximum upload tokens per day.  0 disables uploads entirely.
    _dry_run:
        Override for ``YTAIMBOT_DRY_RUN`` env var (test injection).

    Complexity
    ----------
    allow(): O(1) — single float comparison and subtraction
    refill(): O(1) — time delta multiply

    Examples
    --------
    >>> import os; os.environ["YTAIMBOT_DRY_RUN"] = "false"
    >>> guard = QuotaGuard(max_per_day=6, _dry_run=False)
    >>> guard.allow()
    True
    >>> os.environ["YTAIMBOT_DRY_RUN"] = "true"
    """

    #: Quota units consumed per operation (YouTube Data API v3)
    COST_UPLOAD: int = 1600
    COST_THUMBNAIL: int = 50
    COST_LIST: int = 1

    def __init__(
        self,
        max_per_day: int = 6,
        *,
        _dry_run: bool | None = None,
    ) -> None:
        self.max_per_day = max_per_day
        self._tokens: float = float(max_per_day)
        self._last_refill: float = time.monotonic()
        # Allow test injection; otherwise read env var
        if _dry_run is not None:
            self._dry_run = _dry_run
        else:
            self._dry_run = os.environ.get("YTAIMBOT_DRY_RUN", "true").lower() != "false"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def allow(self) -> bool:
        """Check whether an upload slot is available and consume it.

        Performs lazy Token Bucket refill, then checks ``tokens ≥ 1``.

        Returns
        -------
        bool
            ``True`` if a token was consumed (upload allowed).
            ``False`` if dry-run mode, disabled, or bucket empty.

        Complexity
        ----------
        O(1)

        Examples
        --------
        >>> guard = QuotaGuard(max_per_day=2, _dry_run=False)
        >>> guard.allow()
        True
        >>> guard.allow()
        True
        >>> guard.allow()
        False
        """
        if self._dry_run:
            return False
        if self.max_per_day == 0:
            return False

        self._refill()

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    def remaining(self) -> float:
        """Return current token count after a lazy refill.

        Complexity: O(1)

        Examples
        --------
        >>> guard = QuotaGuard(max_per_day=6, _dry_run=False)
        >>> 0.0 <= guard.remaining() <= 6.0
        True
        """
        self._refill()
        return self._tokens

    def reset(self) -> None:
        """Restore to full capacity. Intended for test teardown only.

        Complexity: O(1)

        Examples
        --------
        >>> guard = QuotaGuard(max_per_day=3, _dry_run=False)
        >>> guard.allow(); guard.allow()
        True
        True
        >>> guard.reset()
        >>> guard.remaining()
        3.0
        """
        self._tokens = float(self.max_per_day)
        self._last_refill = time.monotonic()

    def require(self) -> None:
        """Like allow() but raises QuotaExhaustedError instead of returning False.

        Use in pipeline stages where a token is mandatory.

        Raises
        ------
        QuotaExhaustedError
            If the bucket is empty, disabled, or in dry-run mode.

        Complexity: O(1)

        Examples
        --------
        >>> guard = QuotaGuard(max_per_day=0, _dry_run=False)
        >>> guard.require()
        Traceback (most recent call last):
            ...
        ytaimbot_ml.quota.guard.QuotaExhaustedError: quota exhausted or disabled
        """
        if not self.allow():
            raise QuotaExhaustedError("quota exhausted or disabled")

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _refill(self) -> None:
        """Lazy Token Bucket refill based on elapsed wall-clock time.

        Adds ``elapsed × rate`` tokens, clamped to ``max_per_day``.

        Complexity: O(1)
        """
        if self.max_per_day == 0:
            return
        now = time.monotonic()
        elapsed = now - self._last_refill
        rate = self.max_per_day / 86_400.0  # tokens per second
        self._tokens = min(self.max_per_day, self._tokens + elapsed * rate)
        self._last_refill = now

