from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

import numpy as np

from modules.adapters.base import (
    ComplianceReport,
    ContentPlan,
    PublisherAdapter,
    StorageAdapter,
    TrendSignal,
    TrendSourceAdapter,
)
from modules.adapters.llm import build_llm_adapter
from modules.adapters.tts import build_tts_adapter
from modules.adapters.video import create_video_backend
# from modules.metrics_collector import MetricsRegistry # Removed line
from modules.adapters.retry import exponential_backoff # Modified line
from ytaimbot_ml.quality import BayesQualityFilter, KSDriftDetector, SimilarityGate
from ytaimbot_ml.rl import LinearPPO, RewardShaper, UCB1Bandit
from ytaimbot_ml.schemas import (
    ContentAction,
    ContentState,
    PipelineResult,
    Script,
    TrendRanking,
    MetricsSnapshot # Added
)
# from ytaimbot_ml.seo import TrendAnalyzer # Removed
from ytaimbot_ml.utils import make_rng
from ytaimbot_ml.utils.metrics import MetricsRegistry # Added line
from ytaimbot_ml.trend_analyzer import TrendAnalyzer # Added

if TYPE_CHECKING:
    # Avoid circular imports for type hinting
    from modules.adapters.llm import LLMAdapter
    from modules.adapters.tts import TTSAdapter
    from modules.adapters.video import VideoAssembler


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dependency Factories (hide complexity of building concrete adapters)
# ---------------------------------------------------------------------------


def build_trend_source(config: dict[str, Any]) -> TrendSourceAdapter:
    """Build the best available trend source adapter.

    Delegates selection to `modules.adapters.trend.build_trend_source`, which
    orchestrates a chain of priority: `CompositeTrendSource` (YouTube + Google
    Trends) -> `GoogleTrendsAdapter` -> `YouTubeSearchAdapter` -> `SyntheticTrendSource`.

    Parameters
    ----------
    config:
        Application configuration dictionary (e.g. from environment variables).

    Returns
    -------
    TrendSourceAdapter
        Configured trend source adapter.

    Examples
    --------
    >>> source = build_trend_source({})
    >>> isinstance(source, TrendSourceAdapter)
    True
    """
    from modules.adapters.trend import build_trend_source as _build

    return _build(config)


def build_storage(config: dict[str, Any]) -> StorageAdapter:
    """Build the best available persistent storage adapter.

    Currently only SQLite is implemented.

    Parameters
    ----------
    config:
        Application configuration dictionary.

    Returns
    -------
    StorageAdapter
        Configured storage adapter.

    Examples
    --------
    >>> store = build_storage({})
    >>> isinstance(store, StorageAdapter)
    True
    """
    from modules.adapters.storage.sqlite import SQLiteStorage

    db_path = config.get("DB_PATH")
    return SQLiteStorage(db_path=Path(db_path) if db_path else None)


def build_youtube_uploader(config: dict[str, Any]) -> PublisherAdapter:
    """Build the YouTube publisher adapter.

    Delegates to ``modules.adapters.publisher.build_youtube_uploader`` which
    requires OAuth2 credentials.

    Parameters
    ----------
    config:
        Application configuration dictionary.

    Returns
    -------
    PublisherAdapter
        Configured YouTube publisher adapter.

    Examples
    --------
    >>> publisher = build_youtube_uploader({})
    >>> isinstance(publisher, PublisherAdapter)
    True
    """
    from modules.adapters.publisher import build_youtube_uploader as _build

    return _build(config)


def build_manual_reviewer(config: dict[str, Any]) -> PublisherAdapter:
    """Builds a "manual review" publisher that just saves artefacts.

    This can be used in dry-run mode or when human oversight is required
    before publishing.

    Parameters
    ----------
    config:
        Application configuration dictionary.

    Returns
    -------
    PublisherAdapter
        Configured manual reviewer adapter.

    Examples
    --------
    >>> reviewer = build_manual_reviewer({})
    >>> isinstance(reviewer, PublisherAdapter)
    True
    """
    from modules.adapters.publisher import build_manual_reviewer as _build

    return _build(config)


