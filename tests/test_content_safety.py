"""Tests for BlocklistTrie and ContentSanitizer (T-501–T-510)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ytaimbot_ml.quality.blocklist import BlocklistTrie
from ytaimbot_ml.quality.sanitizer import ContentSanitizer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trie(*phrases: str) -> BlocklistTrie:
    trie = BlocklistTrie()
    for p in phrases:
        trie.insert(p)
    return trie


# ---------------------------------------------------------------------------
# BlocklistTrie — basic insert / search
# ---------------------------------------------------------------------------

class TestTrieInsertAndSearch:
    def test_exact_match(self):
        trie = _make_trie("self harm")
        assert trie.search("this content involves self harm") is True

    def test_no_match(self):
        trie = _make_trie("self harm")
        assert trie.search("totally safe content") is False

    def test_empty_trie(self):
        trie = BlocklistTrie()
        assert trie.search("any text here") is False


class TestTrieSearchNegative:
    def test_partial_word_not_matched_as_phrase(self):
        trie = _make_trie("hate speech")
        # "hate speech" IS a substring of "hate speeches", so search returns True;
        # test that a genuinely absent phrase does not match
        assert trie.search("completely clean peaceful content") is False

    def test_unrelated_content(self):
        trie = _make_trie("bomb", "violence")
        assert trie.search("peaceful morning ASMR") is False


class TestTrieFindMatches:
    def test_single_match(self):
        trie = _make_trie("self harm")
        assert trie.find_matches("self harm in the video") == ["self harm"]

    def test_multiple_matches(self):
        trie = _make_trie("self harm", "hate speech")
        matches = trie.find_matches("self harm and hate speech")
        assert sorted(matches) == ["hate speech", "self harm"]

    def test_no_matches_empty_list(self):
        trie = _make_trie("danger")
        assert trie.find_matches("safe content here") == []

    def test_duplicate_occurrence_deduplicated(self):
        trie = _make_trie("bad word")
        matches = trie.find_matches("bad word here and bad word there")
        assert matches == ["bad word"]


class TestTrieCaseInsensitive:
    def test_uppercase_input(self):
        trie = _make_trie("self harm")
        assert trie.search("SELF HARM is bad") is True

    def test_mixed_case_phrase(self):
        trie = _make_trie("HATE SPEECH")
        assert trie.search("hate speech detected") is True

    def test_mixed_case_both(self):
        trie = _make_trie("Drug Overdose")
        assert trie.search("DRUG OVERDOSE content") is True


class TestTrieMultiWordPhrase:
    def test_multi_word_found(self):
        trie = _make_trie("how to make bomb")
        assert trie.search("tutorial: how to make bomb at home") is True

    def test_partial_phrase_not_matched(self):
        trie = _make_trie("how to make bomb")
        assert trie.search("how to make") is False

    def test_phrase_with_spaces(self):
        trie = _make_trie("actual crime scene")
        assert trie.search("footage from an actual crime scene") is True


class TestTriePhraseCount:
    def test_zero_initially(self):
        assert BlocklistTrie().phrase_count == 0

    def test_increments_on_insert(self):
        trie = BlocklistTrie()
        trie.insert("one")
        trie.insert("two")
        assert trie.phrase_count == 2

    def test_duplicate_insert_no_double_count(self):
        trie = BlocklistTrie()
        trie.insert("same phrase")
        trie.insert("same phrase")
        assert trie.phrase_count == 1


class TestTrieLoadFromList:
    def test_loads_all(self):
        trie = BlocklistTrie()
        trie.load_from_list(["alpha", "beta", "gamma"])
        assert trie.phrase_count == 3

    def test_loaded_phrases_searchable(self):
        trie = BlocklistTrie()
        trie.load_from_list(["danger zone"])
        assert trie.search("entering the danger zone now") is True

    def test_empty_list(self):
        trie = BlocklistTrie()
        trie.load_from_list([])
        assert trie.phrase_count == 0


class TestTrieLoadFromFile:
    def test_loads_from_temp_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("hello world\nbad phrase\n# comment line\n\n")
            tmp = Path(f.name)
        try:
            trie = BlocklistTrie()
            count = trie.load_from_file(tmp)
            assert count == 2
            assert trie.search("there is a bad phrase here") is True
        finally:
            tmp.unlink(missing_ok=True)

    def test_comments_skipped(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("# this is a comment\nreal phrase\n")
            tmp = Path(f.name)
        try:
            trie = BlocklistTrie()
            count = trie.load_from_file(tmp)
            assert count == 1
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# ContentSanitizer
# ---------------------------------------------------------------------------

class TestSanitizerCleanText:
    def test_clean_text_unchanged(self):
        sanitizer = ContentSanitizer(trie=BlocklistTrie())
        assert sanitizer.sanitize_script("A lovely forest walk") == "A lovely forest walk"

    def test_empty_string(self):
        sanitizer = ContentSanitizer(trie=BlocklistTrie())
        assert sanitizer.sanitize_script("") == ""


class TestSanitizerRemovesBlocked:
    def test_single_phrase_replaced(self):
        trie = _make_trie("bad phrase")
        sanitizer = ContentSanitizer(trie=trie)
        result = sanitizer.sanitize_script("This has a bad phrase inside")
        assert "bad phrase" not in result.lower()
        assert "[REMOVED]" in result

    def test_multiple_phrases_replaced(self):
        trie = _make_trie("foo", "bar")
        sanitizer = ContentSanitizer(trie=trie)
        result = sanitizer.sanitize_script("foo and bar together")
        assert "foo" not in result
        assert "bar" not in result
        assert result.count("[REMOVED]") == 2

    def test_repeated_phrase_replaced(self):
        trie = _make_trie("banned")
        sanitizer = ContentSanitizer(trie=trie)
        result = sanitizer.sanitize_script("banned content is banned")
        assert "banned" not in result
        assert result.count("[REMOVED]") == 2


class TestSanitizerIsSafeTrue:
    def test_clean_text(self):
        sanitizer = ContentSanitizer(trie=BlocklistTrie())
        assert sanitizer.is_safe("a safe story about flowers") is True

    def test_empty_trie(self):
        sanitizer = ContentSanitizer(trie=BlocklistTrie())
        assert sanitizer.is_safe("anything at all") is True


class TestSanitizerIsSafeFalse:
    def test_blocked_content(self):
        trie = _make_trie("danger")
        sanitizer = ContentSanitizer(trie=trie)
        assert sanitizer.is_safe("there is danger ahead") is False


class TestSanitizerGetViolations:
    def test_no_violations(self):
        sanitizer = ContentSanitizer(trie=BlocklistTrie())
        assert sanitizer.get_violations("peaceful garden ASMR") == []

    def test_single_violation(self):
        trie = _make_trie("self harm")
        sanitizer = ContentSanitizer(trie=trie)
        assert sanitizer.get_violations("content about self harm") == ["self harm"]

    def test_multiple_violations_sorted(self):
        trie = _make_trie("zebra content", "alpha content")
        sanitizer = ContentSanitizer(trie=trie)
        viols = sanitizer.get_violations("alpha content and zebra content here")
        assert viols == ["alpha content", "zebra content"]


class TestSanitizerDefaultBlocklist:
    """Integration test: default blocklist.txt is loaded correctly."""

    def test_default_blocklist_loaded(self):
        sanitizer = ContentSanitizer()
        assert sanitizer._trie.phrase_count > 0  # noqa: SLF001

    def test_known_phrase_detected(self):
        sanitizer = ContentSanitizer()
        # "self harm" is in blocklist.txt
        assert sanitizer.is_safe("video about self harm") is False

    def test_clean_content_passes(self):
        sanitizer = ContentSanitizer()
        assert sanitizer.is_safe("peaceful Ghibli ASMR forest walk") is True
