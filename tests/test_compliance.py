"""Tests for EvidenceChain and ComplianceChecker (T-511–T-517)."""
from __future__ import annotations

import dataclasses

import pytest

from ytaimbot_ml.quality.compliance import ComplianceChecker, ComplianceResult
from ytaimbot_ml.quality.evidence import EvidenceArtifact, EvidenceChain


# ---------------------------------------------------------------------------
# EvidenceArtifact
# ---------------------------------------------------------------------------

class TestEvidenceArtifactCreate:
    def test_fields_populated(self):
        a = EvidenceArtifact.create("v1", "abc123", 0.8, 0.1, "approve")
        assert a.video_id == "v1"
        assert a.script_hash == "abc123"
        assert a.similarity_score == 0.8
        assert a.bayes_score == 0.1
        assert a.operator_decision == "approve"
        assert a.previous_hash == ""

    def test_chain_hash_is_64_chars(self):
        a = EvidenceArtifact.create("v1", "abc", 0.5, 0.2, "approve")
        assert len(a.chain_hash) == 64

    def test_chain_hash_changes_with_different_input(self):
        a1 = EvidenceArtifact.create("v1", "abc", 0.5, 0.2, "approve")
        a2 = EvidenceArtifact.create("v2", "abc", 0.5, 0.2, "approve")
        assert a1.chain_hash != a2.chain_hash

    def test_timestamp_is_iso8601(self):
        a = EvidenceArtifact.create("v1", "h", 0.0, 0.0, "approve")
        assert "T" in a.timestamp  # ISO-8601 marker

    def test_immutable(self):
        a = EvidenceArtifact.create("v1", "h", 0.5, 0.5, "approve")
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            a.video_id = "mutated"  # type: ignore[misc]


class TestEvidenceArtifactGenesis:
    def test_genesis_video_id(self):
        g = EvidenceArtifact.create_genesis()
        assert g.video_id == "genesis"

    def test_genesis_previous_hash_empty(self):
        g = EvidenceArtifact.create_genesis()
        assert g.previous_hash == ""

    def test_genesis_operator_decision(self):
        g = EvidenceArtifact.create_genesis()
        assert g.operator_decision == "genesis"

    def test_genesis_has_chain_hash(self):
        g = EvidenceArtifact.create_genesis()
        assert len(g.chain_hash) == 64

    def test_genesis_verify_none(self):
        g = EvidenceArtifact.create_genesis()
        assert g.verify(None) is True


# ---------------------------------------------------------------------------
# EvidenceChain
# ---------------------------------------------------------------------------

class TestEvidenceChainAppend:
    def test_append_single(self):
        chain = EvidenceChain()
        a = EvidenceArtifact.create("v1", "h", 0.5, 0.1, "approve", chain.last_hash)
        chain.append(a)
        assert len(chain) == 1

    def test_append_multiple(self):
        chain = EvidenceChain()
        for i in range(5):
            a = EvidenceArtifact.create(f"v{i}", "h", 0.5, 0.1, "approve", chain.last_hash)
            chain.append(a)
        assert len(chain) == 5

    def test_last_hash_updates(self):
        chain = EvidenceChain()
        initial = chain.last_hash
        a = EvidenceArtifact.create("v1", "h", 0.5, 0.1, "approve", chain.last_hash)
        chain.append(a)
        assert chain.last_hash != initial
        assert chain.last_hash == a.chain_hash


class TestEvidenceChainVerify:
    def test_empty_chain_passes(self):
        chain = EvidenceChain()
        assert chain.verify_chain() is True

    def test_single_artifact_passes(self):
        chain = EvidenceChain()
        a = EvidenceArtifact.create("v1", "h", 0.5, 0.1, "approve", chain.last_hash)
        chain.append(a)
        assert chain.verify_chain() is True

    def test_three_artifacts_pass(self):
        chain = EvidenceChain()
        for i in range(3):
            a = EvidenceArtifact.create(f"v{i}", "h", 0.5, 0.1, "approve", chain.last_hash)
            chain.append(a)
        assert chain.verify_chain() is True

    def test_tamper_detected(self):
        chain = EvidenceChain()
        a = EvidenceArtifact.create("v1", "h", 0.5, 0.1, "approve", chain.last_hash)
        chain.append(a)
        # Manually inject a tampered artifact with wrong chain_hash
        tampered = EvidenceArtifact(
            video_id=a.video_id,
            script_hash=a.script_hash,
            similarity_score=a.similarity_score,
            bayes_score=a.bayes_score,
            operator_decision=a.operator_decision,
            previous_hash=a.previous_hash,
            timestamp=a.timestamp,
            chain_hash="0" * 64,  # corrupted
        )
        chain._artifacts[0] = tampered  # noqa: SLF001
        assert chain.verify_chain() is False


class TestEvidenceChainLen:
    def test_empty_len_zero(self):
        assert len(EvidenceChain()) == 0

    def test_len_after_appends(self):
        chain = EvidenceChain()
        for i in range(7):
            a = EvidenceArtifact.create(f"v{i}", "h", 0.5, 0.1, "approve", chain.last_hash)
            chain.append(a)
        assert len(chain) == 7