def build_metrics_collector(config: dict[str, Any]) -> MetricsRegistry:
    """Build metrics collector.

    Parameters
    ----------
    config:
        Application configuration dictionary.

    Returns
    -------
    MetricsRegistry
        Configured metrics registry.

    Examples
    --------
    >>> metrics = build_metrics_collector({})
    >>> isinstance(metrics, MetricsRegistry)
    True
    """
    return MetricsRegistry()


def build_llm_adapter() -> Optional[LLMAdapter]:
    """Build the best available free-tier LLM adapter.

    Delegates selection to ``modules.adapters.llm.build_llm_adapter`` which
    prefers ``GroqAdapter`` and degrades to ``OllamaAdapter`` (if available).

    Returns
    -------
    LLMAdapter | None
        Configured adapter, or None if no LLM backend is available.

    Examples
    --------
    >>> adapter = build_llm_adapter()
    >>> adapter is None or hasattr(adapter, 'generate')
    True
    """
    try:
        from modules.adapters.llm import build_llm_adapter as _build
        return _build()
    except RuntimeError:
        logger.info("LLM: no adapter configured — script generation disabled")
        return None


def build_tts_adapter() -> Optional[TTSAdapter]:
    """Build best available free-tier TTS adapter.

    Delegates selection to ``modules.adapters.tts.build_tts_adapter`` which
    prefers ``FreeTierTTSChain`` (auto-fallback on quota/service errors) and
    degrades to ``EdgeTTSAdapter`` when chain construction is unavailable.

    Returns
    -------
    TTSAdapter | None
        Configured adapter, or None if no TTS backend is available.

    Complexity
    ----------
    O(1)

    Examples
    --------
    >>> adapter = build_tts_adapter()
    >>> adapter is None or hasattr(adapter, 'speak')
    True
    """
    from modules.adapters.tts import build_tts_adapter as _build_tts

    adapter = _build_tts()
    if adapter is None:
        logger.info("TTS: no adapter configured — audio synthesis disabled")
    else:
        logger.info("TTS: %s", adapter.__class__.__name__)
    return adapter


