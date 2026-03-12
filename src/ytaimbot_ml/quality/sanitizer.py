"""ContentSanitizer: removes blocked content from scripts using BlocklistTrie.

Roadmap: T-503–T-504 (Phase 8)
Uses BlocklistTrie for O(m) detection, replaces matches with [REMOVED].
"""
from __future__ import annotations

import logging
from pathlib import Path

from ytaimbot_ml.quality.blocklist import BlocklistTrie

log = logging.getLogger(__name__)

_DEFAULT_BLOCKLIST_PATH = Path(__file__).parent / "blocklist.txt"
_REPLACEMENT = "[REMOVED]"


class ContentSanitizer:
    """Sanitizes script/description text using BlocklistTrie.

    Loads the default ``blocklist.txt`` from the quality package directory
    unless a custom ``BlocklistTrie`` is supplied.

    Algorithm: O(n × m) where n = text length, m = max phrase length

    Examples
    --------
    >>> sanitizer = ContentSanitizer()
    >>> sanitizer.sanitize_script("This video has no banned content")
    'This video has no banned content'
    >>> sanitizer.is_safe("clean Ghibli ASMR story")
    True
    """

    def __init__(self, trie: BlocklistTrie | None = None) -> None:
        """Initialise with an optional pre-built trie.

        Parameters
        ----------
        trie:
            A pre-populated ``BlocklistTrie``.  When ``None``, the default
            ``blocklist.txt`` is loaded automatically.

        Complexity: O(∑ m_i) for file loading, O(1) when trie is provided.
        """
        if trie is not None:
            self._trie = trie
        else:
            self._trie = BlocklistTrie()
            if _DEFAULT_BLOCKLIST_PATH.exists():
                count = self._trie.load_from_file(_DEFAULT_BLOCKLIST_PATH)
                log.info("ContentSanitizer: loaded %d phrases from default blocklist", count)
            else:
                log.warning(
                    "ContentSanitizer: default blocklist not found at %s",
                    _DEFAULT_BLOCKLIST_PATH,
                )

    def sanitize_script(self, text: str) -> str:
        """Replace all blocked phrases in *text* with ``[REMOVED]``.

        Replacement is case-insensitive and preserves surrounding text.
        Overlapping phrases are each independently replaced left-to-right.

        Parameters
        ----------
        text:
            Raw script or description text to sanitize.

        Returns
        -------
        str
            Sanitized text with blocked phrases replaced.

        Complexity: O(n × m) where n = len(text), m = max phrase length

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.insert("bad phrase")
        >>> s = ContentSanitizer(trie=t)
        >>> s.sanitize_script("This has a bad phrase inside")
        'This has a [REMOVED] inside'
        """
        matches = self._trie.find_matches(text)
        result = text
        for match in matches:
            # Case-insensitive replacement preserving order
            lower = result.lower()
            while match in lower:
                idx = lower.index(match)
                result = result[:idx] + _REPLACEMENT + result[idx + len(match):]
                lower = result.lower()
        if matches:
            log.debug(
                "ContentSanitizer: replaced %d phrase(s): %s",
                len(matches),
                matches,
            )
        return result

    def is_safe(self, text: str) -> bool:
        """Return True if no blocked phrases are found in *text*.

        Parameters
        ----------
        text:
            Text to check.

        Returns
        -------
        bool
            True = no violations found, False = at least one match.

        Complexity: O(n × m)

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.insert("danger")
        >>> s = ContentSanitizer(trie=t)
        >>> s.is_safe("a safe story")
        True
        >>> s.is_safe("danger ahead")
        False
        """
        return not self._trie.search(text)

    def get_violations(self, text: str) -> list[str]:
        """Return sorted list of blocked phrases found in *text*.

        Parameters
        ----------
        text:
            Text to inspect.

        Returns
        -------
        list[str]
            Alphabetically-sorted blocked phrases found (empty if clean).

        Complexity: O(n × m)

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.insert("foo")
        >>> t.insert("bar")
        >>> s = ContentSanitizer(trie=t)
        >>> s.get_violations("foo and bar together")
        ['bar', 'foo']
        """
        return self._trie.find_matches(text)
