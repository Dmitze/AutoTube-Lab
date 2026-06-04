import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import pytest

from modules.adapters.base import StorageAdapter
from modules.adapters.storage.sqlite import SQLiteStorage
from ytaimbot_ml.schemas import ComplianceReport, MetricsSnapshot, TrendSignal


class TestSQLiteStorage(TestCase):
    """Unit tests for the SQLiteStorage adapter."""

    def setUp(self) -> None:
        """Set up a temporary in-memory database for each test."""
        # Use an in-memory database for speed and isolation
        self.db_path = Path(":memory:")
        self.storage = SQLiteStorage(db_path=self.db_path)

    def tearDown(self) -> None:
        """Close the database connection after each test."""
        self.storage.close()

    def test_init_creates_tables(self) -> None:
        """Test that tables are created on initialization."""
        # Check if tables exist by querying sqlite_master
        cursor = self.storage._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = [row["name"] for row in cursor.fetchall()]

        expected_tables = [
            "pipeline_runs",
            "trend_signals",
            "compliance_reports",
            "published_videos",
            "metrics",
            "ab_tests",
            "audit_log",
            "characters",
            "niche_arms",
            "niche_weights",
            "ppo_transitions",
        ]
        for table in expected_tables:
            self.assertIn(table, tables)

    def test_save_and_load_run(self) -> None:
        """Test saving and loading a pipeline run."""
        run_id = "test-run-123"
        status = "ok"
        self.storage.save_run(run_id, status)

        loaded_run = self.storage.load_run(run_id)
        self.assertIsNotNone(loaded_run)
        self.assertEqual(loaded_run["run_id"], run_id)
        self.assertEqual(loaded_run["status"], status)
        self.assertIn("timestamp", loaded_run)
        self.assertIsNone(loaded_run["result_json"])

    def test_load_nonexistent_run_returns_none(self) -> None:
        """Test loading a non-existent run."""
        loaded_run = self.storage.load_run("nonexistent-run")
        self.assertIsNone(loaded_run)

    def test_list_runs(self) -> None:
        """Test listing multiple pipeline runs."""
        self.storage.save_run("run-001", "ok")
        self.storage.save_run("run-002", "error")
        self.storage.save_run("run-003", "pending")

        runs = self.storage.list_runs(limit=2)
        self.assertEqual(len(runs), 2)
        # Should be ordered by timestamp DESC
        self.assertEqual(runs[0]["run_id"], "run-003")
        self.assertEqual(runs[1]["run_id"], "run-002")

    def test_save_trends(self) -> None:
        """Test saving trend signals."""
        run_id = "trend-run-456"
        trends = [
            TrendSignal("t1", "keyword1", 0.8, "source1", "2024-01-01T00:00:00Z"),
            TrendSignal("t2", "keyword2", 0.9, "source2", "2024-01-01T01:00:00Z"),
        ]
        self.storage.save_trends(run_id, trends)

        # For trends, we don't have a direct load_trends method by run_id
        # In a real scenario, we'd query the table directly or add a load method
        cursor = self.storage._conn.execute(
            "SELECT COUNT(*) FROM trend_signals WHERE run_id = ?", (run_id,)
        )
        self.assertEqual(cursor.fetchone()[0], 2)

    def test_save_compliance(self) -> None:
        """Test saving compliance reports."""
        run_id = "compliance-run-789"
        reports = [
            ComplianceReport("h1", 0.1, 0.05, "pass", ["reason1"]),
            ComplianceReport("h2", 0.2, 0.10, "fail", ["reason2", "reason3"]),
        ]
        self.storage.save_compliance(run_id, reports)

        cursor = self.storage._conn.execute(
            "SELECT COUNT(*) FROM compliance_reports WHERE run_id = ?", (run_id,)
        )
        self.assertEqual(cursor.fetchone()[0], 2)
        cursor = self.storage._conn.execute(
            "SELECT reasons_json FROM compliance_reports WHERE content_hash = 'h2';"
        )
        self.assertEqual(json.loads(cursor.fetchone()[0]), ["reason2", "reason3"])

    def test_save_video(self) -> None:
        """Test saving a published video."""
        video_id = "test-video-abc"
        trend_id = "test-trend-xyz"
        title = "Test Video Title"
        privacy_status = "public"
        self.storage.save_video(video_id, trend_id, title, privacy_status)

        cursor = self.storage._conn.execute(
            "SELECT video_id, trend_id, title, privacy_status FROM published_videos WHERE video_id = ?",
            (video_id,),
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["video_id"], video_id)
        self.assertEqual(row["trend_id"], trend_id)
        self.assertEqual(row["title"], title)
        self.assertEqual(row["privacy_status"], privacy_status)

    def test_save_metrics(self) -> None:
        """Test saving video metrics snapshot."""
        video_id = "metric-video-123"
        metrics = MetricsSnapshot(video_id=video_id, views=100, ctr=0.05)
        self.storage.save_metrics(metrics)

        cursor = self.storage._conn.execute(
            "SELECT video_id, views, ctr FROM metrics WHERE video_id = ?", (video_id,)
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["video_id"], video_id)
        self.assertEqual(row["views"], 100)
        self.assertEqual(row["ctr"], 0.05)

    def test_get_upload_count(self) -> None:
        """Test getting the total upload count."""
        self.storage.save_video("v1", "t1", "Title 1")
        self.storage.save_video("v2", "t2", "Title 2")
        self.assertEqual(self.storage.get_upload_count(), 2)

    def test_list_published_videos(self) -> None:
        """Test listing published videos."""
        self.storage.save_video("v_old", "t_old", "Old Video") # This needs to be mocked to control time
        self.storage.save_video("v_new", "t_new", "New Video")
        videos = self.storage.list_published_videos(limit=1)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["video_id"], "v_new")

    @mock.patch("time.time", side_effect=[100, 200, 300]) # Mock time for consistent ordering
    def test_list_published_videos_order(self, mock_time) -> None:
        """Test listing published videos order by published_at DESC."""
        self.storage.save_video("v1", "t1", "Title 1")
        self.storage.save_video("v2", "t2", "Title 2")
        self.storage.save_video("v3", "t3", "Title 3")

        videos = self.storage.list_published_videos(limit=3)
        self.assertEqual(len(videos), 3)
        self.assertEqual(videos[0]["video_id"], "v3")
        self.assertEqual(videos[1]["video_id"], "v2")
        self.assertEqual(videos[2]["video_id"], "v1")

    def test_load_archive(self) -> None:
        """Test loading archived script texts (from compliance reports)."""
        run_id = "archive-run-1"
        reports = [
            ComplianceReport("hash1", 0.1, 0.05, "pass", ["script1_reason"]),
            ComplianceReport("hash2", 0.2, 0.10, "fail", ["script2_reason"]),
        ]
        self.storage.save_compliance(run_id, reports)

        archive = self.storage.load_archive()
        self.assertIn("hash1", archive)
        self.assertIn("hash2", archive)
        self.assertEqual(archive["hash1"], json.dumps(["script1_reason"]))

    def test_storage_adapter_inheritance(self) -> None:
        """Ensure SQLiteStorage correctly inherits from StorageAdapter."""
        self.assertIsInstance(self.storage, StorageAdapter)
        # Check that all abstract methods are implemented
        # This will raise TypeError if any abstract methods are not implemented
        try:
            StorageAdapter.register(SQLiteStorage)
        except TypeError as e:
            self.fail(f"SQLiteStorage does not implement all abstract methods: {e}")

    # Test cases for other methods like save_character, load_characters,
    # upsert_niche_arm, load_niche_arms, etc. would go here.

    def test_db_path_resolution(self) -> None:
        """Test default db path resolution from environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_data_dir = Path(tmpdir) / "test_data"
            os.environ["YTAIMBOT_DATA_DIR"] = str(temp_data_dir)

            try:
                storage = SQLiteStorage()
                expected_path = temp_data_dir / "db" / "ytaimbot.db"
                self.assertEqual(storage._db_path, expected_path)
                self.assertTrue(expected_path.parent.exists())
            finally:
                del os.environ["YTAIMBOT_DATA_DIR"]
                storage.close()

    def test_db_path_explicit(self) -> None:
        """Test explicit db path takes precedence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            explicit_path = Path(tmpdir) / "explicit.db"
            storage = SQLiteStorage(db_path=explicit_path)
            self.assertEqual(storage._db_path, explicit_path)
            self.assertTrue(explicit_path.parent.exists())
            storage.close()

    def test_thread_safety(self) -> None:
        """Test basic thread safety for write operations."""
        import threading

        def writer_func(run_id_prefix: str, count: int) -> None:
            for i in range(count):
                self.storage.save_run(f"{run_id_prefix}-{i}", "status")

        threads = []
        num_threads = 5
        runs_per_thread = 10
        for i in range(num_threads):
            thread = threading.Thread(
                target=writer_func, args=(f"thread-{i}", runs_per_thread)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        expected_total_runs = num_threads * runs_per_thread
        # Use an explicit query to count, as list_runs has a limit
        cursor = self.storage._conn.execute("SELECT COUNT(*) FROM pipeline_runs")
        self.assertEqual(cursor.fetchone()[0], expected_total_runs)

    def test_save_ppo_transition_and_load_ppo_transitions(self) -> None:
        """Test saving and loading PPO transitions."""
        video_id = "ppo-video-1"
        state = [0.1, 0.2, 0.3]
        action_idx = 0
        prob = 0.99

        self.storage.save_ppo_transition(video_id, state, action_idx, prob)
        transitions = self.storage.load_ppo_transitions()

        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["video_id"], video_id)
        self.assertEqual(json.loads(transitions[0]["state_json"]), state)
        self.assertEqual(transitions[0]["action_idx"], action_idx)
        self.assertEqual(transitions[0]["prob"], prob)

    def test_clear_ppo_transitions(self) -> None:
        """Test clearing PPO transitions."""
        self.storage.save_ppo_transition("ppo-video-2", [0.4, 0.5], 1, 0.8)
        self.storage.clear_ppo_transitions()
        transitions = self.storage.load_ppo_transitions()
        self.assertEqual(len(transitions), 0)

    @mock.patch("time.time", return_value=12345.0)
    def test_save_bandit_state_and_load_bandit_state(self, mock_time) -> None:
        """Test saving and loading bandit state."""
        arm_id = "test_arm"
        n_pulls = 10
        total_reward = 5.5
        last_reward = 0.7

        self.storage.save_bandit_state(arm_id, n_pulls, total_reward, last_reward)
        bandit_state = self.storage.load_bandit_state()

        self.assertIn(arm_id, bandit_state)
        self.assertEqual(bandit_state[arm_id]["n_pulls"], n_pulls)
        self.assertEqual(bandit_state[arm_id]["total_reward"], total_reward)
        self.assertEqual(bandit_state[arm_id]["last_reward"], last_reward)
        self.assertEqual(bandit_state[arm_id]["updated_at"], 12345.0)

    @mock.patch("time.time", return_value=100)
    def test_save_niche_weights_and_load_niche_weights(self, mock_time) -> None:
        """Test saving and loading niche weights."""
        weights = {"niche1": 0.5, "niche2": 0.8}
        self.storage.save_niche_weights(weights)

        loaded_weights = self.storage.load_niche_weights()
        self.assertEqual(loaded_weights, weights)

        # Update and check
        updated_weights = {"niche1": 0.6, "niche3": 0.9}
        self.storage.save_niche_weights(updated_weights)
        loaded_weights = self.storage.load_niche_weights()
        self.assertIn("niche1", loaded_weights)
        self.assertEqual(loaded_weights["niche1"], 0.6)
        self.assertIn("niche3", loaded_weights)
        self.assertEqual(loaded_weights["niche3"], 0.9)
        self.assertIn("niche2", loaded_weights)  # niche2 should still be present
        self.assertEqual(loaded_weights["niche2"], 0.8)  # its value should be unchanged from the first save
