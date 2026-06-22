"""Tests for SecretMaskingFilter (T-498, T-499, EPIC 8.1)."""
from __future__ import annotations

import logging

import pytest

from src.ytaimbot_ml.utils.logging import SecretMaskingFilter, setup_logging


def _make_record(msg: str) -> logging.LogRecord:
    """Create a LogRecord with the given message."""
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )


# ---------------------------------------------------------------------------
# T-499: API key in log message → replaced with ***REDACTED***
# ---------------------------------------------------------------------------

def test_google_api_key_is_redacted():
    """T-499: Google API key pattern is masked."""
    f = SecretMaskingFilter()
    record = _make_record("Using key: AIzaSyABC123DEF456GHI789JKL012MNO345PQR")
    f.filter(record)
    assert "REDACTED" in record.msg
    assert "AIzaSy" not in record.msg


def test_groq_api_key_is_redacted():
    """T-499: Groq API key (gsk_...) is masked."""
    f = SecretMaskingFilter()
    fake_key = "gsk_" + "A" * 52
    record = _make_record(f"GROQ_API_KEY={fake_key}")
    f.filter(record)
    assert "REDACTED" in record.msg
    assert fake_key not in record.msg


def test_bearer_token_is_redacted():
    """T-499: Bearer token in Authorization header is masked."""
    f = SecretMaskingFilter()
    record = _make_record("Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9")
    f.filter(record)
    assert "REDACTED" in record.msg


def test_generic_password_is_redacted():
    """T-499: Generic password=value pattern is masked."""
    f = SecretMaskingFilter()
    record = _make_record("Connecting with password=supersecret123")
    f.filter(record)
    assert "REDACTED" in record.msg


def test_safe_message_not_modified():
    """T-499: Normal log messages are not modified."""
    f = SecretMaskingFilter()
    msg = "Pipeline started successfully with 10 trends"
    record = _make_record(msg)
    f.filter(record)
    assert record.msg == msg


def test_filter_always_returns_true():
    """T-498: filter() always returns True (record is kept)."""
    f = SecretMaskingFilter()
    record = _make_record("Any message")
    result = f.filter(record)
    assert result is True


def test_multiple_secrets_in_one_message():
    """T-499: Multiple secrets in one message are all redacted."""
    f = SecretMaskingFilter()
    fake_groq = "gsk_" + "B" * 52
    fake_google = "AIzaSyXYZ123ABC456DEF789GHI012JKL345MNO"
    record = _make_record(f"groq={fake_groq} google={fake_google}")
    f.filter(record)
    assert fake_groq not in record.msg
    assert fake_google not in record.msg
    assert record.msg.count("REDACTED") >= 2


def test_setup_logging_attaches_filter(caplog):
    """T-498: setup_logging() attaches SecretMaskingFilter to root logger."""
    setup_logging(level=logging.DEBUG, mask_secrets=True)
    root = logging.getLogger()
    filters = [f for f in root.filters if isinstance(f, SecretMaskingFilter)]
    assert len(filters) >= 1
