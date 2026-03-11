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

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from modules.adapters.base import (
    LLMAdapter,
    PublisherAdapter,
    StorageAdapter,
    TTSAdapter,
    TrendSourceAdapter,
)
from ytaimbot_ml.quality.bayes_filter import BayesQualityFilter
from ytaimbot_ml.schemas import (
    ComplianceReport,
    ContentPlan,
    PipelineResult,
    Script,
    TrendRanking,
    TrendSignal,
    UploadResult,
)
from ytaimbot_ml.trend_analyzer import TrendAnalyzer
from ytaimbot_ml.utils.random import make_rng

logger = logging.getLogger(__name__)


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
    | No                       | Yes → GoogleTrendsTrendSource |
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
        from modules.adapters.google_trends import GoogleTrendsTrendSource
        from modules.adapters.youtube_search import YouTubeSearchTrendSource

        geo = os.environ["GOOGLE_TRENDS_GEO"]
        weight_str = os.environ.get("ADAPTER_WEIGHTS", "1.0,1.0").split(",")
        w_gt = float(weight_str[0]) if len(weight_str) > 0 else 1.0
        w_yt = float(weight_str[1]) if len(weight_str) > 1 else 1.0

        logger.info("TrendSource: CompositeTrendSource (GoogleTrends + YouTube)")
        return CompositeTrendSource(
            adapters=[
                (GoogleTrendsTrendSource(geo=geo, seed=seed), w_gt),
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
        from modules.adapters.google_trends import GoogleTrendsTrendSource
        geo = os.environ["GOOGLE_TRENDS_GEO"]
        logger.info("TrendSource: GoogleTrendsTrendSource (geo=%s)", geo)
        return GoogleTrendsTrendSource(geo=geo, seed=seed)

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
    """Build EdgeTTSAdapter if edge-tts is installed.

    Falls back to None if edge-tts package is missing (TTS stage skipped).

    Returns
    -------
    TTSAdapter | None
        Configured adapter, or None if edge-tts not available.

    Complexity
    ----------
    O(1)

    Examples
    --------
    >>> adapter = build_tts_adapter()
    >>> adapter is None or hasattr(adapter, 'speak')
    True
    """
    try:
        import edge_tts  # noqa: F401  — just checking availability
        from modules.adapters.tts.edge_tts import EdgeTTSAdapter
        logger.info("TTS: EdgeTTSAdapter (voice=%s)", os.environ.get("TTS_VOICE", "uk-UA-OstapNeural"))
        return EdgeTTSAdapter()
    except ImportError:
        logger.info("TTS: edge-tts not installed — audio synthesis disabled")
        return None


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
        llm: Optional[LLMAdapter] = None,
        tts: Optional[TTSAdapter] = None,
        dry_run: bool = True,
        seed: int = 42,
        audio_dir: str | Path = "data/audio",
    ) -> None:
        self._source = trend_source
        self._storage = storage
        self._publisher = publisher
        self._llm = llm
        self._tts = tts
        self._dry_run = dry_run
        self._seed = seed
        self._rng = make_rng(seed)
        self._analyzer = TrendAnalyzer(rng=make_rng(seed))
        self._gate = BayesQualityFilter()
        self._audio_dir = Path(audio_dir)

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
        logger.info(
            "Pipeline run %s started (dry_run=%s, llm=%s, tts=%s)",
            run_id,
            self._dry_run,
            self._llm.__class__.__name__ if self._llm else "disabled",
            self._tts.__class__.__name__ if self._tts else "disabled",
        )

        result = PipelineResult(run_id=run_id)

        try:
            # Stage 1: ingest
            signals = self._ingest()
            self._storage.save_trends(run_id, signals)

            # Stages 2–4: featurize → reduce → score
            rankings = self._score(signals)
            result.rankings = rankings

            # Stage 5: plan
            plans = self._plan(rankings)
            result.plans = plans

            # Stage 6: gate
            reports = self._gate_all(plans)
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

            # Stage 9: publish (fail-closed)
            if not self._dry_run and self._publisher is not None:
                self._publish_approved(plans, reports)

            result.status = "ok"

        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline run %s failed: %s", run_id, exc)
            result.status = "error"

        self._storage.save_run(run_id, result.status)
        logger.info("Pipeline run %s finished → status=%s", run_id, result.status)
        return result

    # ------------------------------------------------------------------
    # Private stage implementations
    # ------------------------------------------------------------------

    def _ingest(self) -> list[TrendSignal]:
        signals = self._source.fetch()
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

    def _publish_approved(
        self,
        plans: list[ContentPlan],
        reports: list[ComplianceReport],
    ) -> None:
        """Stage 9: Publish only plans whose compliance report is 'pass'."""
        assert self._publisher is not None
        for plan, report in zip(plans, reports):
            if report.decision == "pass":
                ok = self._publisher.publish(plan, report)
                logger.info("Stage 9 — published %s → %s", plan.trend_id, ok)
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

    from modules.adapters.synthetic import InMemoryStorage, SyntheticTrendSource

    seed = int(os.environ.get("YTAIMBOT_SEED", "42"))
    dry_run = os.environ.get("YTAIMBOT_DRY_RUN", "true").lower() != "false"

    source = build_trend_source(seed=seed)
    llm = build_llm_adapter(seed=seed)
    tts = build_tts_adapter()
    storage = InMemoryStorage()

    pipeline = Pipeline(
        trend_source=source,
        storage=storage,
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
