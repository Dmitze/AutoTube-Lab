"""Phase 5 — SQLiteStorage: persistent storage adapter using SQLite.

Roadmap tasks: T-431 through T-445 (EPIC 5.3 Persistent Storage)
Depends on:   sqlite3 (stdlib), StorageAdapter ABC

Configuration
-------------
YTAIMBOT_DATA_DIR : base data directory (default: ./data)
DB path           : {YTAIMBOT_DATA_DIR}/db/ytaimbot.db

Algorithm
---------
WAL mode enables concurrent reads + single-writer with low-latency commits:

  PRAGMA journal_mode=WAL      → O(1) setup, enables concurrent readers
  PRAGMA synchronous=NORMAL    → balance durability / write throughput

  save_run()              : INSERT OR REPLACE → O(log n) B-tree index
  save_trends()           : executemany INSERT → O(k log n), k = batch size
  save_compliance()       : executemany INSERT → O(k log n)
  load_run()              : SELECT by PK       → O(log n)
  list_runs()             : SELECT ORDER BY ts DESC LIMIT L → O(L log n)
  save_video()            : INSERT OR REPLACE → O(log n)
  update_video_metrics()  : UPDATE by PK       → O(log n)
  save_character()        : INSERT OR REPLACE → O(log n)
  load_characters()       : SELECT WHERE channel_id (indexed) → O(log n + r)
  upsert_niche_arm()      : INSERT OR REPLACE → O(log n)
  load_niche_arms()       : full table scan → O(n) (small table expected)
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from modules.adapters.base import StorageAdapter
from ytaimbot_ml.schemas import (
    ChannelStats,
    ComplianceReport,
    ContentPlan,
    PipelineResult,
    TrendSignal,
)

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id      TEXT PRIMARY KEY,
    status      TEXT NOT NULL,
    timestamp   REAL NOT NULL,
    result_json TEXT DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_ts ON pipeline_runs(timestamp);

CREATE TABLE IF NOT EXISTS trend_signals (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           TEXT NOT NULL,
    trend_id         TEXT NOT NULL,
    keyword          TEXT NOT NULL,
    raw_score        REAL NOT NULL,
    source           TEXT NOT NULL,
    signal_timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS compliance_reports (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           TEXT NOT NULL,
    content_hash     TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    bayes_p_bad      REAL NOT NULL,
    decision         TEXT NOT NULL,
    reasons_json     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS published_videos (
    video_id       TEXT PRIMARY KEY,
    trend_id       TEXT NOT NULL,
    title          TEXT NOT NULL,
    published_at   REAL NOT NULL,
    ctr            REAL DEFAULT 0.0,
    retention_30s  REAL DEFAULT 0.0,
    views          INTEGER DEFAULT 0,
    privacy_status TEXT DEFAULT 'unlisted'
);

CREATE TABLE IF NOT EXISTS characters (
    char_id     TEXT PRIMARY KEY,
    channel_id  TEXT NOT NULL,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chars_channel ON characters(channel_id);

CREATE TABLE IF NOT EXISTS niche_arms (
    arm_id       TEXT PRIMARY KEY,
    n_pulls      INTEGER DEFAULT 0,
    total_reward REAL    DEFAULT 0.0,
    last_reward  REAL    DEFAULT 0.0,
    updated_at   REAL    NOT NULL
);
"""