class YTAIMBotOrchestrator(object):
    """The main YTAIMBot pipeline orchestrator.

    Coordinates all steps of the content generation pipeline:
    1. Trend signal ingestion
    2. Trend analysis (ranking)
    3. Script generation
    4. Content quality & compliance checks
    5. Video assembly
    6. Publishing

    Parameters
    ----------
    trend_source:
        Adapter for ingesting raw trend signals.
    script_generator:
        Generates video scripts from content plans.
    video_assembler:
        Assembles video assets (video file, thumbnail, subtitles).
    publisher:
        Publishes final video assets to the target platform (e.g., YouTube).
    storage:
        Persistent storage adapter for pipeline artifacts.
    compliance_checker:
        Performs content quality and compliance checks.
    config:
        Application configuration dictionary (e.g., environment variables).
    rng:
        Numpy random number generator for deterministic behavior.

    Examples
    --------
    >>> from modules.adapters.synthetic import SyntheticTrendSource
    >>> from modules.adapters.storage.sqlite import SQLiteStorage
    >>> from modules.adapters.publisher.manual import ManualReviewPublisher
    >>> from ytaimbot_ml.quality import MockComplianceChecker
    >>> from ytaimbot_ml.schemas import Script, VideoAsset, ContentPlan
    >>> from ytaimbot_ml.rl import MockRewardShaper, MockPolicy
    >>> import numpy as np
    >>> # Minimal setup for demonstration
    >>> class MockScriptGenerator:
    ...     def generate_script(self, plan: ContentPlan) -> Script:
    ...         return Script(plan_id=plan.trend_id, sections=[])
    >>> class MockVideoAssembler:
    ...     def assemble_video(self, script: Script) -> VideoAsset:
    ...         return VideoAsset(plan_id=script.plan_id)
    >>> config = {"DRY_RUN": "1", "YTAIMBOT_DRY_RUN": "1"}
    >>> storage = SQLiteStorage(db_path=":memory:")
    >>> orchestrator = YTAIMBotOrchestrator(
    ...     trend_source=SyntheticTrendSource(),
    ...     script_generator=MockScriptGenerator(),
    ...     video_assembler=MockVideoAssembler(),
    ...     publisher=ManualReviewPublisher(storage=storage, config=config),
    ...     storage=storage,
    ...     compliance_checker=MockComplianceChecker(),
    ...     config=config,
    ...     rng=np.random.default_rng(42)
    ... )
    >>> run_id = str(uuid4())
    >>> orchestrator.run_pipeline(run_id=run_id)
    >>> orchestrator.storage.load_run(run_id)["status"]
    'ok'
    """

    def __init__(
        self,
        trend_source: TrendSourceAdapter,
        script_generator: Any,  # ScriptGeneratorAdapter
        video_assembler: Any,  # VideoAssemblerAdapter
        publisher: PublisherAdapter,
        storage: StorageAdapter,
        compliance_checker: Any,  # ComplianceCheckerAdapter
        config: dict[str, Any],
        rng: np.random.Generator,
    ) -> None:
        self.trend_source = trend_source
        self.script_generator = script_generator
        self.video_assembler = video_assembler
        self.publisher = publisher
        self.storage = storage
        self.compliance_checker = compliance_checker
        self.config = config
        self.rng = rng

        self.trend_analyzer = TrendAnalyzer(rng=rng)
        self.quality_filter = BayesQualityFilter()
        self.similarity_gate = SimilarityGate()
        self.reward_shaper = RewardShaper()

        # UCB1 Bandit for niche selection (explore/exploit)
        self.niche_bandit = UCB1Bandit(
            arm_ids=self.storage.load_niche_arms(), # Fixed parameter name
            rng=rng,
        )
        self.niche_weights = self.storage.load_niche_weights()

        # PPO Reinforcement Learning for content optimization
        self.ppo_policy = LinearPPO(
            state_dim=10,  # Fixed parameter names, removed rng
            action_dim=5,
        )
        self.ppo_transitions: list[Transition] = []  # state, action, reward, next_state

        self.drift_detector = KSDriftDetector()
        self.metrics_registry = MetricsRegistry()

        # Load PPO transitions from storage if any
        stored_transitions = self.storage.load_ppo_transitions()
        if stored_transitions:
            logger.info("Loaded %d PPO transitions from storage.", len(stored_transitions))
            for t_data in stored_transitions:
                state = np.array(json.loads(t_data["state_json"]))
                action_idx = t_data["action_idx"] # Fixed: action is int index in LinearPPO
                reward = 0.0 # Reward will be calculated when the actual video metrics are available
                next_state = np.zeros(self.ppo_policy.state_dim) # Placeholder
                self.ppo_transitions.append(
                    Transition(
                        state=state,
                        action_idx=action_idx,
                        reward=reward,
                        next_state=next_state,
                        prob=t_data["prob"]
                    )
                )

        logger.info("Orchestrator initialized in DRY_RUN mode: %s", self.dry_run)

    @property
    def dry_run(self) -> bool:
        """True if the pipeline is running in dry-run mode (no publishing)."""
        return (
            os.getenv("DRY_RUN", "0").lower() == "1"
            or os.getenv("YTAIMBOT_DRY_RUN", "0").lower() == "1"
        )

    def run_pipeline(self, run_id: str) -> PipelineResult:
        """Execute one full iteration of the YTAIMBot content generation pipeline.

        Parameters
        ----------
        run_id:
            Unique identifier for this pipeline run.

        Returns
-------
        PipelineResult
            Aggregated results and status of the pipeline run.
        """
        logger.info("[%s] Pipeline run started.", run_id)
        start_time = time.time()
        self.storage.save_run(run_id, "in_progress")

        result = PipelineResult(run_id=run_id, status="error")

        try:
            # 1. Trend signal ingestion
            trends = self.trend_source.fetch()
            self.storage.save_trends(run_id, trends)
            logger.info("[%s] Ingested %d trend signals.", run_id, len(trends))

            if not trends:
                logger.warning("[%s] No trends found. Pipeline finished.", run_id)
                result.status = "ok"
                self.storage.save_run(run_id, "ok")
                return result

            # 2. Trend analysis (ranking)
            ranked_trends = self.trend_analyzer.rank_trends(trends)
            result.rankings = ranked_trends
            logger.info("[%s] Ranked %d trends.", run_id, len(ranked_trends))

            # Select top trend for content generation (e.g., highest ranked)
            top_trend = ranked_trends[0]
            logger.info(
                "[%s] Selected top trend: %s (score: %.2f)",
                run_id,
                top_trend.keyword,
                top_trend.score,
            )

            # 3. Content Plan Generation (simplified for now)
            # In a real scenario, this would involve more LLM calls
            content_plan = ContentPlan(
                trend_id=top_trend.trend_id,
                title=f"How to {top_trend.keyword}",
                outline=[
                    "Introduction",
                    f"Why {top_trend.keyword} is important",
                    "Step-by-step guide",
                    "Conclusion",
                ],
                keywords=[top_trend.keyword, "tutorial", "guide"],
            )
            result.plans.append(content_plan)
            logger.info("[%s] Generated content plan for '%s'.", run_id, top_trend.keyword)

            # Choose an action using the PPO policy
            content_state = np.random.rand(self.ppo_policy.state_dim) # Fixed: state is np.ndarray
            action_idx, prob = self.ppo_policy.select_action(content_state) # Fixed method call
            logger.info("[%s] PPO Policy chose action %d with prob %.2f", run_id, action_idx, prob)

            # Store the transition for later PPO update
            self.storage.save_ppo_transition(
                video_id=run_id, # Use run_id as a dummy video_id for now
                state=content_state.tolist(),
                action_idx=action_idx,
                prob=prob
            )

            # 4. Script Generation
            if self.script_generator:
                script = self.script_generator.generate_script(content_plan)
                result.scripts.append(script)
                logger.info(
                    "[%s] Generated script with %d sections (total words: %d).",
                    run_id,
                    len(script.sections),
                    script.total_words,
                )
            else:
                logger.warning("[%s] Script generator not available.", run_id)
                script = Script(plan_id=content_plan.trend_id, sections=[]) # Placeholder

            # 5. Content Quality & Compliance Checks
            compliance_report = self.compliance_checker.check(script)
            self.storage.save_compliance(run_id, [compliance_report])
            result.compliance_reports.append(compliance_report)
            logger.info(
                "[%s] Compliance check decision: %s (Bayes P(bad): %.2f)",
                run_id,
                compliance_report.decision,
                compliance_report.bayes_p_bad,
            )

            if compliance_report.decision != "pass":
                logger.warning("[%s] Content failed compliance. Aborting pipeline.", run_id)
                result.status = "blocked"
                self.storage.save_run(run_id, "blocked")
                return result

            # Stage 7: _generate_script — save script to disk (T-152, T-154)
            data_dir = Path(self.config.get("YTAIMBOT_DATA_DIR", "/tmp"))
            script_dir = data_dir / "scripts"
            script_dir.mkdir(parents=True, exist_ok=True)
            script_file = script_dir / f"{run_id}.txt"
            try:
                script_file.write_text(script.full_text, encoding="utf-8")
                result.script_path = str(script_file)
                logger.info("[%s] Script saved: %s (%d words)", run_id, script_file, script.total_words)
            except OSError as e:
                logger.warning("[%s] Could not save script to disk: %s", run_id, e)

            # Stage 8: _synthesize_audio — TTS synthesis (T-153, T-154)
            audio_dir = data_dir / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            audio_path = audio_dir / f"{run_id}.mp3"
            tts_adapter = build_tts_adapter()
            if tts_adapter:
                try:
                    tts_adapter.speak(script.full_text, audio_path)
                    result.audio_path = str(audio_path)
                    logger.info("[%s] Audio synthesized: %s", run_id, audio_path)
                except Exception as e:
                    logger.warning("[%s] TTS failed (non-fatal): %s", run_id, e)
            else:
                logger.info("[%s] TTS adapter not available — audio skipped", run_id)


            # 6. Video Assembly
            video_asset = self.video_assembler.assemble_video(script)
            result.videos.append(video_asset)
            logger.info(
                "[%s] Assembled video: %s (thumbnail: %s).",
                run_id,
                video_asset.video_path,
                video_asset.thumbnail_path,
            )

            # 7. Publishing
            if not self.dry_run:
                upload_result = self.publisher.publish(content_plan, compliance_report)
                result.uploads.append(upload_result)
                if upload_result.success:
                    self.storage.save_video(
                        video_id=upload_result.video_id,
                        trend_id=content_plan.trend_id,
                        title=content_plan.title,
                        privacy_status=upload_result.privacy_status,
                    )
                    logger.info(
                        "[%s] Published video: %s (URL: %s)",
                        run_id,
                        upload_result.video_id,
                        upload_result.url,
                    )
                    # For PPO, calculate immediate reward based on preliminary metrics
                    reward = self.reward_shaper.shape(
                        views=0, # Initial views are 0
                        ctr=0.0,
                        retention_30s=0.0
                    )
                    # Find the stored PPO transition and update its reward
                    for t in self.ppo_transitions:
                        # Assuming video_id is used to link transition to actual video
                        if np.array_equal(t.state, content_state): # Fixed match
                            t.reward = reward
                            break
                    # Train PPO policy periodically
                    if len(self.ppo_transitions) >= 10: # Example batch size
                        self.ppo_policy.update(self.ppo_transitions) # Fixed method call
                        self.storage.clear_ppo_transitions()
                        self.ppo_transitions.clear()


                else:
                    logger.error("[%s] Video publishing failed.", run_id)
                    result.status = "error"
                    self.storage.save_run(run_id, "error")
                    return result
            else:
                logger.info(
                    "[%s] Dry-run mode: skipping actual video publishing.", run_id
                )
                self.storage.save_video(
                    video_id=compliance_report.content_hash, # Use content_hash as dummy video_id for dry run
                    trend_id=content_plan.trend_id,
                    title=content_plan.title,
                    privacy_status="unlisted",
                )


            result.status = "ok"
            self.storage.save_run(run_id, "ok")
            logger.info("[%s] Pipeline run finished successfully.", run_id)

        except Exception as e:
            logger.exception("[%s] Pipeline run failed due to exception.", run_id)
            result.status = "error"
            self.storage.save_run(run_id, "error")
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.info("[%s] Pipeline run completed in %.2f seconds.", run_id, duration)
            self.metrics_registry.record_run(result.status) # Fixed method call
            self.metrics_registry.observe_duration(duration) # Fixed method call

        return result

    def update_metrics(self) -> None:
        """Update metrics for published videos and use them for RL training.

        This method is typically called by the scheduler.
        """
        logger.info("Updating metrics for published videos.")
        published_videos = self.storage.list_published_videos()
        for video_info in published_videos:
            video_id = video_info["video_id"]
            # In a real scenario, fetch actual metrics from YouTube API
            # For now, simulate some metrics for demonstration
            metrics = {
                "views": self.rng.randint(100, 10000),
                "ctr": self.rng.uniform(0.02, 0.15),
                "retention_30s": self.rng.uniform(0.3, 0.9),
                "rpm": self.rng.uniform(0.5, 5.0),
                "watch_time_h": self.rng.uniform(10, 1000),
            }
            snapshot = MetricsSnapshot(
                video_id=video_id,
                views=metrics["views"],
                ctr=metrics["ctr"],
                retention_30s=metrics["retention_30s"],
                rpm=metrics["rpm"],
                watch_time_h=metrics["watch_time_h"],
                collected_at=datetime.now(timezone.utc)
            )
            self.storage.save_metrics(snapshot)
            logger.debug("Saved metrics for video %s: %s", video_id, snapshot)

            # Update PPO policy with new rewards
            transitions = self.storage.load_ppo_transitions()
            for transition_data in transitions:
                if transition_data["video_id"] == video_id:
                    # Calculate reward based on new metrics
                    reward = self.reward_shaper.shape(
                        views=snapshot.views,
                        ctr=snapshot.ctr,
                        retention_30s=snapshot.retention_30s
                    )
                    state = np.array(json.loads(transition_data["state_json"]))
                    action_idx = transition_data["action_idx"]
                    next_state = np.zeros(self.ppo_policy.state_dim) # Placeholder

                    self.ppo_transitions.append(
                        Transition(
                            state=state,
                            action_idx=action_idx,
                            reward=reward,
                            next_state=next_state,
                            prob=transition_data["prob"]
                        )
                    )
            if len(self.ppo_transitions) >= 10: # Example batch size
                self.ppo_policy.update(self.ppo_transitions)
                self.storage.clear_ppo_transitions()
                self.ppo_transitions.clear()

        logger.info("Metrics update completed.")

    def optimize_niche_weights(self) -> None:
        """Optimize niche weights based on UCB1 bandit results.

        This method is typically called by the scheduler.
        """
        logger.info("Optimizing niche weights using UCB1 bandit.")
        # Fetch current arm ids from storage
        arm_ids = self.storage.load_niche_arms()
        self.niche_bandit = UCB1Bandit(arm_ids=arm_ids, rng=self.rng)

        # Simulate a pull for each niche to update internal states and get new weights
        for arm_id in arm_ids:
            # This is a simplification; actual reward would come from video performance
            simulated_reward = self.rng.uniform(0.0, 1.0)
            self.niche_bandit.update(arm_id, simulated_reward) # Fixed method name

        # Update niche weights based on bandit's estimated values
        new_weights = {
            arm_id: self.niche_bandit._arms[arm_id].avg_reward for arm_id in arm_ids
        }
        self.storage.save_niche_weights(new_weights)
        logger.info("Niche weights optimized and saved: %s", new_weights)

    def run_daily_maintenance(self) -> None:
        """Perform daily maintenance tasks like data cleanup, log rotation etc."""
        logger.info("Running daily maintenance tasks.")
        # Example: Clean up old temporary files
        temp_dir = Path("/tmp")
        for f in temp_dir.glob("ytaimbot_*.mp4"):
            try:
                os.remove(f)
                logger.debug("Cleaned up old video file: %s", f)
            except OSError as e:
                logger.warning("Error cleaning up file %s: %s", f, e)
        logger.info("Daily maintenance completed.")

