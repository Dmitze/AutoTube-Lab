"""Shared text utilities for the ytaimbot_ml package.

Used by: ScriptGenerator, TitleOptimizer, KeywordScorer

Functions
---------
sanitize(text)          : remove control chars, normalize whitespace → O(n)
truncate(text, max_len) : truncate to word boundary ≤ max_len chars  → O(n)
normalize_keyword(kw)   : lowercase, strip, collapse spaces          → O(n)
count_words(text)       : fast word count via split()                → O(n)
extract_keywords(text)  : naive keyword extraction (stopword filter) → O(n)
"""
from __future__ import annotations

import re
import unicodedata

# Common English/Ukrainian stopwords to filter out during keyword extraction
_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "it", "its", "be", "are",
    "was", "were", "been", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "that", "this",
    "these", "those", "i", "you", "he", "she", "we", "they", "my", "your",
    # Ukrainian stopwords
    "і", "в", "на", "з", "що", "як", "не", "до", "це", "та", "він",
    "вона", "вони", "ми", "ви", "я",
})


def sanitize(text: str) -> str:
    """Remove control characters and normalize whitespace.

    Strips Unicode control characters (category Cc/Cf), normalizes all
    whitespace sequences to a single space, and strips leading/trailing
    whitespace.

    Complexity: O(n) where n = len(text)

    Parameters
    ----------
    text:
        Raw input string (may contain control chars, extra spaces).

    Returns
    -------
    str
        Cleaned string safe for LLM prompts and SEO fields.

    Examples
    --------
    >>> sanitize("Hello\\x00 World\\n\\t!")
    'Hello World !'
    >>> sanitize("  multiple   spaces  ")
    'multiple spaces'
    """
    # Remove control characters (Unicode categories Cc and Cf)
    cleaned = "".join(
        ch for ch in text
        if unicodedata.category(ch) not in ("Cc", "Cf") or ch in (" ", "\n", "\t")
    )
    # Collapse all whitespace sequences to single space
    return re.sub(r"\s+", " ", cleaned).strip()


def truncate(text: str, max_len: int = 500) -> str:
    """Truncate text to at most max_len characters at a word boundary.

    Never cuts mid-word: walks back to the last space before max_len.
    Returns the original string if len(text) <= max_len.

    Complexity: O(n) where n = len(text)

    Parameters
    ----------
    text:
        Input string to truncate.
    max_len:
        Maximum number of characters in the result. Default 500.

    Returns
    -------
    str
        Truncated string ≤ max_len characters (ending at word boundary).

    Examples
    --------
    >>> truncate("Hello World", max_len=7)
    'Hello'
    >>> truncate("Hi", max_len=100)
    'Hi'
    >>> truncate("Hello World", max_len=11)
    'Hello World'
    """
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    boundary = cut.rfind(" ")
    return cut[:boundary].rstrip() if boundary > 0 else cut


def normalize_keyword(kw: str) -> str:
    """Lowercase, strip, and collapse internal whitespace.

    Suitable for building a keyword index or comparing trend keywords
    case-insensitively.

    Complexity: O(n) where n = len(kw)

    Parameters
    ----------
    kw:
        Raw keyword string.

    Returns
    -------
    str
        Normalized keyword (lowercase, stripped, single-spaced).

    Examples
    --------
    >>> normalize_keyword("  Studio Ghibli  ")
    'studio ghibli'
    >>> normalize_keyword("COZY\\tASMR")
    'cozy asmr'
    """
    return re.sub(r"\s+", " ", kw.lower().strip())


def count_words(text: str) -> int:
    """Count words in text via split().

    Handles multiple whitespace separators, leading/trailing whitespace.
    Returns 0 for empty or whitespace-only strings.

    Complexity: O(n) where n = len(text)

    Parameters
    ----------
    text:
        Input string.

    Returns
    -------
    int
        Number of whitespace-separated tokens.

    Examples
    --------
    >>> count_words("Hello World")
    2
    >>> count_words("  one  two   three  ")
    3
    >>> count_words("")
    0
    """
    return len(text.split())


def extract_keywords(text: str, max_keywords: int = 20) -> list[str]:
    """Extract unique non-stopword keywords from text.

    Algorithm:
    1. Lowercase and tokenize on non-alphanumeric boundaries
    2. Filter: length ≥ 3 and not in _STOPWORDS
    3. Deduplicate (preserve first-occurrence order)
    4. Return up to max_keywords tokens

    Complexity: O(n × k) where n = len(text), k = |_STOPWORDS| ≈ O(n)

    Parameters
    ----------
    text:
        Input text (script, title, description).
    max_keywords:
        Maximum number of keywords to return. Default 20.

    Returns
    -------
    list[str]
        Ordered list of unique keywords (lowercase, ≥ 3 chars).

    Examples
    --------
    >>> kws = extract_keywords("Ghibli cozy ASMR is a great niche for YouTube")
    >>> "ghibli" in kws and "asmr" in kws
    True
    >>> "is" in kws
    False
    """
    tokens = re.findall(r"[a-zA-Zа-яА-ЯіІїЇєЄёЁ0-9]+", text.lower())
    seen: set[str] = set()
    result: list[str] = []
    for tok in tokens:
        if len(tok) >= 3 and tok not in _STOPWORDS and tok not in seen:
            seen.add(tok)
            result.append(tok)
        if len(result) >= max_keywords:
            break
    return result

