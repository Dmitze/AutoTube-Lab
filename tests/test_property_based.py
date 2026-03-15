"""Property-based invariants for core pipeline components (Phase 9)."""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings, strategies as st

from modules.adapters.cache import TrendCache
from ytaimbot_ml.quality.bayes_filter import BayesQualityFilter
from ytaimbot_ml.quality.evidence import EvidenceArtifact, EvidenceChain
from ytaimbot_ml.rl.ucb1_bandit import UCB1Bandit
from ytaimbot_ml.schemas import TrendSignal
from ytaimbot_ml.trend_analyzer import TrendAnalyzer
from ytaimbot_ml.utils.random import make_rng


@settings(max_examples=80, deadline=None)
@given(
    st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=25,
    )
)
def test_property_trend_analyzer_rankings_always_sorted(raw_scores: list[float]) -> None:
    """TrendAnalyzer output scores are always sorted descending."""
    signals = [
        TrendSignal(
            trend_id=f"t{i}",
            keyword=f"kw{i}",
            raw_score=float(score),
            source="prop-test",
            timestamp="2026-01-01T00:00:00Z",
        )
        for i, score in enumerate(raw_scores)
    ]
    analyzer = TrendAnalyzer(rng=make_rng(42))
    rankings = analyzer.analyze(signals)
    scores = [r.score for r in rankings]
    assert scores == sorted(scores, reverse=True)


@settings(max_examples=100, deadline=None)
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=12),
        values=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=12,
    )
)
def test_property_bayes_score_is_bounded(features: dict[str, float]) -> None:
    """BayesQualityFilter score and report probability stay in [0.0, 1.0]."""
    filt = BayesQualityFilter(prior_bad=0.1, threshold=0.5)
    p_bad = filt.score(features)
    report = filt.decide(features)
    assert 0.0 <= p_bad <= 1.0
    assert 0.0 <= report.bayes_p_bad <= 1.0


@settings(max_examples=80, deadline=None)
@given(
    st.lists(
        st.text(min_size=1, max_size=10),
        min_size=1,
        max_size=8,
        unique=True,
    ),
    st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=8,
        max_size=24,
    ),
)
def test_property_ucb1_select_returns_valid_arm(arm_ids: list[str], rewards: list[float]) -> None:
    """UCB1 select() always returns an arm from its configured set."""
    bandit = UCB1Bandit(arm_ids=arm_ids, rng=make_rng(42))
    for reward in rewards:
        arm = bandit.select()
        assert arm in arm_ids
        bandit.update(arm, float(reward))


@settings(max_examples=80, deadline=None)
@given(
    st.text(min_size=1, max_size=20),
    st.integers(min_value=-10_000, max_value=10_000),
)
def test_property_cache_get_after_put_returns_value(key: str, value: int) -> None:
    """LRU cache invariant: get(key) after put(key, value) returns same value."""
    cache: TrendCache[int] = TrendCache(capacity=16, ttl_seconds=30)
    cache.put(key, value)
    assert cache.get(key) == value


@settings(max_examples=60, deadline=None)
@given(
    st.lists(st.text(min_size=1, max_size=12), min_size=1, max_size=10),
    st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=10,
        max_size=20,
    ),
)
def test_property_evidence_chain_valid_sequence_verifies(
    ids: list[str],
    scores: list[float],
) -> None:
    """EvidenceChain invariant: valid append sequence always verifies True."""
    chain = EvidenceChain()
    for idx, video_id in enumerate(ids):
        a = EvidenceArtifact.create(
            video_id=f"{video_id}-{idx}",
            script_hash=f"hash-{idx}",
            similarity_score=float(scores[idx % len(scores)]),
            bayes_score=float(scores[(idx + 1) % len(scores)]),
            operator_decision="approve",
            previous_hash=chain.last_hash,
        )
        chain.append(a)
    assert chain.verify_chain() is True

