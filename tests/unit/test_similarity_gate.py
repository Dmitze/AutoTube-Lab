"""Unit tests for SimilarityGate (plagiarism detection).

Roadmap tasks: T-276 through T-280 (EPIC 4.3)
"""

import pytest
from ytaimbot_ml.quality.similarity_gate import SimilarityGate

@pytest.fixture
def gate():
    return SimilarityGate(threshold=0.85)

def test_check_identical(gate):
    """Test that identical text is blocked (T-277)."""
    text = "This is a unique script about python automation in 2026."
    archive = {"v1": text}
    
    report = gate.check(text, archive)
    
    assert report.score == pytest.approx(1.0)
    assert report.decision == "block"
    assert "v1" in report.matches

def test_check_different(gate):
    """Test that completely different text passes (T-278)."""
    text = "Python automation guide."
    archive = {"v2": "How to cook a pizza in 10 minutes."}
    
    report = gate.check(text, archive)
    
    assert report.score < 0.2
    assert report.decision == "pass"

def test_check_empty_archive(gate):
    """Test that empty archive always passes (T-279)."""
    report = gate.check("Some text", {})
    
    assert report.score == 0.0
    assert report.decision == "pass"

def test_get_hash(gate):
    """Test SHA-256 content hashing (T-280)."""
    text1 = "Hello World!"
    text2 = "hello world"  # normalization should make them identical
    
    h1 = gate.get_hash(text1)
    h2 = gate.get_hash(text2)
    
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 length
