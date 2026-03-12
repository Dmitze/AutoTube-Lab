"""Trie-based content safety blocklist.

Roadmap: T-501–T-510 (Phase 8, EPIC 8.2)

BlocklistTrie: O(m) search where m = pattern length (not list size).
Supports multi-word phrases. Case-insensitive matching.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class TrieNode:
    """Internal Trie node.

    Complexity: O(1) per node creation.
    """

    children: dict[str, TrieNode] = field(default_factory=dict)
    is_end: bool = False
    phrase: str = ""  # full original phrase if is_end


class BlocklistTrie:
    """Trie-based phrase blocklist for content safety.

    Algorithm: Trie insertion O(m), search O(text × m) sliding window
    where m = phrase length (NOT list size n).

    Much faster than linear scan for large lists:
    O(m) lookup vs O(n×m) for set/list search because the Trie shares
    common prefix nodes across all inserted phrases.

    Examples
    --------
    >>> trie = BlocklistTrie()
    >>> trie.insert("self harm")
    >>> trie.search("this content involves self harm")
    True
    >>> trie.find_matches("self harm in video")
    ['self harm']
    >>> trie.search("totally safe content")
    False
    """

    def __init__(self) -> None:
        self._root = TrieNode()
        self._count = 0

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def insert(self, phrase: str) -> None:
        """Insert a phrase into the trie (case-insensitive).

        Parameters
        ----------
        phrase:
            The blocked phrase to add (may contain spaces).

        Complexity: O(m) where m = len(phrase)

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.insert("bad word")
        >>> t.phrase_count
        1
        """
        normalised = phrase.strip().lower()
        if not normalised:
            return
        node = self._root
        for char in normalised:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if not node.is_end:
            node.is_end = True
            node.phrase = normalised
            self._count += 1
            log.debug("BlocklistTrie: inserted %r (total=%d)", normalised, self._count)

    def load_from_list(self, phrases: list[str]) -> None:
        """Bulk-insert phrases from a list.

        Parameters
        ----------
        phrases:
            Sequence of blocked phrase strings.

        Complexity: O(∑ m_i) where m_i = length of each phrase

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.load_from_list(["foo bar", "baz"])
        >>> t.phrase_count
        2
        """
        for phrase in phrases:
            self.insert(phrase)

    def load_from_file(self, path: Path) -> int:
        """Load blocked phrases from a plain-text file (one phrase per line).

        Parameters
        ----------
        path:
            Absolute or relative path to the blocklist text file.
            Lines beginning with ``#`` and blank lines are skipped.

        Returns
        -------
        int
            Number of new phrases loaded from this file.

        Complexity: O(∑ m_i) where m_i = length of each phrase

        Examples
        --------
        >>> import tempfile, pathlib
        >>> p = pathlib.Path(tempfile.mktemp(suffix=".txt"))
        >>> _ = p.write_text("hello world\\nbad phrase\\n")
        >>> t = BlocklistTrie()
        >>> t.load_from_file(p)
        2
        """
        before = self._count
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    self.insert(stripped)
        loaded = self._count - before
        log.info("BlocklistTrie: loaded %d phrases from %s", loaded, path)
        return loaded

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def search(self, text: str) -> bool:
        """Return True if any blocked phrase appears in text.

        Uses a sliding-window scan: for each position in the normalised
        text, walk the trie character-by-character until mismatch or end.

        Parameters
        ----------
        text:
            The text to scan for blocked content.

        Returns
        -------
        bool
            True if at least one blocked phrase is found.

        Complexity: O(|text| × m) where m = max phrase length

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.insert("self harm")
        >>> t.search("video about self harm")
        True
        >>> t.search("totally fine content")
        False
        """
        normalised = text.lower()
        n = len(normalised)
        for start in range(n):
            node = self._root
            for i in range(start, n):
                ch = normalised[i]
                if ch not in node.children:
                    break
                node = node.children[ch]
                if node.is_end:
                    return True
        return False

    def find_matches(self, text: str) -> list[str]:
        """Return all blocked phrases found in text (no duplicates).

        Parameters
        ----------
        text:
            The text to scan.

        Returns
        -------
        list[str]
            Alphabetically-sorted list of matched blocked phrases.

        Complexity: O(|text| × m) where m = max phrase length

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.insert("self harm")
        >>> t.insert("hate speech")
        >>> sorted(t.find_matches("self harm and hate speech here"))
        ['hate speech', 'self harm']
        """
        normalised = text.lower()
        n = len(normalised)
        found: set[str] = set()
        for start in range(n):
            node = self._root
            for i in range(start, n):
                ch = normalised[i]
                if ch not in node.children:
                    break
                node = node.children[ch]
                if node.is_end:
                    found.add(node.phrase)
        return sorted(found)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def phrase_count(self) -> int:
        """Number of phrases currently stored in the trie.

        Complexity: O(1)

        Examples
        --------
        >>> t = BlocklistTrie()
        >>> t.phrase_count
        0
        >>> t.insert("example")
        >>> t.phrase_count
        1
        """
        return self._count
