"""Pre-publish compliance checker for YouTube Terms of Service.

Roadmap: T-515–T-517 (Phase 8, EPIC 8.3)

Checks:
1. AI disclosure present in description
2. No PII (email, phone) in script
3. TopicBlacklist passes (from bayes_filter.py)
4. Video duration >= 8 minutes (if provided)
5. Age disclaimer present in description
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ytaimbot_ml.quality.bayes_filter import TopicBlacklist

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComplianceResult:
    """Result of a compliance check.

    Complexity: O(1) creation.

    Examples
    --------
    >>> r = ComplianceResult.ok()
    >>> r.passed
    True
    >>> r = ComplianceResult.fail(["missing disclosure"])
    >>> r.passed
    False
    >>> r.violations
    ['missing disclosure']
    """

    passed: bool
    violations: list[str]  # human-readable violation descriptions
    checked_at: str        # ISO-8601 UTC

    @classmethod
    def ok(cls) -> ComplianceResult:
        """Create a passing ComplianceResult with no violations.

        Returns
        -------
        ComplianceResult
            A result with ``passed=True`` and an empty violations list.

        Complexity: O(1)

        Examples
        --------
        >>> ComplianceResult.ok().passed
        True
        """
        return cls(
            passed=True,
            violations=[],
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def fail(cls, violations: list[str]) -> ComplianceResult:
        """Create a failing ComplianceResult with the given violations.

        Parameters
        ----------
        violations:
            Non-empty list of human-readable violation descriptions.

        Returns
        -------
        ComplianceResult
            A result with ``passed=False``.

        Complexity: O(1)

        Examples
        --------
        >>> ComplianceResult.fail(["pii detected"]).passed
        False
        """
        return cls(
            passed=False,
            violations=violations,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )


class ComplianceChecker:
    """Automated pre-publish compliance checklist for YouTube ToS.

    Runs five sequential checks before allowing publication:

    1. **AI disclosure** — description must contain at least one keyword
       indicating AI-generated content (required since 2024).
    2. **PII scan** — script and description must not contain email
       addresses or phone numbers.
    3. **Topic safety** — ``TopicBlacklist`` must find no demonetization
       triggers in the combined text.
    4. **Duration** — video duration must be ≥ ``min_duration_seconds``
       (default 480 s / 8 min) when provided.
    5. **Age disclaimer** — description must mention ``"18+"`` or
       ``"adults"`` to satisfy character-age requirements.

    Algorithm: O(n) per check where n = text length.

    Examples
    --------
    >>> checker = ComplianceChecker()
    >>> result = checker.check(
    ...     description="AI-generated content. All characters are adults 18+.",
    ...     script="A cozy Ghibli ASMR story.",
    ...     duration_seconds=600,
    ... )
    >>> result.passed
    True
    """

    MIN_DURATION_SECONDS: int = 480  # 8 minutes

    _EMAIL_RE: re.Pattern[str] = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )
    _PHONE_RE: re.Pattern[str] = re.compile(
        r"\b(?:\+?\d[\d\s\-().]{6,}\d)\b"
    )
    _DISCLOSURE_KEYWORDS: list[str] = [
        "ai-generated",
        "ai generated",
        "artificial intelligence",
        "created with ai",
        "ai content",
        "🤖",
    ]

    def __init__(
        self,
        min_duration_seconds: int = MIN_DURATION_SECONDS,
        require_age_disclaimer: bool = True,
        require_ai_disclosure: bool = True,
    ) -> None:
        """Initialise the checker with configurable thresholds.

        Parameters
        ----------
        min_duration_seconds:
            Minimum allowed video duration in seconds (default: 480).
        require_age_disclaimer:
            When True (default), enforce the age-disclaimer check.
        require_ai_disclosure:
            When True (default), enforce the AI-disclosure check.

        Complexity: O(1)
        """
        self._min_duration = min_duration_seconds
        self._require_age_disclaimer = require_age_disclaimer
        self._require_ai_disclosure = require_ai_disclosure
        self._blacklist = TopicBlacklist()

    def check(
        self,
        description: str,
        script: str = "",
        duration_seconds: float | None = None,
    ) -> ComplianceResult:
        """Run all enabled compliance checks and return a consolidated result.

        Parameters
        ----------
        description:
            YouTube video description text.
        script:
            Video script text (checked for PII and topic safety).
        duration_seconds:
            Video duration in seconds; pass ``None`` to skip that check.

        Returns
        -------
        ComplianceResult
            Passes only when every enabled check finds no violations.

        Complexity: O(n) where n = max(len(description), len(script))

        Examples
        --------
        >>> c = ComplianceChecker()
        >>> c.check(
        ...     description="AI-generated. Adults 18+ only.",
        ...     script="Relaxing forest sounds.",
        ...     duration_seconds=500,
        ... ).passed
        True
        """
        violations: list[str] = []

        combined = f"{description} {script}"

        if self._require_ai_disclosure:
            v = self._check_ai_disclosure(description)
            if v:
                violations.append(v)

        v = self._check_pii(combined)
        if v:
            violations.append(v)

        v = self._check_topic_safety(combined)
        if v:
            violations.append(v)

        if duration_seconds is not None:
            v = self._check_duration(duration_seconds)
            if v:
                violations.append(v)

        if self._require_age_disclaimer:
            v = self._check_age_disclaimer(description)
            if v:
                violations.append(v)

        if violations:
            log.info(
                "ComplianceChecker: FAIL (%d violation(s)): %s",
                len(violations),
                violations,
            )
            return ComplianceResult.fail(violations)

        log.info("ComplianceChecker: PASS")
        return ComplianceResult.ok()

    def _check_ai_disclosure(self, description: str) -> str | None:
        """Return a violation message if AI disclosure is missing.

        Parameters
        ----------
        description:
            Video description to inspect.

        Returns
        -------
        str | None
            Violation string, or ``None`` if disclosure is present.

        Complexity: O(n) where n = len(description)
        """
        lower = description.lower()
        if any(kw in lower for kw in self._DISCLOSURE_KEYWORDS):
            return None
        return (
            "AI disclosure missing: description must contain one of "
            + str(self._DISCLOSURE_KEYWORDS)
        )

    def _check_pii(self, text: str) -> str | None:
        """Return a violation message if PII is found in text.

        Detects email addresses and phone numbers via regex.

        Parameters
        ----------
        text:
            Combined description + script text to inspect.

        Returns
        -------
        str | None
            Violation string listing found PII types, or ``None`` if clean.

        Complexity: O(n) where n = len(text)
        """
        found: list[str] = []
        if self._EMAIL_RE.search(text):
            found.append("email address")
        if self._PHONE_RE.search(text):
            found.append("phone number")
        if found:
            return f"PII detected: {', '.join(found)}"
        return None

    def _check_age_disclaimer(self, description: str) -> str | None:
        """Return a violation if age disclaimer is absent from description.

        Checks for ``"18+"`` or ``"adults"`` (case-insensitive).

        Parameters
        ----------
        description:
            YouTube description text.

        Returns
        -------
        str | None
            Violation string, or ``None`` if disclaimer is found.

        Complexity: O(n) where n = len(description)
        """
        lower = description.lower()
        if "18+" in lower or "adults" in lower:
            return None
        return "Age disclaimer missing: description must include '18+' or 'adults'"

    def _check_duration(self, duration_seconds: float) -> str | None:
        """Return a violation if duration is below the minimum.

        Parameters
        ----------
        duration_seconds:
            Video duration in seconds.

        Returns
        -------
        str | None
            Violation string, or ``None`` if duration is acceptable.

        Complexity: O(1)
        """
        if duration_seconds < self._min_duration:
            return (
                f"Duration too short: {duration_seconds:.0f}s < "
                f"{self._min_duration}s minimum"
            )
        return None

    def _check_topic_safety(self, text: str) -> str | None:
        """Return a violation if TopicBlacklist detects demonetization triggers.

        Parameters
        ----------
        text:
            Combined text to scan (description + script).

        Returns
        -------
        str | None
            Violation string naming detected triggers, or ``None`` if safe.

        Complexity: O(k × n) where k = number of blacklist patterns
        """
        hits = self._blacklist.get_violations(text)
        if hits:
            return f"Demonetization topics detected: {hits}"
        return None