class SQLiteStorage(StorageAdapter):
    """SQLite-backed persistent storage adapter for the YTAIMBot pipeline.

    Uses Write-Ahead Logging (WAL) for concurrent read access and
    ``PRAGMA synchronous=NORMAL`` for a balanced durability/throughput
    trade-off appropriate for a single-machine deployment.

    All write operations are protected by a ``threading.Lock`` so the same
    instance can be shared safely across threads (e.g. pipeline + analytics
    background worker).

    Configuration
    -------------
    db_path
        Explicit filesystem path.  If ``None``, the path is resolved from:
        ``Path(os.getenv("YTAIMBOT_DATA_DIR", "./data")) / "db" / "ytaimbot.db"``

    Parameters
    ----------
    db_path:
        Optional explicit path to the ``.db`` file.  Parent directories are
        created automatically.

    Examples
    --------
    >>> from modules.adapters.storage.sqlite import SQLiteStorage
    >>> store = SQLiteStorage()                          # uses env/default path
    >>> store.save_run("run-001", "ok")
    >>> store.load_run("run-001")
    {'run_id': 'run-001', 'status': 'ok', ...}
    >>> store.list_runs(limit=5)
    [{'run_id': 'run-001', ...}]
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialise the SQLite connection and create schema if needed.

        Complexity: O(t) where t = number of DDL statements (~8).

        Parameters
        ----------
        db_path:
            Path to the SQLite database file.  When ``None`` the default path
            ``$YTAIMBOT_DATA_DIR/db/ytaimbot.db`` is used.
        """
        if db_path is None:
            data_dir = Path(os.getenv("YTAIMBOT_DATA_DIR", "./data"))
            db_path = data_dir / "db" / "ytaimbot.db"

        self._db_path: Path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        _log.info("SQLiteStorage: opening database at %s", self._db_path)

        self._conn: sqlite3.Connection = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row

        self._lock: threading.Lock = threading.Lock()

        self._configure_pragmas()
        self._create_tables()

        _log.info("SQLiteStorage: ready (WAL mode, schema verified)")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _configure_pragmas(self) -> None:
        """Apply WAL journal mode and NORMAL synchronous setting.

        Complexity: O(1)
        """
        with self._conn:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        _log.debug("SQLiteStorage: WAL + synchronous=NORMAL applied")

    def _create_tables(self) -> None:
        """Execute DDL to create tables and indexes if they do not exist.

        Complexity: O(t) where t = number of DDL statements.
        """
        with self._lock:
            with self._conn:
                self._conn.executescript(_DDL)
        _log.debug("SQLiteStorage: schema initialised")

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        """Convert a ``sqlite3.Row`` to a plain ``dict``, or return ``None``.

        Complexity: O(c) where c = number of columns.
        """
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # StorageAdapter ABC — required methods
    # ------------------------------------------------------------------

    def save_run(self, run_id: str, status: str) -> None:
        """Insert or replace a pipeline run record.

        Uses the current wall-clock time (``time.time()``) as the timestamp
        so that ``list_runs`` can order by recency.

        Complexity: O(log n) — B-tree INSERT OR REPLACE on primary key.

        Parameters
        ----------
        run_id:
            Unique identifier for this pipeline run (UUID recommended).
        status:
            Terminal status string: ``"ok"``, ``"blocked"``, or ``"error"``.

        Examples
        --------
        >>> store.save_run("run-abc", "ok")
        """
        _log.debug("save_run: run_id=%s status=%s", run_id, status)
        try:
            with self._lock:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT OR REPLACE INTO pipeline_runs
                            (run_id, status, timestamp)
                        VALUES (?, ?, ?)
                        """,
                        (run_id, status, time.time()),
                    )
        except sqlite3.Error:
            _log.exception("save_run failed for run_id=%s", run_id)
            raise

    def save_trends(self, run_id: str, trends: list[TrendSignal]) -> None:
        """Batch-insert trend signals associated with a pipeline run.

        Existing rows for this ``run_id`` are NOT deleted first; repeated
        calls append additional rows (idempotency is the caller's concern).

        Complexity: O(k log n) where k = ``len(trends)``.

        Parameters
        ----------
        run_id:
            Pipeline run identifier; foreign-key reference to
            ``pipeline_runs.run_id``.
        trends:
            List of ``TrendSignal`` dataclass instances to persist.

        Examples
        --------
        >>> from ytaimbot_ml.schemas import TrendSignal
        >>> signals = [TrendSignal("t1", "python", 0.9, "google", "2024-01-01T00:00:00Z")]
        >>> store.save_trends("run-abc", signals)
        """
        if not trends:
            _log.debug("save_trends: empty list, nothing to insert (run_id=%s)", run_id)
            return
        _log.debug("save_trends: inserting %d signals for run_id=%s", len(trends), run_id)
        rows = [
            (run_id, t.trend_id, t.keyword, t.raw_score, t.source, t.timestamp)
            for t in trends
        ]
        try:
            with self._lock:
                with self._conn:
                    self._conn.executemany(
                        """
                        INSERT INTO trend_signals
                            (run_id, trend_id, keyword, raw_score, source, signal_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        rows,
                    )
        except sqlite3.Error:
            _log.exception("save_trends failed for run_id=%s", run_id)
            raise

    def save_compliance(
        self, run_id: str, reports: list[ComplianceReport]
    ) -> None:
        """Batch-insert compliance reports associated with a pipeline run.

        Complexity: O(k log n) where k = ``len(reports)``.

        Parameters
        ----------
        run_id:
            Pipeline run identifier.
        reports:
            List of ``ComplianceReport`` dataclass instances to persist.

        Examples
        --------
        >>> from ytaimbot_ml.schemas import ComplianceReport
        >>> rpt = ComplianceReport("h1", 0.1, 0.05, "pass", [])
        >>> store.save_compliance("run-abc", [rpt])
        """
        if not reports:
            _log.debug(
                "save_compliance: empty list, nothing to insert (run_id=%s)", run_id
            )
            return
        _log.debug(
            "save_compliance: inserting %d reports for run_id=%s", len(reports), run_id
        )
        rows = [
            (
                run_id,
                r.content_hash,
                r.similarity_score,
                r.bayes_p_bad,
                r.decision,
                json.dumps(r.reasons),
            )
            for r in reports
        ]
        try:
            with self._lock:
                with self._conn:
                    self._conn.executemany(
                        """
                        INSERT INTO compliance_reports
                            (run_id, content_hash, similarity_score,
                             bayes_p_bad, decision, reasons_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        rows,
                    )
        except sqlite3.Error:
            _log.exception("save_compliance failed for run_id=%s", run_id)
            raise

    # ------------------------------------------------------------------
    # Additional read/write methods
    # ------------------------------------------------------------------

    def load_run(self, run_id: str) -> dict[str, Any] | None:
        """Fetch a single pipeline run record by primary key.

        Complexity: O(log n) — B-tree seek on primary key.

        Parameters
        ----------
        run_id:
            The pipeline run identifier to look up.

        Returns
        -------
        dict | None
            A dict with keys ``run_id``, ``status``, ``timestamp``,
            ``result_json`` on success, or ``None`` if not found.

        Examples
        --------
        >>> store.save_run("run-abc", "ok")
        >>> row = store.load_run("run-abc")
        >>> row["status"]
        'ok'
        >>> store.load_run("nonexistent") is None
        True
        """
        _log.debug("load_run: run_id=%s", run_id)
        try:
            cur = self._conn.execute(
                "SELECT run_id, status, timestamp, result_json "
                "FROM pipeline_runs WHERE run_id = ?",
                (run_id,),
            )
            return self._row_to_dict(cur.fetchone())
        except sqlite3.Error:
            _log.exception("load_run failed for run_id=%s", run_id)
            raise

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent pipeline run records ordered by timestamp descending.

        Complexity: O(L log n) where L = ``limit`` and n = total run count.

        Parameters
        ----------
        limit:
            Maximum number of records to return.  Defaults to ``50``.

        Returns
        -------
        list[dict]
            Each dict contains ``run_id``, ``status``, ``timestamp``,
            ``result_json``.  Empty list when no runs exist.

        Examples
        --------
        >>> store.save_run("run-001", "ok")
        >>> store.save_run("run-002", "error")
        >>> runs = store.list_runs(limit=10)
        >>> runs[0]["run_id"]  # most recent first
        'run-002'
        """
        _log.debug("list_runs: limit=%d", limit)
        try:
            cur = self._conn.execute(
                "SELECT run_id, status, timestamp, result_json "
                "FROM pipeline_runs ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            _log.exception("list_runs failed")
            raise

    def save_video(
        self,
        video_id: str,
        trend_id: str,
        title: str,
        privacy_status: str = "unlisted",
    ) -> None:
        """Insert or replace a published video record.

        Sets ``published_at`` to the current wall-clock time.  Metric fields
        (``ctr``, ``retention_30s``, ``views``) default to ``0`` and can be
        updated later via :meth:`update_video_metrics`.

        Complexity: O(log n) — B-tree INSERT OR REPLACE on primary key.

        Parameters
        ----------
        video_id:
            YouTube video ID (e.g. ``"dQw4w9WgXcQ"``).
        trend_id:
            Originating trend ID from the pipeline.
        title:
            Video title string.
        privacy_status:
            YouTube privacy status; one of ``"private"``, ``"unlisted"``,
            ``"public"``.  Defaults to ``"unlisted"``.

        Examples
        --------
        >>> store.save_video("dQw4w9WgXcQ", "t1", "Never Gonna Give You Up")
        """
        _log.debug("save_video: video_id=%s trend_id=%s", video_id, trend_id)
        try:
            with self._lock:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT OR REPLACE INTO published_videos
                            (video_id, trend_id, title, published_at, privacy_status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (video_id, trend_id, title, time.time(), privacy_status),
                    )
        except sqlite3.Error:
            _log.exception("save_video failed for video_id=%s", video_id)
            raise

    def update_video_metrics(self, video_id: str, stats: ChannelStats) -> None:
        """Update CTR, 30-second retention, and view count for a video.

        No-op (with a WARNING log) if ``video_id`` does not exist.

        Complexity: O(log n) — B-tree UPDATE on primary key.

        Parameters
        ----------
        video_id:
            YouTube video ID to update.
        stats:
            A ``ChannelStats`` instance with ``ctr``, ``retention_30s``,
            and ``views`` populated.

        Examples
        --------
        >>> from ytaimbot_ml.schemas import ChannelStats
        >>> s = ChannelStats(video_id="abc", views=500, ctr=0.07, retention_30s=0.75)
        >>> store.update_video_metrics("abc", s)
        """
        _log.debug(
            "update_video_metrics: video_id=%s ctr=%.4f retention=%.4f views=%d",
            video_id,
            stats.ctr,
            stats.retention_30s,
            stats.views,
        )
        try:
            with self._lock:
                with self._conn:
                    cur = self._conn.execute(
                        """
                        UPDATE published_videos
                        SET ctr = ?, retention_30s = ?, views = ?
                        WHERE video_id = ?
                        """,
                        (stats.ctr, stats.retention_30s, stats.views, video_id),
                    )
            if cur.rowcount == 0:
                _log.warning(
                    "update_video_metrics: video_id=%s not found, skipping", video_id
                )
        except sqlite3.Error:
            _log.exception("update_video_metrics failed for video_id=%s", video_id)
            raise

    def save_character(
        self,
        char_id: str,
        channel_id: str,
        name: str,
        description: str,
    ) -> None:
        """Insert or replace a channel character (persona) record.

        Sets ``created_at`` to the current wall-clock time on first insert.
        A replace preserves the original ``created_at`` only if the caller
        manages that separately; here it is always set to ``time.time()``.

        Complexity: O(log n) — B-tree INSERT OR REPLACE on primary key.

        Parameters
        ----------
        char_id:
            Unique character identifier (UUID recommended).
        channel_id:
            YouTube channel ID this character belongs to.
        name:
            Display name of the character/persona.
        description:
            Textual description used by the ScriptGenerator for tone/style.

        Examples
        --------
        >>> store.save_character("c-001", "UC123", "TechBot", "A friendly tech explainer")
        """
        _log.debug(
            "save_character: char_id=%s channel_id=%s name=%s", char_id, channel_id, name
        )
        try:
            with self._lock:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT OR REPLACE INTO characters
                            (char_id, channel_id, name, description, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (char_id, channel_id, name, description, time.time()),
                    )
        except sqlite3.Error:
            _log.exception("save_character failed for char_id=%s", char_id)
            raise

    def load_characters(self, channel_id: str) -> list[dict[str, Any]]:
        """Return all characters belonging to a channel, ordered by creation time.

        Uses the ``idx_chars_channel`` index for efficient lookup.

        Complexity: O(log n + r) where r = number of matching characters.

        Parameters
        ----------
        channel_id:
            The YouTube channel ID to filter by.

        Returns
        -------
        list[dict]
            Each dict contains ``char_id``, ``channel_id``, ``name``,
            ``description``, ``created_at``.  Empty list if none found.

        Examples
        --------
        >>> store.save_character("c-001", "UC123", "TechBot", "Friendly explainer")
        >>> chars = store.load_characters("UC123")
        >>> chars[0]["name"]
        'TechBot'
        """
        _log.debug("load_characters: channel_id=%s", channel_id)
        try:
            cur = self._conn.execute(
                "SELECT char_id, channel_id, name, description, created_at "
                "FROM characters WHERE channel_id = ? ORDER BY created_at ASC",
                (channel_id,),
            )
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            _log.exception("load_characters failed for channel_id=%s", channel_id)
            raise

    def upsert_niche_arm(
        self,
        arm_id: str,
        n_pulls: int,
        total_reward: float,
        last_reward: float,
    ) -> None:
        """Insert or replace a UCB1 bandit arm state for niche selection.

        Sets ``updated_at`` to the current wall-clock time.

        Complexity: O(log n) — B-tree INSERT OR REPLACE on primary key.

        Parameters
        ----------
        arm_id:
            Unique identifier for the niche/arm (e.g. ``"python_tutorials"``).
        n_pulls:
            Total number of times this arm has been selected.
        total_reward:
            Cumulative reward signal (e.g. sum of CTR values).
        last_reward:
            Most recent observed reward value.

        Examples
        --------
        >>> store.upsert_niche_arm("python_tutorials", 10, 0.72, 0.08)
        """
        _log.debug(
            "upsert_niche_arm: arm_id=%s n_pulls=%d total_reward=%.4f last_reward=%.4f",
            arm_id,
            n_pulls,
            total_reward,
            last_reward,
        )
        try:
            with self._lock:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT OR REPLACE INTO niche_arms
                            (arm_id, n_pulls, total_reward, last_reward, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (arm_id, n_pulls, total_reward, last_reward, time.time()),
                    )
        except sqlite3.Error:
            _log.exception("upsert_niche_arm failed for arm_id=%s", arm_id)
            raise

    def load_niche_arms(self) -> list[dict[str, Any]]:
        """Return all niche bandit arm states for UCB1 initialisation.

        Complexity: O(n) — full table scan (table is expected to be small,
        bounded by the number of distinct niches, typically < 50).

        Returns
        -------
        list[dict]
            Each dict contains ``arm_id``, ``n_pulls``, ``total_reward``,
            ``last_reward``, ``updated_at``.  Empty list if table is empty.

        Examples
        --------
        >>> store.upsert_niche_arm("python_tutorials", 10, 0.72, 0.08)
        >>> arms = store.load_niche_arms()
        >>> arms[0]["arm_id"]
        'python_tutorials'
        """
        _log.debug("load_niche_arms: fetching all arms")
        try:
            cur = self._conn.execute(
                "SELECT arm_id, n_pulls, total_reward, last_reward, updated_at "
                "FROM niche_arms ORDER BY arm_id ASC"
            )
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            _log.exception("load_niche_arms failed")
            raise

    # ------------------------------------------------------------------
    # Resource management
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying SQLite connection gracefully.

        Safe to call multiple times — subsequent calls are no-ops.

        Complexity: O(1)

        Examples
        --------
        >>> store.close()
        """
        try:
            self._conn.close()
            _log.info("SQLiteStorage: connection closed")
        except sqlite3.Error:
            _log.exception("SQLiteStorage: error closing connection")

    def __enter__(self) -> "SQLiteStorage":
        """Support use as a context manager.

        Examples
        --------
        >>> with SQLiteStorage() as store:
        ...     store.save_run("run-ctx", "ok")
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close connection on context manager exit.

        Complexity: O(1)
        """
        self.close()

    def __repr__(self) -> str:
        """Return a developer-friendly string representation.

        Complexity: O(1)
        """
        return f"SQLiteStorage(db_path={self._db_path!r})"
