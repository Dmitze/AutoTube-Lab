"""Tests for the retry decorator."""

from __future__ import annotations

import random
import time
from unittest.mock import MagicMock, call, patch

import pytest

from modules.adapters.errors import RetryableError


class TestExponentialBackoff:
    """Tests for the exponential_backoff decorator."""

    @patch("time.sleep")
    def test_backoff_timing(self, mock_sleep: MagicMock) -> None:
        """
        Verify that the decorated function retries with exponential backoff timing.
        """
        from modules.adapters.retry import exponential_backoff

        @exponential_backoff(max_retries=3, base_delay=0.1, jitter=False)
        def flaky_function() -> str:
            if flaky_function.calls < 2:  # Fail twice, succeed on third call
                flaky_function.calls += 1
                raise RetryableError("Transient error")
            return "Success"

        flaky_function.calls = 0  # Initialize call counter

        result = flaky_function()

        assert result == "Success"
        assert flaky_function.calls == 2  # Two failures before success

        # Expected sleep calls for max_retries=3, base_delay=0.1, jitter=False
        # 1st retry: 2^0 * 0.1 = 0.1s
        # 2nd retry: 2^1 * 0.1 = 0.2s
        expected_calls = [call(0.1), call(0.2)]
        mock_sleep.assert_has_calls(expected_calls)
        assert mock_sleep.call_count == 2
    
    @patch("time.sleep")
    def test_max_retries_exceeded_raises(self, mock_sleep: MagicMock) -> None:
        """
        Verify that the decorated function raises RetryableError after max_retries.
        """
        from modules.adapters.retry import exponential_backoff

        @exponential_backoff(max_retries=2, base_delay=0.1, jitter=False)
        def always_flaky_function() -> str:
            raise RetryableError("Always failing")

        with pytest.raises(RetryableError, match="Always failing"):
            always_flaky_function()

        # Expected sleep calls for max_retries=2, base_delay=0.1, jitter=False
        # 1st retry: 0.1s
        # 2nd retry: 0.2s
        expected_calls = [call(0.1), call(0.2)]
        mock_sleep.assert_has_calls(expected_calls)
        assert mock_sleep.call_count == 2 # 2 retries, so 2 sleeps
    
    @patch("time.sleep")
    @patch("random.random")
    def test_jitter_adds_randomness(self, mock_random: MagicMock, mock_sleep: MagicMock) -> None:
        """
        Verify that jitter adds randomness to the delay.
        """
        from modules.adapters.retry import exponential_backoff

        # Set specific random values for predictable jitter
        mock_random.side_effect = [0.1, 0.9] # For first and second retry

        @exponential_backoff(max_retries=2, base_delay=1.0, jitter=True)
        def flaky_function_with_jitter() -> str:
            if flaky_function_with_jitter.calls < 2:
                flaky_function_with_jitter.calls += 1
                raise RetryableError("Transient error")
            return "Success"

        flaky_function_with_jitter.calls = 0

        result = flaky_function_with_jitter()

        assert result == "Success"
        assert flaky_function_with_jitter.calls == 2

        # Expected sleep calls with jitter: delay = base_delay * (2**attempt) * (1 + random_value)
        # 1st retry: 1.0 * (2**0) * (1 + 0.1) = 1.0 * 1.1 = 1.1s
        # 2nd retry: 1.0 * (2**1) * (1 + 0.9) = 2.0 * 1.9 = 3.8s
        expected_calls = [call(1.1), call(3.8)]
        mock_sleep.assert_has_calls(expected_calls)
        assert mock_sleep.call_count == 2
