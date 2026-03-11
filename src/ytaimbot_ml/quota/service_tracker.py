"""ServiceQuotaTracker: SQLite-backed per-service free-tier usage tracker.

Tracks character/credit consumption across TTS and LLM free-tier services.
Persists to ``data/quota.db`` so limits survive restarts.

Free-tier limits (2026, verified):
┌─────────────────┬──────────────────────┬──────────┬──────────────┐
│ Service         │ Limit                │ Period   │ Reset        │
├─────────────────┼──────────────────────┼──────────┼──────────────┤
│ edge-tts        │ unlimited            │ —        │ never        │
│ elevenlabs      │ 10 000 chars/month   │ 30 days  │ monthly      │
│ gemini-tts      │ ~1 000 000 chars/day │ 1 day    │ daily        │
│ ttsmaker        │ 20 000 chars/week    │ 7 days   │ weekly       │
│ minimax-tts     │ 10 000 credits/month │ 30 days  │ monthly      │
│ groq-llm        │ 14 400 req/day       │ 1 day    │ daily        │
│ gemini-llm      │ 1 500 req/day        │ 1 day    │ daily        │
└─────────────────┴──────────────────────┴──────────┴──────────────┘

Algorithm — Sliding Window Reset:
  On each check:  elapsed = now - period_start
  If elapsed ≥ period_days: reset used=0, period_start=now
  check_available: remaining = limit - used ≥ requested

Complexity: O(1) per call — single SQL read/write
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Final

_DB_DEFAULT: Final[str] = "data/quota.db"

# Default free-tier definitions: (limit, period_days)
# -1 = unlimited
_SERVICE_DEFAULTS: Final[dict[str, tuple[int, int]]] = {
    "edge-tts":    (-1,       1),   # unlimited, resets daily (no-op)
    "elevenlabs":  (10_000,  30),   # 10k chars/month
    "gemini-tts":  (1_000_000, 1),  # ~1M chars/day (generous free tier)
    "ttsmaker":    (20_000,   7),   # 20k chars/week
    "minimax-tts": (10_000,  30),   # 10k credits/month
    "groq-llm":    (14_400,   1),   # 14.4k req/day
    "gemini-llm":  (1_500,    1),   # 1500 req/day
}

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS service_quota (
    service      TEXT PRIMARY KEY,
    used         INTEGER NOT NULL DEFAULT 0,
    period_limit INTEGER NOT NULL DEFAULT -1,
    period_days  INTEGER NOT NULL DEFAULT 30,
    period_start TEXT    NOT NULL
)
"""


