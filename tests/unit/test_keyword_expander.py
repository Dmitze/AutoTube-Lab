"""Unit tests for KeywordExpander (BFS-based SEO keyword expansion).

Roadmap tasks: T-207 through T-212 (EPIC 3.4)
"""

import pytest
from unittest.mock import MagicMock, patch
from ytaimbot_ml.seo.keyword_expander import KeywordExpander
from modules.adapters.retry import RetryableError

@pytest.fixture
def expander():
    return KeywordExpander()

def test_expand_basic(expander):
    """Test expansion with mocked suggestions."""
    with patch.object(expander, '_fetch_suggestions') as mock_fetch:
        # Mock depth 1 expansion
        mock_fetch.side_effect = lambda kw: [f"{kw} tips", f"how to {kw}"] if kw == "python" else []
        
        result = expander.expand(["python"], depth=1)
        
        assert "python" in result
        assert "python tips" in result
        assert "how to python" in result
        assert len(result) >= 3

def test_expand_deduplication(expander):
    """Test that duplicate keywords are removed (T-209)."""
    with patch.object(expander, '_fetch_suggestions') as mock_fetch:
        mock_fetch.return_value = ["python", "PYTHON ", "Python tips"]
        
        result = expander.expand(["python"], depth=1)
        
        # Should be unique normalized keywords
        assert len(result) == 2
        assert "python" in result
        assert "Python tips" in result

def test_expand_depth_limit(expander):
    """Test BFS depth limit (T-210)."""
    with patch.object(expander, '_fetch_suggestions') as mock_fetch:
        # Depth 0: python
        # Depth 1: python -> tips
        # Depth 2: tips -> advanced
        def mock_suggest(kw):
            if kw == "python": return ["tips"]
            if kw == "tips": return ["advanced"]
            return []
        
        mock_fetch.side_effect = mock_suggest
        
        # Depth 1 expansion
        res1 = expander.expand(["python"], depth=1)
        assert "advanced" not in res1
        
        # Depth 2 expansion
        res2 = expander.expand(["python"], depth=2)
        assert "advanced" in res2

def test_expand_error_handling(expander):
    """Test that HTTP errors don't crash the expansion (T-211)."""
    with patch.object(expander, '_fetch_suggestions') as mock_fetch:
        mock_fetch.side_effect = Exception("Network error")
        
        result = expander.expand(["python"], depth=1)
        
        # Should still return seeds
        assert result == ["python"]

def test_fetch_suggestions_retry():
    """Test that _fetch_suggestions retries on RetryableError (T-205)."""
    mock_client = MagicMock()
    expander = KeywordExpander(client=mock_client)
    
    # Mock 429 once, then success
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = ["python", ["python tips"]]
    
    mock_client.get.side_effect = [mock_response_429, mock_response_200]
    
    suggestions = expander._fetch_suggestions("python")
    
    assert suggestions == ["python tips"]
    assert mock_client.get.call_count == 2
