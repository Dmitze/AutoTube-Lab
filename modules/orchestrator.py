"""MVP pipeline orchestrator.

Stages
------
1. ingest          — fetch TrendSignals from source adapter
2. featurize       — (handled inside TrendAnalyzer.analyze)
3. reduce          — SVD/PCA dimensionality reduction (inside TrendAnalyzer)
4. score           — rank trends by magnitude
5. plan            — generate stub ContentPlans for top-N trends
6. gate            — compliance check via BayesQualityFilter
7. generate_script — LLM generates 6-section script per approved plan [Phase 2]
8. synthesize_tts  — EdgeTTS converts script to MP3 audio              [Phase 2]
9. assemble_video  — VideoAssembler + ThumbnailGenerator               [Phase 4]
10. publish        — YouTube upload with QuotaGuard (skip in dry_run)  [Phase 5]

Fail-closed design: publish is NEVER called unless a ComplianceReport
with decision="pass" exists for the plan AND YTAIMBOT_DRY_RUN=false.

Adapter auto-selection:
  Trend  (T-069): YOUTUBE_API_KEY + GOOGLE_TRENDS_GEO → CompositeTrendSource
  LLM    (T-082): GROQ_API_KEY → GroqAdapter | OLLAMA_URL → OllamaAdapter
  TTS    (T-098): TTS_VOICE set → EdgeTTSAdapter (default uk-UA-OstapNeural)
  Upload (T-371): YOUTUBE_CLIENT_SECRET_PATH set → YouTubeUploadAdapter
"""

from __future__ import annotations

import json
import logging
import os
import uuid
import time
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.adapters.base import (
    LLMAdapter,
    PublisherAdapter,
    StorageAdapter,
    TTSAdapter,
    TrendSourceAdapter,
)
from modules.adapters.video.assembler import VideoAssembler
from modules.adapters.video.ai_generator import create_video_backend
from ytaimbot_ml.quality.bayes_filter import BayesQualityFilter
from ytaimbot_ml.quality.similarity_gate import SimilarityGate
from ytaimbot_ml.rl.reward_shaper import RewardShaper
from ytaimbot_ml.rl.ucb1_bandit import UCB1Bandit
from ytaimbot_ml.utils.metrics import MetricsRegistry
from ytaimbot_ml.learner.drift_detector import KSDriftDetector
from ytaimbot_ml.learner.optimizer import LinearPPO, Transition
from ytaimbot_ml.schemas import (
    ComplianceReport,
    ContentPlan,
    PipelineResult,
    Script,
    TrendRanking,
    TrendSignal,
    ContentState,
    ContentAction,
)
from ytaimbot_ml.trend_analyzer import TrendAnalyzer
from ytaimbot_ml.utils.random import make_rng

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from modules.dashboard.manual_review import ManualReviewCLI
    from modules.scheduler import UploadScheduler


# ---------------------------------------------------------------------------
# Adapter factories
# ---------------------------------------------------------------------------


def build_trend_source(seed: int = 42) -> TrendSourceAdapter:
    """Auto-select trend source adapter based on environment variables.

    Selection logic (T-069):

    +--------------------------+----------------------------+
    | YOUTUBE_API_KEY present? | GOOGLE_TRENDS_GEO present? |
    +--------------------------+----------------------------+
    | Yes                      | Yes → CompositeTrendSource  |
    | Yes                      | No  → YouTubeSearchTrendSource |
    | No                       | Yes → GoogleTrendsAdapter |
    | No                       | No  → SyntheticTrendSource  |
    +--------------------------+----------------------------+

    Parameters
    ----------
    seed:
        RNG seed passed to adapters for deterministic fallback.

    Returns
    -------
    TrendSourceAdapter
        The most capable adapter available given current env vars.

    Complexity
    ----------
    O(1)

    Examples
    --------
    >>> import os; os.environ.pop("YOUTUBE_API_KEY", None)
    >>> src = build_trend_source(seed=42)
    >>> src.__class__.__name__
    'SyntheticTrendSource'
    """
    has_yt = bool(os.environ.get("YOUTUBE_API_KEY", "").strip())
    has_gt = bool(os.environ.get("GOOGLE_TRENDS_GEO", "").strip())

    if has_yt and has_gt:
        from modules.adapters.composite import CompositeTrendSource
        from modules.adapters.google_trends import GoogleTrendsAdapter
        from modules.adapters.youtube_search import YouTubeSearchTrendSource

        geo = os.environ["GOOGLE_TRENDS_GEO"]
        weight_str = os.environ.get("ADAPTER_WEIGHTS", "1.0,1.0").split(",")
        w_gt = float(weight_str[0]) if len(weight_str) > 0 else 1.0
        w_yt = float(weight_str[1]) if len(weight_str) > 1 else 1.0

        logger.info("TrendSource: CompositeTrendSource (GoogleTrends + YouTube)")
        return CompositeTrendSource(
            adapters=[
                (GoogleTrendsAdapter(geo=geo, seed=seed), w_gt),
                (YouTubeSearchTrendSource(seed=seed), w_yt),
            ],
            cache_ttl=int(os.environ.get("TREND_CACHE_TTL", "900")),
            seed=seed,
        )

    if has_yt:
        from modules.adapters.youtube_search import YouTubeSearchTrendSource
        logger.info("TrendSource: YouTubeSearchTrendSource")
        return YouTubeSearchTrendSource(seed=seed)

    if has_gt:
        from modules.adapters.google_trends import GoogleTrendsAdapter
        geo = os.environ["GOOGLE_TRENDS_GEO"]
        logger.info("TrendSource: GoogleTrendsAdapter (geo=%s)", geo)
        return GoogleTrendsAdapter(geo=geo, seed=seed)

    from modules.adapters.synthetic import SyntheticTrendSource
    logger.info("TrendSource: SyntheticTrendSource (no API keys configured)")
    return SyntheticTrendSource(seed=seed)


