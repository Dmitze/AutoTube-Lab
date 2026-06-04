import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import pytest

from modules.adapters.base import (
    ComplianceReport,
    ContentPlan,
    PublisherAdapter,
    StorageAdapter,
    TrendSignal,
    TrendSourceAdapter,
)
from ytaimbot_ml.schemas import Script, VideoAsset
from modules.adapters.storage.sqlite import SQLiteStorage
from modules.orchestrator import YTAIMBotOrchestrator


class MockTrendSource(TrendSourceAdapter):
    def fetch(self) -> list[TrendSignal]:
        return [
            TrendSignal(
                trend_id="trend-1",
                keyword="test keyword",
                raw_score=0.7,
                source="mock",
                timestamp="2024-01-01T00:00:00Z",
            )
        ]


class MockScriptGenerator:
    def generate_script(self, plan: ContentPlan) -> Script:
        return Script(
            plan_id=plan.trend_id,
            sections=[
                {"name": "hook", "text": "Mock hook."},
                {"name": "body", "text": "Mock body."},
            ],
        )


class MockVideoAssembler:
    def assemble_video(self, script: Script) -> VideoAsset:
        return VideoAsset(
            plan_id=script.plan_id,
            video_path="/tmp/mock_video.mp4",
            thumbnail_path="/tmp/mock_thumbnail.png",
        )


class MockPublisher(PublisherAdapter):
    def publish(self, plan: ContentPlan, compliance_report: ComplianceReport) -> bool:
        return True


class MockComplianceChecker:
    def check(self, script: Script) -> ComplianceReport:
        return ComplianceReport(
            content_hash="mock-hash",
            similarity_score=0.1,
            bayes_p_bad=0.01,
            decision="pass",
            reasons=[],
        )


class TestOrchestratorPersistence(TestCase):
    """Integration tests for Orchestrator's interaction with StorageAdapter."""

    def setUp(self) -> None:
        """Set up a temporary file-based SQLite database for integration tests."""
        # Use a temporary file for the database to simulate real file system
        self.temp_db_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_db_dir.name) / "test_ytaimbot.db"
        self.storage = SQLiteStorage(db_path=self.db_path)

        # Mock other Orchestrator dependencies
        self.mock_trend_source = MockTrendSource()
        self.mock_script_generator = MockScriptGenerator()
        self.mock_video_assembler = MockVideoAssembler()
        self.mock_publisher = MockPublisher()
        self.mock_compliance_checker = MockComplianceChecker()
        self.mock_config = {}  # Empty config for now
        self.mock_rng = mock.Mock()  # Mock random number generator

        # Seed niche arms to avoid UCB1Bandit initialization failure
        self.storage.upsert_niche_arm("test_niche", 0, 0.0, 0.0)

        self.orchestrator = YTAIMBotOrchestrator(
            trend_source=self.mock_trend_source,
            script_generator=self.mock_script_generator,
            video_assembler=self.mock_video_assembler,
            publisher=self.mock_publisher,
            storage=self.storage,
            compliance_checker=self.mock_compliance_checker,
            config=self.mock_config,
            rng=self.mock_rng,
        )

    def tearDown(self) -> None:
        """Close the database connection and clean up temporary files."""
        self.storage.close()
        self.temp_db_dir.cleanup()

    @mock.patch("time.time", side_effect=[100, 200, 300])  # For save_run timestamps
    def test_run_pipeline_persists_data(self, mock_time) -> None:
        """Test that running the pipeline persists run status, trends, and compliance reports."""
        run_id = "integration-test-run-1"
        self.orchestrator.run_pipeline(run_id)

        # Verify run status persistence
        loaded_run = self.storage.load_run(run_id)
        self.assertIsNotNone(loaded_run)
        self.assertEqual(loaded_run["run_id"], run_id)
        self.assertEqual(loaded_run["status"], "ok")
        self.assertAlmostEqual(loaded_run["timestamp"], 300) # Last save_run call

        # Verify trend signals persistence
        cursor = self.storage._conn.execute(
            "SELECT COUNT(*) FROM trend_signals WHERE run_id = ?", (run_id,)
        )
        self.assertEqual(cursor.fetchone()[0], 1)

        # Verify compliance reports persistence
        cursor = self.storage._conn.execute(
            "SELECT COUNT(*) FROM compliance_reports WHERE run_id = ?", (run_id,)
        )
        self.assertEqual(cursor.fetchone()[0], 1)
        
        # Verify video persistence (if publish is called and successful)
        uploaded_videos = self.storage.list_published_videos()
        self.assertEqual(len(uploaded_videos), 1)
        self.assertEqual(uploaded_videos[0]["video_id"], "mock-hash") # Assuming content_hash from mock compliance becomes video_id