class ServiceQuotaTracker:
    """Per-service free-tier usage tracker backed by SQLite.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file. Created automatically if missing.
        Defaults to ``data/quota.db``.

    Complexity
    ----------
    check_available():  O(1) — single SQL SELECT
    consume():          O(1) — single SQL UPDATE
    reset_service():    O(1) — single SQL UPDATE

    Examples
    --------
    >>> tracker = ServiceQuotaTracker(db_path=":memory:")
    >>> tracker.check_available("elevenlabs", 500)
    True
    >>> tracker.consume("elevenlabs", 500)
    >>> tracker.remaining("elevenlabs")
    9500
    """

    def __init__(self, db_path: str | Path = _DB_DEFAULT) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()
        self._ensure_defaults()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_available(self, service: str, chars: int = 1) -> bool:
        """Return True if ``chars`` units are still available in this period.

        Unlimited services (limit=-1) always return True.
        Automatically resets usage if the period has expired.

        Parameters
        ----------
        service:
            Service identifier (e.g. ``"elevenlabs"``).
        chars:
            Number of characters/tokens/requests to check.

        Returns
        -------
        bool
            ``True`` if the request can proceed within free-tier limits.

        Complexity: O(1)

        Examples
        --------
        >>> t = ServiceQuotaTracker(db_path=":memory:")
        >>> t.check_available("edge-tts", 99999)
        True
        >>> t.check_available("elevenlabs", 1)
        True
        """
        self._maybe_reset(service)
        row = self._conn.execute(
            "SELECT used, period_limit FROM service_quota WHERE service=?",
            (service,),
        ).fetchone()
        if row is None:
            return True  # unknown service → allow
        used, limit = row
        if limit == -1:
            return True
        return (limit - used) >= chars

    def consume(self, service: str, chars: int) -> None:
        """Record that ``chars`` units were consumed from a service quota.

        No-op if the service is unlimited or unknown.

        Parameters
        ----------
        service:
            Service identifier.
        chars:
            Units consumed.

        Complexity: O(1)

        Examples
        --------
        >>> t = ServiceQuotaTracker(db_path=":memory:")
        >>> t.consume("elevenlabs", 1000)
        >>> t.remaining("elevenlabs")
        9000
        """
        self._maybe_reset(service)
        self._conn.execute(
            "UPDATE service_quota SET used = used + ? WHERE service=?",
            (chars, service),
        )
        self._conn.commit()

    def remaining(self, service: str) -> int:
        """Return remaining units for this service in the current period.

        Returns ``-1`` for unlimited services.

        Complexity: O(1)

        Examples
        --------
        >>> t = ServiceQuotaTracker(db_path=":memory:")
        >>> t.remaining("edge-tts")
        -1
        >>> t.remaining("elevenlabs") > 0
        True
        """
        self._maybe_reset(service)
        row = self._conn.execute(
            "SELECT used, period_limit FROM service_quota WHERE service=?",
            (service,),
        ).fetchone()
        if row is None:
            return -1
        used, limit = row
        if limit == -1:
            return -1
        return max(0, limit - used)

    def reset_service(self, service: str) -> None:
        """Manually reset a service's used counter to zero.

        Intended for test teardown or manual resets.

        Complexity: O(1)

        Examples
        --------
        >>> t = ServiceQuotaTracker(db_path=":memory:")
        >>> t.consume("elevenlabs", 5000)
        >>> t.reset_service("elevenlabs")
        >>> t.remaining("elevenlabs")
        10000
        """
        today = date.today().isoformat()
        self._conn.execute(
            "UPDATE service_quota SET used=0, period_start=? WHERE service=?",
            (today, service),
        )
        self._conn.commit()

    def summary(self) -> dict[str, dict[str, int | str]]:
        """Return a dict of all services with their current usage.

        Returns
        -------
        dict[str, dict]
            Keys: service name. Values: {used, limit, remaining, period_days}.

        Complexity: O(n) where n = number of services

        Examples
        --------
        >>> t = ServiceQuotaTracker(db_path=":memory:")
        >>> info = t.summary()
        >>> "edge-tts" in info
        True
        """
        rows = self._conn.execute(
            "SELECT service, used, period_limit, period_days, period_start FROM service_quota"
        ).fetchall()
        result: dict[str, dict[str, int | str]] = {}
        for service, used, limit, period_days, period_start in rows:
            remaining = -1 if limit == -1 else max(0, limit - used)
            result[service] = {
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "period_days": period_days,
                "period_start": period_start,
            }
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_defaults(self) -> None:
        """Seed the DB with default service definitions (idempotent)."""
        today = date.today().isoformat()
        for service, (limit, period_days) in _SERVICE_DEFAULTS.items():
            self._conn.execute(
                """
                INSERT OR IGNORE INTO service_quota
                    (service, used, period_limit, period_days, period_start)
                VALUES (?, 0, ?, ?, ?)
                """,
                (service, limit, period_days, today),
            )
        self._conn.commit()

    def _maybe_reset(self, service: str) -> None:
        """Reset usage counter if the current period has expired.

        Uses a Sliding Window strategy:
          if today - period_start >= period_days: reset used=0

        Complexity: O(1)
        """
        row = self._conn.execute(
            "SELECT period_start, period_days, period_limit FROM service_quota WHERE service=?",
            (service,),
        ).fetchone()
        if row is None:
            return
        period_start_str, period_days, limit = row
        if limit == -1:
            return  # unlimited — never reset needed

        period_start = date.fromisoformat(period_start_str)
        if date.today() >= period_start + timedelta(days=period_days):
            self._conn.execute(
                "UPDATE service_quota SET used=0, period_start=? WHERE service=?",
                (date.today().isoformat(), service),
            )
            self._conn.commit()