def build_llm_adapter(seed: int = 42) -> Optional[LLMAdapter]:
    """Auto-select LLM adapter from environment variables.

    Selection priority:
      1. GROQ_API_KEY + OLLAMA_URL → LLMFallbackChain([Groq, Ollama])
      2. GROQ_API_KEY only         → GroqAdapter
      3. OLLAMA_URL only           → OllamaAdapter
      4. Neither                   → None (script generation stage skipped)

    Parameters
    ----------
    seed:
        Unused — reserved for future deterministic sampling.

    Returns
    -------
    LLMAdapter | None
        Configured adapter, or None if no LLM keys present.

    Complexity
    ----------
    O(1)

    Examples
    --------
    >>> import os; os.environ.pop("GROQ_API_KEY", None); os.environ.pop("OLLAMA_URL", None)
    >>> build_llm_adapter() is None
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


def build_youtube_uploader() -> Optional[PublisherAdapter]:
    """Build YouTubeUploadAdapter when client_secret.json is configured.

    Selection logic:
      YOUTUBE_CLIENT_SECRET_PATH exists → YouTubeUploadAdapter (dry_run from env)
      Not configured                    → None (publish stage skipped)

    Returns
    -------
    PublisherAdapter | None
        Configured adapter, or None if OAuth2 credentials not present.

    Complexity
    ----------
    O(1)

    Examples
    --------
    >>> import os; os.environ.pop("YOUTUBE_CLIENT_SECRET_PATH", None)
    >>> build_youtube_uploader() is None
    True
    """
    secret_path = os.environ.get("YOUTUBE_CLIENT_SECRET_PATH", "data/client_secret.json")
    from pathlib import Path as _Path
    if _Path(secret_path).exists():
        from modules.adapters.publisher.youtube_upload import YouTubeUploadAdapter
        logger.info("Publisher: YouTubeUploadAdapter (secret=%s)", secret_path)
        return YouTubeUploadAdapter(client_secret_path=secret_path)
    logger.info("Publisher: no client_secret.json — upload stage disabled")
    return None


def build_manual_reviewer() -> Optional["ManualReviewCLI"]:
    """Build ManualReviewCLI from env if enabled.

    Reads:
      - MANUAL_REVIEW_ENABLED (default false)
      - MANUAL_REVIEW_QUOTA (default 50)
      - MANUAL_REVIEW_LOG_PATH (default data/audit/review_log.jsonl)
    """
    enabled = os.environ.get("MANUAL_REVIEW_ENABLED", "false").lower() == "true"
    if not enabled:
        return None
    from modules.dashboard.audit_log import AuditLog
    from modules.dashboard.manual_review import ManualReviewCLI

    quota = int(os.environ.get("MANUAL_REVIEW_QUOTA", "50"))
    path = os.environ.get("MANUAL_REVIEW_LOG_PATH", "data/audit/review_log.jsonl")
    logger.info("ManualReview: enabled quota=%d log=%s", quota, path)
    return ManualReviewCLI(audit_log=AuditLog(path=path), manual_quota=quota)


def build_storage() -> StorageAdapter:
    """Auto-select storage adapter based on environment variables.

    Selection logic (T-321):
    - STORAGE_BACKEND=sqlite → SQLiteStorage
    - Default → InMemoryStorage (non-persistent)

    Returns
    -------
    StorageAdapter
        Persistent or ephemeral storage backend.
    """
    backend = os.environ.get("STORAGE_BACKEND", "in_memory").lower()
    if backend == "sqlite":
        from modules.adapters.storage.sqlite import SQLiteStorage  # noqa: PLC0415
        return SQLiteStorage()
    
    from modules.adapters.storage.in_memory import InMemoryStorage  # noqa: PLC0415
    return InMemoryStorage()


def build_metrics_collector(storage: StorageAdapter) -> Any:
    """Build MetricsCollector from env if enabled. (T-327)."""
    if os.environ.get("STORAGE_BACKEND") == "in_memory":
        from modules.adapters.synthetic import SyntheticMetricsCollector
        return SyntheticMetricsCollector(storage) # type: ignore
        
    from modules.metrics_collector import MetricsCollector
    return MetricsCollector(storage=storage)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class Pipeline:
    """Orchestrates the full trend-to-publish pipeline (9 stages).

    Parameters
    ----------
    trend_source:
        Adapter that provides TrendSignal objects.
    storage:
        Adapter that persists run artefacts.
    publisher:
        Optional adapter for publishing approved content.
    llm:
        Optional LLM adapter for script generation (Phase 2).
        When None, stage 7 is skipped.
    tts:
        Optional TTS adapter for audio synthesis (Phase 2).
        When None, stage 8 is skipped.
    dry_run:
        When ``True`` (default), no actual publishing occurs.
    seed:
        Integer seed for ML components. Defaults to 42.
    audio_dir:
        Directory for synthesized MP3 files. Defaults to ``data/audio``.
    """

    _TOP_N = 5

    def __init__(
        self,
        trend_source: TrendSourceAdapter,
        storage: StorageAdapter,
        publisher: Optional[PublisherAdapter] = None,
        manual_reviewer: Optional["ManualReviewCLI"] = None,
        scheduler: Optional["UploadScheduler"] = None,
        llm: Optional[LLMAdapter] = None,
        tts: Optional[TTSAdapter] = None,
        dry_run: bool = True,
        seed: int = 42,
        audio_dir: str | Path = "data/audio",
    ) -> None:
        self._source = trend_source
        self._storage = storage
        self._publisher = publisher
        self._manual_reviewer = manual_reviewer
        self._scheduler = scheduler
        self._llm = llm
        self._tts = tts
        self._dry_run = dry_run
        self._seed = seed
        self._rng = make_rng(seed)
        self._analyzer = TrendAnalyzer(rng=make_rng(seed))
        self._gate = BayesQualityFilter()
        self._similarity_gate = SimilarityGate()
        self._reward_shaper = RewardShaper()
        self._audio_dir = Path(audio_dir)

        # RL Niche Selection (T-387+)
        self._bandit: UCB1Bandit = self._init_bandit()
        
        # RL Drift Detection (T-431)
        self._drift_detector = KSDriftDetector(
            threshold=float(os.environ.get("DRIFT_THRESHOLD", "0.05"))
        )
        
        # RL Policy Optimizer (T-432)
        self._ppo = self._init_ppo()
        
        # Monitoring (Phase 7)
        if os.environ.get("METRICS_ENABLED", "false").lower() == "true":
            MetricsRegistry.start_server(int(os.environ.get("METRICS_PORT", "9090")))

    def _init_bandit(self) -> UCB1Bandit:
        """Initialise or restore the niche selection bandit.

        Complexity: O(k) where k = number of niches.
        """
        bandit = UCB1Bandit.for_niches(rng=make_rng(self._seed))
        
        # Restore state if storage supports it
        if hasattr(self._storage, "load_niche_arms"):
            arms_data = self._storage.load_niche_arms()
            if arms_data:
                # Reconstruct bandit from stored stats
                # Note: UCB1Bandit.from_dict expects a specific format
                serialised = {
                    "total_pulls": sum(a["n_pulls"] for a in arms_data),
                    "arms": [
                        {
                            "arm_id": a["arm_id"],
                            "n_pulls": a["n_pulls"],
                            "total_reward": a["total_reward"],
                            "last_reward": a["last_reward"],
                        }
                        for a in arms_data
                    ]
                }
                bandit = UCB1Bandit.from_dict(serialised, rng=make_rng(self._seed))
                logger.info("Pipeline: restored bandit state with %d pulls", bandit.total_pulls)
        
        return bandit

    def _init_ppo(self) -> LinearPPO:
        """Initialise or restore the content policy optimizer.

        Complexity: O(state_dim * action_dim).
        """
        # State: [n_pulls, avg_reward, last_reward, total_pulls] for the niche
        state_dim = 4
        # Actions: [0: short, 1: medium, 2: long] video duration
        action_dim = 3
        
        lr = float(os.environ.get("PPO_LR", "0.01"))
        eps = float(os.environ.get("PPO_EPSILON", "0.2"))
        
        ppo = LinearPPO(state_dim=state_dim, action_dim=action_dim, lr=lr, eps=eps)
        
        policy_path = Path(os.getenv("YTAIMBOT_DATA_DIR", "./data")) / "models" / "ppo_policy.pkl"
        if policy_path.exists():
            try:
                ppo.load_policy(policy_path)
                logger.info("Pipeline: restored PPO policy from %s", policy_path)
            except Exception as exc:
                logger.warning("Pipeline: failed to load PPO policy: %s", exc)
                
        return ppo

    def _feedback_loop(self) -> None:
        """Collect metrics and update RL bandit, PPO, and drift detection.

        Algorithm: 
          1. list recent published videos
          2. query YouTube Analytics via MetricsCollector
          3. shape reward in [0, 1] via RewardShaper
          4. update bandit state
          5. update PPO transitions
          6. persist to storage
          7. check for data drift and reset bandit if needed

        Complexity: O(n_videos × API_call)
        """
        if not self._storage or not hasattr(self._storage, "list_published_videos"):
            return

        # 1. Get videos
        videos = self._storage.list_published_videos(limit=20)
        if not videos:
            return

        # 2. Build metrics collector
        collector = build_metrics_collector(self._storage)

        # 3. Handle PPO updates
        self._update_ppo(videos, collector)

        # 4. Handle Bandit and Drift
        self._update_bandit_and_drift(videos, collector)

    def _update_ppo(self, videos: list[dict], collector: Any) -> None:
        """Process pending PPO transitions.  O(n_transitions)."""
        if not hasattr(self._storage, "load_ppo_transitions"):
            return
            
        pending = self._storage.load_ppo_transitions()
        if not pending:
            return
            
        trajectory = []
        for p in pending:
            video_id = p["video_id"]
            # Find video record to get published_at
            v = next((v for v in videos if v["video_id"] == video_id), None)
            if not v:
                continue
                
            try:
                pub_at = datetime.fromtimestamp(v["published_at"], tz=timezone.utc)
                snapshot = collector.collect(video_id, pub_at)
                
                # Reward for PPO
                reward = self._reward_shaper.shape(
                    ctr=snapshot.ctr,
                    retention_30s=snapshot.retention_30s,
                    views=snapshot.views
                )
                
                # Create transition object
                state = np.array(json.loads(p["state_json"]))
                trajectory.append(Transition(
                    state=state,
                    action_idx=p["action_idx"],
                    reward=reward,
                    prob=p["prob"]
                ))
            except Exception:
                continue
                
        if trajectory:
            loss = self._ppo.update(trajectory)
            # Save updated policy
            policy_dir = Path(os.getenv("YTAIMBOT_DATA_DIR", "./data")) / "models"
            policy_dir.mkdir(parents=True, exist_ok=True)
            self._ppo.save_policy(policy_dir / "ppo_policy.pkl")
            logger.info("Pipeline: PPO update successful (loss=%.4f)", loss)
            
        # Always clear transitions to prevent stale updates
        self._storage.clear_ppo_transitions()

    def _update_bandit_and_drift(self, videos: list[dict], collector: Any) -> None:
        """Update niche bandit and check for data drift.  O(n_videos)."""
        all_rewards = []
        for v in videos:
            try:
                from modules.metrics_collector import TooEarlyError
                pub_at = datetime.fromtimestamp(v["published_at"], tz=timezone.utc)
                snapshot = collector.collect(v["video_id"], pub_at)
                
                reward = self._reward_shaper.shape(
                    ctr=snapshot.ctr,
                    retention_30s=snapshot.retention_30s,
                    views=snapshot.views
                )
                all_rewards.append(reward)
                
                # Update bandit
                arm_id = v.get("trend_id")
                if arm_id in self._bandit.stats:
                    self._bandit.update(arm_id, reward)
                    if hasattr(self._storage, "upsert_niche_arm"):
                        arm = self._bandit.stats[arm_id]
                        self._storage.upsert_niche_arm(
                            arm_id=arm_id,
                            n_pulls=arm.n_pulls,
                            total_reward=arm.total_reward,
                            last_reward=arm.last_reward
                        )
            except Exception:
                continue

        # Drift check (T-431)
        if len(all_rewards) >= 10:
            # We need reference and current distributions.
            # Reference = last 20-10, Current = last 10.
            # Simplified for MVP using current batch
            mid = len(all_rewards) // 2
            ref = all_rewards[:mid]
            curr = all_rewards[mid:]
            
            report = self._drift_detector.check(ref, curr)
            if report.drift_detected:
                logger.warning("Pipeline: drift detected! Resetting bandit.")
                self._bandit.reset()
                # Persist reset
                for aid in self._bandit.stats:
                    if hasattr(self._storage, "upsert_niche_arm"):
                        arm = self._bandit.stats[aid]
                        self._storage.upsert_niche_arm(aid, 0, 0.0, 0.0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, run_id: str | None = None) -> PipelineResult:
        """Execute all pipeline stages and return a PipelineResult.

        Parameters
        ----------
        run_id:
            Unique identifier for this run. Auto-generated if omitted.

        Returns
        -------
        PipelineResult
            Contains rankings, plans, compliance reports, scripts, status.

        Complexity
        ----------
        O(n_trends × tokens) — dominated by LLM calls when enabled
        """
        run_id = run_id or str(uuid.uuid4())
        
        # Stage -2: RL Feedback (T-387+)
        # Collect metrics from YouTube and update bandit before new selection
        self._feedback_loop()

        # Stage -1: RL Niche Selection (Phase 6)
        # Select target niche before ingestion
        target_niche = self._bandit.select()
        logger.info("Pipeline: RL selected niche '%s'", target_niche)

        # Stage -0.5: RL Content Optimization (PPO) (T-432)
        # 1. Get state for the niche
        arm = self._bandit.stats.get(target_niche)
        state_vec = np.array([
            float(arm.n_pulls) if arm else 0.0,
            float(arm.avg_reward) if arm else 0.0,
            float(arm.last_reward) if arm else 0.0,
            float(self._bandit.total_pulls)
        ])
        
        # 2. Select action
        action_idx, prob = self._ppo.select_action(state_vec)
        durations = ["short", "medium", "long"]
        logger.info("Pipeline: PPO selected duration '%s' (prob=%.2f)", durations[action_idx], prob)

        logger.info(
            "Pipeline run %s started (dry_run=%s, llm=%s, tts=%s)",
            run_id,
            self._dry_run,
            self._llm.__class__.__name__ if self._llm else "disabled",
            self._tts.__class__.__name__ if self._tts else "disabled",
        )

        result = PipelineResult(run_id=run_id)

        try:
            # Stage 0: persistent status
            self._storage.save_run(run_id, "pending")

            # Stage 1: ingest (with RL filtering)
            signals = self._ingest(target_niche=target_niche)
            self._storage.save_trends(run_id, signals)

            # Stages 2–4: featurize → reduce → score
            rankings = self._score(signals)
            result.rankings = rankings

            # Stage 5: plan
            plans = self._plan(rankings)
            result.plans = plans

            # Stage 6: gate (Similarity + Bayes)
            # Stage 6.1: Similarity Gate (T-275)
            archive = self._storage.load_archive() if hasattr(self._storage, "load_archive") else {}
            similarity_reports = [self._similarity_gate.check(p.title, archive) for p in plans]
            
            # Stage 6.2: Bayes Quality Filter
            reports = self._gate_all(plans)
            
            # Combine reports (fail-closed)
            for r, s in zip(reports, similarity_reports):
                if s.decision == "block":
                    r.decision = "block"
                    r.reasons.append(f"Similarity too high: {s.score:.2f}")

            result.compliance_reports = reports
            self._storage.save_compliance(run_id, reports)

            # Stage 7: script generation (Phase 2 — optional)
            approved_plans = [
                p for p, r in zip(plans, reports) if r.decision == "pass"
            ]
            if self._llm is not None and approved_plans:
                scripts = self._generate_scripts(approved_plans)
                result.scripts = scripts
            else:
                if self._llm is None:
                    logger.info("Stage 7 skipped: no LLM adapter configured")

            # Stage 8: TTS audio synthesis (Phase 2 — optional)
            if self._tts is not None and result.scripts:
                self._synthesize_audio(result.scripts, run_id)
            else:
                if self._tts is None and result.scripts:
                    logger.info("Stage 8 skipped: no TTS adapter configured")

            # Stage 8.1: SEO optimization (Phase 3 — optional)
            if result.plans:
                self._optimize_seo(result.plans)

            # Stage 8.2: Thumbnail generation (Phase 3 — optional)
            if result.plans:
                self._generate_thumbnails(result.plans, run_id)

            # Stage 8.3: Subtitle generation (Phase 3 — optional)
            if result.scripts:
                self._generate_subtitles(result.scripts, run_id)

            # Stage 8.4: Video assembly (Phase 3 — optional)
            if result.scripts:
                self._assemble_videos(result.scripts, run_id)

            # Stage 9: publish (T-371)
            if self._publisher and not self._dry_run:
                self._publish_approved(
                    plans, 
                    reports, 
                    run_id,
                    ppo_state=state_vec,
                    ppo_action=action_idx,
                    ppo_prob=prob
                )

            result.status = "ok"
            self._storage.save_run(run_id, "ok")
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline failed: %s", exc)
            result.status = "error"
            self._storage.save_run(run_id, "error")
            return result

    # ------------------------------------------------------------------
    # Private stage implementations
    # ------------------------------------------------------------------

    def _ingest(self, target_niche: str | None = None) -> list[TrendSignal]:
        """Fetch signals from source, filtered by niche if provided."""
        signals = self._source.fetch()
        
        # RL Filter: If a niche is selected, prioritise its keywords
        if target_niche:
            # Simple keyword matching for demo; in production, 
            # the adapter would take the niche as a query parameter.
            niche_signals = [s for s in signals if target_niche.lower() in s.keyword.lower()]
            if niche_signals:
                logger.debug("Stage 1 — RL filtering: found %d signals for niche %s", len(niche_signals), target_niche)
                return niche_signals
            
        logger.debug("Stage 1 — ingested %d signals", len(signals))
        return signals

    def _score(self, signals: list[TrendSignal]) -> list[TrendRanking]:
        rankings = self._analyzer.analyze(signals)
        logger.debug("Stages 2–4 — scored %d trends", len(rankings))
        return rankings

    def _plan(self, rankings: list[TrendRanking]) -> list[ContentPlan]:
        top = rankings[: self._TOP_N]
        optimizer = _get_title_optimizer()
        plans = []
        for r in top:
            keywords = [r.trend_id, "youtube", "2026"]
            title = (
                optimizer.optimize_from_plan(
                    ContentPlan(r.trend_id, r.trend_id, [], keywords)
                )
                if optimizer
                else f"Video about {r.trend_id}"
            )
            plans.append(ContentPlan(
                trend_id=r.trend_id,
                title=title,
                outline=["Introduction", "Main content", "Call to action"],
                keywords=keywords,
            ))
        logger.debug("Stage 5 — generated %d content plans (seo=%s)", len(plans), optimizer is not None)
        return plans

    def _gate_all(self, plans: list[ContentPlan]) -> list[ComplianceReport]:
        reports: list[ComplianceReport] = []
        for plan in plans:
            features = _plan_to_features(plan)
            report = self._gate.decide(features)
            reports.append(report)
            logger.debug(
                "Stage 6 — compliance %s → %s (p_bad=%.3f)",
                plan.trend_id,
                report.decision,
                report.bayes_p_bad,
            )
        return reports

    def _generate_scripts(self, approved_plans: list[ContentPlan]) -> list[Script]:
        """Stage 7: Generate LLM scripts for each approved plan.

        Complexity: O(n_plans × tokens) — network/inference bound
        """
        from ytaimbot_ml.content.script_generator import ScriptGenerator
        from ytaimbot_ml.content.token_budget import TokenBudget

        language = os.environ.get("SCRIPT_LANGUAGE", "uk")
        total_tokens = int(os.environ.get("LLM_TOTAL_TOKENS", "2048"))
        generator = ScriptGenerator(
            llm=self._llm,  # type: ignore[arg-type]
            budget=TokenBudget(total_tokens=total_tokens),
            language=language,
        )

        scripts: list[Script] = []
        for plan in approved_plans:
            try:
                script = generator.generate(plan, self._rng)
                scripts.append(script)
                logger.info(
                    "Stage 7 — script generated: plan=%s words=%d",
                    plan.trend_id,
                    script.total_words,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Stage 7 — script generation failed for %s: %s", plan.trend_id, exc)

        return scripts

    def _synthesize_audio(self, scripts: list[Script], run_id: str) -> None:
        """Stage 8: Convert scripts to MP3 audio via TTS adapter.

        Audio files saved to: {audio_dir}/{run_id}/{plan_id}.mp3

        Complexity: O(n_scripts × len(text)) — synthesis bound
        """
        self._audio_dir.mkdir(parents=True, exist_ok=True)
        run_audio_dir = self._audio_dir / run_id
        run_audio_dir.mkdir(parents=True, exist_ok=True)

        for script in scripts:
            output_path = run_audio_dir / f"{script.plan_id}.mp3"
            try:
                self._tts.speak(script.full_text, output_path)  # type: ignore[union-attr]
                logger.info(
                    "Stage 8 — audio synthesized: %s → %s",
                    script.plan_id,
                    output_path,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Stage 8 — TTS failed for %s: %s", script.plan_id, exc)

    def _optimize_seo(self, plans: list[ContentPlan]) -> None:
        """Stage 8.1: Expand keywords and optimize titles.  O(n_plans × k)."""
        from ytaimbot_ml.seo.keyword_expander import KeywordExpander  # noqa: PLC0415
        from ytaimbot_ml.seo.title_generator import TitleGenerator  # noqa: PLC0415

        expander = KeywordExpander()
        title_gen = TitleGenerator()

        for plan in plans:
            try:
                # 1. Expand keywords
                plan.keywords = expander.expand(plan.keywords)
                # 2. Optimize title
                variants = title_gen.generate_variants(plan)
                plan.title = title_gen.select_best(variants, plan)
                logger.debug("Stage 8.1 — SEO optimized: %s", plan.trend_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Stage 8.1 — SEO failed for %s: %s", plan.trend_id, exc)

    def _generate_thumbnails(self, plans: list[ContentPlan], run_id: str) -> None:
        """Stage 8.2: Generate YouTube thumbnails.  O(n_plans × pixels)."""
        from modules.adapters.video.thumbnail import ThumbnailGenerator  # noqa: PLC0415
        
        generator = ThumbnailGenerator()
        thumb_dir = Path("data/thumbnails") / run_id
        thumb_dir.mkdir(parents=True, exist_ok=True)

        for plan in plans:
            output_path = thumb_dir / f"{plan.trend_id}.jpg"
            try:
                generator.generate(plan.title, str(output_path))
                logger.info("Stage 8.2 — thumbnail generated: %s", output_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Stage 8.2 — thumbnail failed for %s: %s", plan.trend_id, exc)

    def _generate_subtitles(self, scripts: list[Script], run_id: str) -> None:
        """Stage 8.3: Generate SRT subtitles.  O(n_scripts × words)."""
        from modules.adapters.video.subtitle import SubtitleGenerator  # noqa: PLC0415
        
        generator = SubtitleGenerator()
        subtitle_dir = Path("data/subtitles") / run_id
        subtitle_dir.mkdir(parents=True, exist_ok=True)

        for script in scripts:
            output_path = subtitle_dir / f"{script.plan_id}.srt"
            try:
                # Estimate duration: ~150 wpm
                duration = script.total_words / 2.5
                generator.generate(script.full_text, duration, str(output_path))
                logger.info("Stage 8.3 — subtitles generated: %s", output_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Stage 8.3 — subtitles failed for %s: %s", script.plan_id, exc)

    def _assemble_videos(self, scripts: list[Script], run_id: str) -> None:
        """Stage 8.4 — Video assembly (T-433)."""
        logger.info("Stage 8.4 — assembling %d videos", len(scripts))
        
        # Use GPU-gated factory
        use_sora = os.environ.get("USE_OPEN_SORA", "false").lower() == "true"
        assembler = create_video_backend(
            use_open_sora=use_sora,
            output_dir=os.getenv("YTAIMBOT_DATA_DIR", "data") + "/videos"
        )
        
        for s in scripts:
            try:
                # Find matching plan to get thumbnail
                # (Simplified for MVP)
                # assembler.assemble(...) would be called here
                logger.info("Stage 8.4 — video assembly simulated for %s", s.plan_id)
            except Exception as exc:
                logger.error("Video assembly failed for %s: %s", s.plan_id, exc)

    def _publish_approved(
        self,
        plans: list[ContentPlan],
        reports: list[ComplianceReport],
        run_id: str,
        ppo_state: np.ndarray | None = None,
        ppo_action: int | None = None,
        ppo_prob: float | None = None
    ) -> None:
        """Stage 9: Publish approved content with PPO tracking (T-371)."""
        assert self._publisher is not None
        
        # Get upload count for manual review threshold (T-288)
        upload_count = self._storage.get_upload_count() if hasattr(self._storage, "get_upload_count") else 0

        for plan, report in zip(plans, reports):
            if report.decision == "pass":
                # 1. Similarity check for manual review (T-287)
                archive = self._storage.load_archive() if hasattr(self._storage, "load_archive") else {}
                similarity = self._similarity_gate.check(plan.title, archive)

                # 2. Manual Review (T-286, T-306)
                if self._manual_reviewer is not None:
                    decision = self._manual_reviewer.review(
                        plan=plan,
                        similarity=similarity,
                        upload_count=upload_count,
                        compliance_score=report.score,
                    )
                    if decision != "approve":
                        logger.info("Stage 9 — manual review rejected %s", plan.trend_id)
                        continue

                # 3. Scheduling or direct publishing (T-307)
                success = False
                if self._scheduler is not None:
                    from modules.scheduler import UploadJob
                    # Schedule with 1 hour gap between videos (T-298)
                    scheduled_at = time.time() + (3600 * (upload_count + 1))
                    job = UploadJob(
                        scheduled_at=scheduled_at,
                        plan_id=plan.trend_id,
                        video_path=f"data/videos/{run_id}/{plan.trend_id}.mp4",
                        thumbnail_path=f"data/thumbnails/{run_id}/{plan.trend_id}.jpg",
                        title=plan.title,
                        tags=plan.keywords,
                    )
                    self._scheduler.schedule(job)
                    logger.info("Stage 9 — scheduled %s at %s", plan.trend_id, scheduled_at)
                    success = True
                else:
                    # Fallback to direct publishing
                    success = self._publisher.publish(plan, report)
                    logger.info("Stage 9 — published %s → %s", plan.trend_id, success)
                
                # 4. Save transition for PPO (T-432)
                if success and ppo_state is not None and ppo_action is not None and hasattr(self._storage, "save_ppo_transition"):
                    self._storage.save_ppo_transition(
                        video_id=plan.trend_id,
                        state=ppo_state.tolist(),
                        action_idx=ppo_action,
                        prob=ppo_prob
                    )
                
                upload_count += 1
            else:
                logger.info("Stage 9 — skipped %s (compliance failed)", plan.trend_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _plan_to_features(plan: ContentPlan) -> dict[str, float]:
    """Convert a ContentPlan to feature dict for the Bayes gate.

    All features normalised to [0, 1].
    """
    title_len = min(len(plan.title) / 100.0, 1.0)
    n_keywords = min(len(plan.keywords) / 10.0, 1.0)
    n_outline = min(len(plan.outline) / 10.0, 1.0)
    return {
        "title_length_norm": title_len,
        "keyword_density": n_keywords,
        "outline_depth": n_outline,
    }


def _get_title_optimizer():
    """Lazy-load TitleOptimizer. Returns None if seo package unavailable."""
    try:
        from ytaimbot_ml.seo.title_optimizer import TitleOptimizer  # noqa: PLC0415
        return TitleOptimizer(year=os.environ.get("VIDEO_YEAR", "2026"))
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Module entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    from modules.adapters.synthetic import InMemoryStorage

    seed = int(os.environ.get("YTAIMBOT_SEED", "42"))
    dry_run = os.environ.get("YTAIMBOT_DRY_RUN", "true").lower() != "false"

    source = build_trend_source(seed=seed)
    llm = build_llm_adapter(seed=seed)
    tts = build_tts_adapter()
    storage = InMemoryStorage()
    manual_reviewer = build_manual_reviewer()

    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
        manual_reviewer=manual_reviewer,
        llm=llm,
        tts=tts,
        dry_run=dry_run,
        seed=seed,
    )

    result = pipeline.run(run_id="demo-run-001")
    print(f"Status  : {result.status}")
    print(f"Rankings: {len(result.rankings)}")
    print(f"Plans   : {len(result.plans)}")
    print(f"Reports : {len(result.compliance_reports)}")
    print(f"Scripts : {len(result.scripts)}")
    sys.exit(0 if result.status == "ok" else 1)
