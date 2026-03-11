"""Bayesian quality / slop filter.

Complexity: O(n_features) per call.

The filter estimates P(bad | features) via Naive-Bayes style conditional
probabilities.  Each feature is assumed independent, and the likelihood
P(feature_i | bad) is modelled with a simple clipped beta approximation
using the feature value itself as a proxy for "badness probability".

Design decisions
----------------
- Fully deterministic — no random state.
- No external network calls.
- Works with any dict of float features in [0, 1].
"""

from __future__ import annotations

import math

from ytaimbot_ml.schemas import ComplianceReport


class BayesQualityFilter:
    """Naive-Bayes quality gate.

    Parameters
    ----------
    prior_bad:
        Prior probability that content is bad.  Defaults to 0.1 (10 %).
    threshold:
        Decision threshold for P(bad | features).  Content is blocked
        when P(bad | features) >= threshold.
    """

    def __init__(self, prior_bad: float = 0.1, threshold: float = 0.5) -> None:
        if not (0.0 < prior_bad < 1.0):
            raise ValueError("prior_bad must be in (0, 1)")
        if not (0.0 < threshold < 1.0):
            raise ValueError("threshold must be in (0, 1)")
        self.prior_bad = prior_bad
        self.threshold = threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, features: dict[str, float]) -> float:
        """Return P(bad | features) in [0, 1].

        Complexity: O(n_features).

        Each feature value is interpreted as a conditional probability
        P(feature_i | bad).  The complementary likelihood is 1 - value.

        Parameters
        ----------
        features:
            Mapping of feature_name → value in [0, 1].  Higher values
            indicate stronger evidence of "bad" content.

        Returns
        -------
        float
            Posterior probability of badness.
        """
        if not features:
            return self.prior_bad

        log_p_bad = math.log(self.prior_bad)
        log_p_good = math.log(1.0 - self.prior_bad)

        for val in features.values():
            val = float(max(1e-9, min(1.0 - 1e-9, val)))
            log_p_bad += math.log(val)
            log_p_good += math.log(1.0 - val)

        # Normalise in log-space to avoid underflow
        max_log = max(log_p_bad, log_p_good)
        p_bad = math.exp(log_p_bad - max_log)
        p_good = math.exp(log_p_good - max_log)
        return p_bad / (p_bad + p_good)

    def decide(self, features: dict[str, float]) -> ComplianceReport:
        """Return a ComplianceReport for the given feature set.

        Complexity: O(n_features).

        Parameters
        ----------
        features:
            Same feature dict as :meth:`score`.

        Returns
        -------
        ComplianceReport
            decision is "pass" if P(bad) < threshold, else "fail".
        """
        p_bad = self.score(features)
        decision = "fail" if p_bad >= self.threshold else "pass"

        reasons: list[str] = []
        if decision == "fail":
            reasons.append(
                f"P(bad|features)={p_bad:.4f} exceeds threshold={self.threshold}"
            )
            # Surface the top-3 most suspicious features
            top = sorted(features.items(), key=lambda kv: kv[1], reverse=True)[:3]
            for name, val in top:
                reasons.append(f"  high '{name}' = {val:.3f}")

        content_hash = _dict_hash(features)
        return ComplianceReport(
            content_hash=content_hash,
            similarity_score=0.0,  # placeholder; set by orchestrator if needed
            bayes_p_bad=p_bad,
            decision=decision,
            reasons=reasons,
        )


class TopicBlacklist:
    """Content safety blacklist that blocks demonetization-risk topics.

    Based on documented YouTube demonetization patterns (2025–2026):
    pregnancy content, visible injuries, unverified health claims,
    minors in problematic contexts, and misinformation-adjacent topics.

    Algorithm: Aho-Corasick multi-pattern matching (simplified: set lookup O(k×n))
    Complexity: O(k × n) where k=patterns, n=text length

    Parameters
    ----------
    custom_patterns:
        Optional extra patterns to add on top of BLOCKED_PATTERNS.

    Examples
    --------
    >>> bl = TopicBlacklist()
    >>> bl.is_safe("cozy village ASMR video")
    True
    >>> bl.is_safe("pregnant woman injured scene")
    False
    """

    BLOCKED_PATTERNS: frozenset[str] = frozenset({
        "pregnant", "pregnancy", "injury", "injuries", "wounded", "bleeding",
        "surgery", "medical advice", "cure disease", "self-harm", "suicide",
        "weapon tutorial", "real news", "breaking news", "actual event",
        "this really happened", "true story", "fact checked",
    })

    def __init__(self, custom_patterns: list[str] | None = None) -> None:
        self._patterns: set[str] = set(self.BLOCKED_PATTERNS)
        if custom_patterns:
            self._patterns.update(p.lower() for p in custom_patterns)

    def is_safe(self, text: str) -> bool:
        """Return True if text contains no blocked patterns.

        Parameters
        ----------
        text:
            Text to scan (title, description, script, etc.).

        Returns
        -------
        bool
            True = safe to publish, False = blocked topic detected.

        Complexity: O(k × n) where k = number of patterns, n = len(text)

        Examples
        --------
        >>> TopicBlacklist().is_safe("peaceful morning ASMR")
        True
        >>> TopicBlacklist().is_safe("breaking news alert")
        False
        """
        lower = text.lower()
        return not any(pattern in lower for pattern in self._patterns)

    def get_violations(self, text: str) -> list[str]:
        """Return all blocked patterns found in text.

        Parameters
        ----------
        text:
            Text to scan.

        Returns
        -------
        list[str]
            Matched blocked patterns (empty if none found).

        Complexity: O(k × n)

        Examples
        --------
        >>> bl = TopicBlacklist()
        >>> bl.get_violations("surgery and medical advice")
        ['surgery', 'medical advice']
        """
        lower = text.lower()
        return sorted(p for p in self._patterns if p in lower)

    def add_pattern(self, pattern: str) -> None:
        """Register an additional blocked pattern at runtime.

        Parameters
        ----------
        pattern:
            New pattern string (case-insensitive match).

        Complexity: O(1)

        Examples
        --------
        >>> bl = TopicBlacklist()
        >>> bl.add_pattern("dangerous stunt")
        >>> bl.is_safe("dangerous stunt video")
        False
        """
        self._patterns.add(pattern.lower())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dict_hash(d: dict[str, float]) -> str:
    """Stable string hash of a feature dict."""
    items = sorted(d.items())
    return hex(hash(str(items)) & 0xFFFFFFFF)