class TestEvidenceChainPreviousHashMismatch:
    def test_wrong_previous_hash_raises(self):
        chain = EvidenceChain()
        bad = EvidenceArtifact.create("v1", "h", 0.5, 0.1, "approve", previous_hash="wrong")
        with pytest.raises(ValueError, match="does not match"):
            chain.append(bad)


class TestEvidenceChainIteration:
    def test_iter_order(self):
        chain = EvidenceChain()
        ids = []
        for i in range(4):
            a = EvidenceArtifact.create(f"v{i}", "h", 0.5, 0.1, "approve", chain.last_hash)
            chain.append(a)
            ids.append(f"v{i}")
        assert [a.video_id for a in chain] == ids


# ---------------------------------------------------------------------------
# ComplianceResult factory methods
# ---------------------------------------------------------------------------

class TestComplianceResultOkFactory:
    def test_passed_true(self):
        r = ComplianceResult.ok()
        assert r.passed is True

    def test_no_violations(self):
        r = ComplianceResult.ok()
        assert r.violations == []

    def test_checked_at_present(self):
        r = ComplianceResult.ok()
        assert "T" in r.checked_at  # ISO-8601


class TestComplianceResultFailFactory:
    def test_passed_false(self):
        r = ComplianceResult.fail(["bad thing"])
        assert r.passed is False

    def test_violations_preserved(self):
        viols = ["problem 1", "problem 2"]
        r = ComplianceResult.fail(viols)
        assert r.violations == viols


# ---------------------------------------------------------------------------
# ComplianceChecker checks
# ---------------------------------------------------------------------------

_GOOD_DESC = "AI-generated content. All characters are adults 18+."
_GOOD_SCRIPT = "A peaceful Ghibli ASMR forest walk."


class TestComplianceCheckerOk:
    def test_fully_compliant_passes(self):
        checker = ComplianceChecker()
        result = checker.check(
            description=_GOOD_DESC,
            script=_GOOD_SCRIPT,
            duration_seconds=600,
        )
        assert result.passed is True
        assert result.violations == []

    def test_no_duration_skip(self):
        checker = ComplianceChecker()
        result = checker.check(description=_GOOD_DESC, script=_GOOD_SCRIPT)
        assert result.passed is True


class TestComplianceCheckerNoDisclosure:
    def test_missing_disclosure_fails(self):
        checker = ComplianceChecker()
        result = checker.check(
            description="A great video. All characters are adults 18+.",
            script=_GOOD_SCRIPT,
            duration_seconds=600,
        )
        assert result.passed is False
        assert any("disclosure" in v.lower() for v in result.violations)

    def test_disclosure_flag_disabled(self):
        checker = ComplianceChecker(require_ai_disclosure=False)
        result = checker.check(
            description="No disclosure here. All characters are adults 18+.",
            script=_GOOD_SCRIPT,
            duration_seconds=600,
        )
        assert result.passed is True


class TestComplianceCheckerPiiEmail:
    def test_email_in_script_fails(self):
        checker = ComplianceChecker()
        result = checker.check(
            description=_GOOD_DESC,
            script="Contact us at user@example.com for more info.",
            duration_seconds=600,
        )
        assert result.passed is False
        assert any("email" in v.lower() for v in result.violations)


class TestComplianceCheckerPiiPhone:
    def test_phone_in_description_fails(self):
        checker = ComplianceChecker()
        result = checker.check(
            description=f"{_GOOD_DESC} Call +1-800-555-1234 now.",
            script=_GOOD_SCRIPT,
            duration_seconds=600,
        )
        assert result.passed is False
        assert any("phone" in v.lower() for v in result.violations)


class TestComplianceCheckerShortDuration:
    def test_short_video_fails(self):
        checker = ComplianceChecker()
        result = checker.check(
            description=_GOOD_DESC,
            script=_GOOD_SCRIPT,
            duration_seconds=120,
        )
        assert result.passed is False
        assert any("duration" in v.lower() for v in result.violations)

    def test_exact_minimum_passes(self):
        checker = ComplianceChecker()
        result = checker.check(
            description=_GOOD_DESC,
            script=_GOOD_SCRIPT,
            duration_seconds=480,
        )
        assert result.passed is True


class TestComplianceCheckerNoAgeDisclaimer:
    def test_missing_age_disclaimer_fails(self):
        checker = ComplianceChecker()
        result = checker.check(
            description="AI-generated content. A nice video.",
            script=_GOOD_SCRIPT,
            duration_seconds=600,
        )
        assert result.passed is False
        assert any("age" in v.lower() or "disclaimer" in v.lower() or "18+" in v for v in result.violations)

    def test_age_flag_disabled(self):
        checker = ComplianceChecker(require_age_disclaimer=False)
        result = checker.check(
            description="AI-generated content. No age mention.",
            script=_GOOD_SCRIPT,
            duration_seconds=600,
        )
        assert result.passed is True

    def test_adults_keyword_sufficient(self):
        checker = ComplianceChecker()
        result = checker.check(
            description="AI-generated content. All adults characters.",
            script=_GOOD_SCRIPT,
            duration_seconds=600,
        )
        assert result.passed is True
