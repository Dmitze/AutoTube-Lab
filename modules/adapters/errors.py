"""Custom error classes for adapters."""

from __future__ import annotations


class AdapterError(Exception):
    """Base class for all adapter-specific errors."""


class RetryableError(AdapterError):
    """Raised when an operation can be retried (e.g., transient network issue, rate limit)."""


class NonRetryableError(AdapterError):
    """Raised when an operation should not be retried (e.g., bad request, authentication error)."""
