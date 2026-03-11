"""Phase 3 — TitleOptimizer: SEO-optimized YouTube title generation.

Roadmap tasks: T-137 through T-148 (EPIC 3.1 SEO)
Depends on:   ContentPlan.keywords, ContentPlan.title

Algorithms
----------
1. CTR scoring formula (weighted sum):
     score = 0.40 × keyword_present      # primary keyword in title
           + 0.25 × length_ok            # 40–70 chars → optimal CTR
           + 0.20 × curiosity_gap        # contains "?", "how", "why", etc.
           + 0.10 × starts_power_word    # starts with power word
           + 0.05 × contains_number      # numbers ↑ CTR by ~36%

   All components in [0, 1] → total score in [0, 1]. O(1) per title.

2. Candidate generation (Template Bank):
     - 8 title templates per niche, filled with {keyword} + {title}
     - Templates selected O(1) from pre-built list
     - Best candidate chosen by argmax(score) → O(n_templates)

3. Keyword density check:
     density = keyword_occurrences / word_count
     Target: 0.02 ≤ density ≤ 0.08 (SEO sweet spot)

4. A/B variant generation:
     Produces 3 variants: short (≤50 chars), medium (50–65), long (65–70)
     Caller selects variant based on A/B test result.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ytaimbot_ml.schemas import ContentPlan

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Power words that increase CTR at the start of titles
_POWER_WORDS = frozenset({
    "how", "why", "what", "secret", "proven", "best", "top", "ultimate",
    "complete", "easy", "fast", "free", "new", "simple", "tips", "tricks",
    "guide", "tutorial", "learn", "master", "discover", "surprising",
    "amazing", "incredible", "essential", "must", "never", "always",
    "як", "чому", "що", "кращий", "топ", "повний", "секрет", "навчись",
})

# Curiosity-gap signals (question words, emotional triggers)
_CURIOSITY_WORDS = frozenset({
    "?", "how", "why", "what", "secret", "nobody", "never", "mistake",
    "wrong", "truth", "reveal", "hidden", "forget", "stop", "start",
    "як", "чому", "що", "секрет", "ніхто", "ніколи", "помилка", "правда",
})

# Title templates: {keyword} = primary keyword, {title} = plan title
_TITLE_TEMPLATES: list[str] = [
    "{keyword}: Complete Guide ({year})",
    "How to Master {keyword} in 30 Days",
    "Top 10 {keyword} Tips That Actually Work",
    "{keyword} Tutorial for Beginners — Step by Step",
    "Why {keyword} Will Change Everything in {year}",
    "The Ultimate {keyword} Strategy (Works in {year})",
    "{keyword}: What Nobody Tells You",
    "I Tried {keyword} for 30 Days — Here's What Happened",
    "{keyword} від А до Я — Повний Гайд",
    "Як навчитись {keyword} за 1 тиждень",
    "Топ 10 секретів {keyword} які ніхто не розкаже",
    "{keyword}: Чому всі роблять це неправильно",
]

# Optimal title length range for YouTube CTR
_MIN_TITLE_LEN = 40
_MAX_TITLE_LEN = 70


# ---------------------------------------------------------------------------
# Score result dataclass
# ---------------------------------------------------------------------------


@dataclass
class TitleScore:
    """Detailed CTR score breakdown for a candidate title.

    Attributes
    ----------
    title:
        The candidate title string.
    total:
        Composite score in [0, 1].
    keyword_present:
        1.0 if primary keyword found, 0.0 otherwise.
    length_ok:
        1.0 if 40 ≤ len ≤ 70, partial score for near-optimal.
    curiosity_gap:
        1.0 if curiosity/question signal detected.
    starts_power_word:
        1.0 if title starts with a power word.
    contains_number:
        1.0 if title contains a digit.
    """

    title: str
    total: float = 0.0
    keyword_present: float = 0.0
    length_ok: float = 0.0
    curiosity_gap: float = 0.0
    starts_power_word: float = 0.0
    contains_number: float = 0.0


# ---------------------------------------------------------------------------
# TitleOptimizer
# ---------------------------------------------------------------------------


class TitleOptimizer:
    """SEO-optimized YouTube title generator and scorer.

    Parameters
    ----------
    year:
        Year string injected into templates (default "2026").

    Complexity
    ----------
    optimize():  O(n_templates) — scoring each template
    score():     O(1) — single title evaluation
    variants():  O(n_candidates) — A/B variant selection

    Examples
    --------
    >>> opt = TitleOptimizer(year="2026")
    >>> result = opt.optimize("Python", ["python", "programming"])
    >>> isinstance(result, str) and len(result) > 0
    True
    """

    def __init__(self, year: str = "2026") -> None:
        self.year = year

    def optimize(self, keyword: str, keywords: list[str]) -> str:
        """Generate the highest-scoring title for a keyword.

        Parameters
        ----------
        keyword:
            Primary trend keyword (from ContentPlan.trend_id or title).
        keywords:
            Full keyword list from ContentPlan.keywords.

        Returns
        -------
        str
            Best-scoring title candidate (≤ 70 chars preferred).

        Complexity
        ----------
        O(n_templates) — evaluate all templates, return argmax

        Examples
        --------
        >>> TitleOptimizer().optimize("Python", ["python"])  # doctest: +ELLIPSIS
        '...'
        """
        candidates = self._generate_candidates(keyword)
        scored = [self.score(c, keywords) for c in candidates]
        best = max(scored, key=lambda s: s.total)
        return best.title

    def score(self, title: str, keywords: list[str]) -> TitleScore:
        """Score a single title for CTR potential.

        Parameters
        ----------
        title:
            Title string to evaluate.
        keywords:
            Reference keyword list (primary keyword = keywords[0] if non-empty).

        Returns
        -------
        TitleScore
            Detailed score breakdown.

        Complexity
        ----------
        O(1) — constant number of string operations

        Examples
        --------
        >>> opt = TitleOptimizer()
        >>> s = opt.score("How to Learn Python in 30 Days", ["python"])
        >>> 0.0 <= s.total <= 1.0
        True
        >>> s.contains_number
        1.0
        """
        title_lower = title.lower()
        words = title_lower.split()
        primary = keywords[0].lower() if keywords else ""

        kw_present = 1.0 if primary and primary in title_lower else 0.0

        length = len(title)
        if _MIN_TITLE_LEN <= length <= _MAX_TITLE_LEN:
            length_ok = 1.0
        elif length < _MIN_TITLE_LEN:
            length_ok = length / _MIN_TITLE_LEN
        else:
            over = length - _MAX_TITLE_LEN
            length_ok = max(0.0, 1.0 - over / 30.0)

        curiosity = 1.0 if any(cw in title_lower for cw in _CURIOSITY_WORDS) else 0.0

        starts_power = 1.0 if words and words[0] in _POWER_WORDS else 0.0

        has_number = 1.0 if re.search(r"\d", title) else 0.0

        total = (
            0.40 * kw_present
            + 0.25 * length_ok
            + 0.20 * curiosity
            + 0.10 * starts_power
            + 0.05 * has_number
        )

        return TitleScore(
            title=title,
            total=round(total, 4),
            keyword_present=kw_present,
            length_ok=round(length_ok, 4),
            curiosity_gap=curiosity,
            starts_power_word=starts_power,
            contains_number=has_number,
        )

    def variants(
        self, keyword: str, keywords: list[str]
    ) -> dict[str, str]:
        """Generate 3 A/B title variants: short, medium, long.

        Parameters
        ----------
        keyword:
            Primary keyword.
        keywords:
            Full keyword list.

        Returns
        -------
        dict[str, str]
            Keys: "short" (≤50), "medium" (51–65), "long" (66–70).
            Values: best-scoring title within each length bucket.

        Complexity
        ----------
        O(n_templates)

        Examples
        --------
        >>> vs = TitleOptimizer().variants("Python", ["python"])
        >>> set(vs.keys()) == {"short", "medium", "long"}
        True
        """
        candidates = self._generate_candidates(keyword)
        scored = sorted(
            [self.score(c, keywords) for c in candidates],
            key=lambda s: s.total,
            reverse=True,
        )

        buckets: dict[str, TitleScore | None] = {"short": None, "medium": None, "long": None}
        for s in scored:
            n = len(s.title)
            if n <= 50 and buckets["short"] is None:
                buckets["short"] = s
            elif 51 <= n <= 65 and buckets["medium"] is None:
                buckets["medium"] = s
            elif n > 65 and buckets["long"] is None:
                buckets["long"] = s

        # fallback: fill empty buckets with best overall
        best = scored[0] if scored else TitleScore(title=keyword, total=0.0)
        return {
            k: (v.title if v else best.title)
            for k, v in buckets.items()
        }

    def keyword_density(self, title: str, keyword: str) -> float:
        """Calculate keyword density in title.

        density = occurrences / word_count

        Parameters
        ----------
        title:
            Title string.
        keyword:
            Keyword to check.

        Returns
        -------
        float
            Density value in [0, 1].

        Complexity
        ----------
        O(n_words)

        Examples
        --------
        >>> TitleOptimizer().keyword_density("Python Python tutorial", "python")
        0.6666666666666666
        """
        words = title.lower().split()
        if not words:
            return 0.0
        count = sum(1 for w in words if keyword.lower() in w)
        return count / len(words)

    def optimize_from_plan(self, plan: ContentPlan) -> str:
        """Optimize title directly from a ContentPlan.

        Parameters
        ----------
        plan:
            ContentPlan with trend_id, title, keywords.

        Returns
        -------
        str
            Optimized title string.

        Complexity
        ----------
        O(n_templates)

        Examples
        --------
        >>> from ytaimbot_ml.schemas import ContentPlan
        >>> plan = ContentPlan("t1", "Python tips", [], ["python"])
        >>> opt = TitleOptimizer()
        >>> title = opt.optimize_from_plan(plan)
        >>> "python" in title.lower() or "Python" in title
        True
        """
        keyword = plan.keywords[0] if plan.keywords else plan.trend_id
        return self.optimize(keyword, plan.keywords)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_candidates(self, keyword: str) -> list[str]:
        """Expand all title templates with the given keyword. O(n_templates)."""
        capitalized = keyword.strip().title()
        return [
            t.format(keyword=capitalized, title=capitalized, year=self.year)
            for t in _TITLE_TEMPLATES
        ]

