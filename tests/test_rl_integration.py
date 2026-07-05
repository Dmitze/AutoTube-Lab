"""Integration tests for Phase 6 Reinforcement Learning loop.

Roadmap tasks: T-437 through T-440.
"""

from __future__ import annotations

import os
import time
import pytest
from pathlib import Path

from modules.adapters.synthetic import (
    InMemoryStorage,
    StubPublisher,
    SyntheticTrendSource,
)
from modules.orchestrator import Pipeline
from ytaimbot_ml.schemas import MetricsSnapshot


@pytest.fixture
def rl_pipeline(tmp_path):
    # Use synthetic adapters with niche keywords
    source = SyntheticTrendSource(seed=42)
    # Ensure some keywords match niches
    source._KEYWORDS[0] = "ghibli_asmr"
    source._KEYWORDS[1] = "hype_characters"
    source._KEYWORDS[2] = "ai_stories"
    
    storage = InMemoryStorage()
    for arm in ["ghibli_asmr", "hype_characters", "ai_stories"]:
        storage.upsert_niche_arm(arm, 0, 0.0, 0.0)
    publisher = StubPublisher()
    
    # Mock data dir
    os.environ["YTAIMBOT_DATA_DIR"] = str(tmp_path)
    os.environ["STORAGE_BACKEND"] = "in_memory"
    
    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
        publisher=publisher,
        dry_run=False, # Allow publishing to record transitions
        seed=42,
    )
    return pipeline, storage, publisher


def test_rl_niche_selection_and_feedback(rl_pipeline):
    """Test that bandit selects a niche and updates after feedback."""
    pipeline, storage, _ = rl_pipeline
    
    # 1. First run: should select first niche (cold start)
    niche1 = pipeline.orchestrator.niche_bandit.select()
    result1 = pipeline.run(run_id="run-1")
    assert result1.status == "ok"
    
    # 2. Simulate feedback
    # Add a published video record to storage (3 days ago)
    ago_3d = time.time() - (3 * 24 * 3600)
    storage.save_video(video_id="run-1-video", trend_id=niche1, title="Test", published_at=ago_3d)
    # Simulate high reward
    snapshot = MetricsSnapshot(video_id="run-1-video", views=5000, ctr=0.1, retention_30s=0.8)
    storage.save_metrics(snapshot)
    
    # 3. Second run: should run feedback loop and update bandit
    result2 = pipeline.run(run_id="run-2")
    assert result2.status == "ok"
    
    # Check that bandit was updated
    stats = pipeline.orchestrator.niche_bandit.stats["ghibli_asmr"]
    # Depending on how many videos were "published" in run-1
    # In our stub, all approved plans are published. Pipeline._TOP_N = 5.
    assert stats.n_pulls > 0


def test_ppo_transition_and_update(rl_pipeline):
    """Test that PPO transitions are saved and updated."""
    pipeline, storage, _ = rl_pipeline
    
    # 1. Run pipeline to save transition
    pipeline.run(run_id="run-ppo")
    
    # Check if transition was saved
    transitions = storage.load_ppo_transitions()
    assert len(transitions) > 0
    
    # 2. Simulate metrics for the published video (3 days ago)
    video_id = transitions[0]["video_id"]
    ago_3d = time.time() - (3 * 24 * 3600)
    storage.save_video(video_id=video_id, trend_id="niche", title="Test", published_at=ago_3d)
    snapshot = MetricsSnapshot(video_id=video_id, views=1000, ctr=0.05, retention_30s=0.7)
    storage.save_metrics(snapshot)
    
    # 3. Run feedback loop directly to trigger PPO update
    pipeline.orchestrator.update_metrics()
    
    # Transitions should be cleared after update
    assert len(storage.load_ppo_transitions()) == 0


def test_drift_detection_resets_bandit(rl_pipeline):
    """Test that significant drift triggers bandit reset."""
    pipeline, storage, _ = rl_pipeline
    
    # 1. Populate storage with many videos to have enough rewards for drift check (3 days ago)
    ago_3d = time.time() - (3 * 24 * 3600)
    for i in range(20):
        vid = f"v{i}"
        storage.save_video(video_id=vid, trend_id="ghibli_asmr", title="Test", published_at=ago_3d)
        # Half low reward, half high reward -> drift!
        val = 0.1 if i < 10 else 0.9
        snapshot = MetricsSnapshot(video_id=vid, views=int(val*1000), ctr=val/10, retention_30s=val)
        storage.save_metrics(snapshot)
        
    # Set high pulls to verify reset
    pipeline.orchestrator.niche_bandit.update("ghibli_asmr", 0.5)
    assert pipeline.orchestrator.niche_bandit.total_pulls > 0
    
    # 2. Run pipeline: feedback loop should detect drift
    pipeline.orchestrator.drift_detector.threshold = 0.0001 # Force drift detection
    pipeline.run(run_id="run-drift")
    
    # Bandit should be reset
    assert pipeline.orchestrator.niche_bandit.total_pulls == 0