class Pipeline:
    """Entry point for the YTAIMBot pipeline, handling configuration and orchestration."""

    def __init__(self) -> None:
        self.config = self._load_config()
        self.rng = make_rng(self.config.get("YTAIMBOT_SEED", 42))

        self.storage = build_storage(self.config)
        self.trend_source = build_trend_source(self.config)
        self.script_generator = build_llm_adapter()
        self.video_assembler = create_video_backend(self.config)
        self.compliance_checker = self._build_compliance_checker()
        
        # Determine if we are in dry run mode
        dry_run = (
            os.getenv("DRY_RUN", "0").lower() == "1"
            or os.getenv("YTAIMBOT_DRY_RUN", "0").lower() == "1"
        )
        
        self.publisher = (
            build_youtube_uploader(self.config)
            if not dry_run
            else build_manual_reviewer(self.config)
        )
        self.metrics_registry = build_metrics_collector(self.config)

        self.orchestrator = YTAIMBotOrchestrator(
            trend_source=self.trend_source,
            script_generator=self.script_generator,
            video_assembler=self.video_assembler,
            publisher=self.publisher,
            storage=self.storage,
            compliance_checker=self.compliance_checker,
            config=self.config,
            rng=self.rng,
        )

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            "YTAIMBOT_DRY_RUN": os.getenv("YTAIMBOT_DRY_RUN", "0"),
            "YTAIMBOT_SEED": int(os.getenv("YTAIMBOT_SEED", "42")),
            "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),
            "GOOGLE_TRENDS_GEO": os.getenv("GOOGLE_TRENDS_GEO", "US"),
            "DB_PATH": os.getenv("DB_PATH"),
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER"),
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
            "LLM_MODEL": os.getenv("LLM_MODEL"),
            "TTS_LANGUAGE": os.getenv("TTS_LANGUAGE"),
            "TTS_VOICE": os.getenv("TTS_VOICE"),
            "ENABLE_TTS": os.getenv("ENABLE_TTS", "0"),
        }

    def _build_compliance_checker(self) -> Any:
        """Build the content compliance checker."""
        return SimilarityGate()

    def run(self) -> None:
        """Run the main pipeline."""
        run_id = str(uuid4())
        self.orchestrator.run_pipeline(run_id)


from ytaimbot_ml.learner.optimizer import Transition # Fixed import to use learner version
