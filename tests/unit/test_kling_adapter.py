"""Unit tests for KlingAdapter (Phase P13, T-948)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from modules.adapters.video.kling import KlingAdapter


class _Resp:
    """Minimal urlopen-compatible response object for tests."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_Resp":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


def test_is_available_false_without_key() -> None:
    """Adapter is unavailable when key is missing."""
    assert KlingAdapter(api_key="", enabled=True).is_available() is False


def test_is_available_false_when_disabled() -> None:
    """Adapter is unavailable when disabled even with key."""
    assert KlingAdapter(api_key="k-test", enabled=False).is_available() is False


def test_is_available_true_with_key_and_enabled() -> None:
    """Adapter is available only with key and enabled=True."""
    assert KlingAdapter(api_key="k-test", enabled=True).is_available() is True


def test_service_name() -> None:
    """Service name is stable for logs/metrics."""
    assert KlingAdapter(api_key="", enabled=False).service_name == "Kling AI"


def test_generate_no_key_writes_placeholder() -> None:
    """Unavailable adapter writes placeholder without network calls."""
    adapter = KlingAdapter(api_key="", enabled=False)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "clip.mp4"
        result = adapter.generate("anime hero", out)
        assert result == out
        assert out.exists()


def test_generate_creates_parent_dirs() -> None:
    """generate() creates target directory tree."""
    adapter = KlingAdapter(api_key="", enabled=False)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "nested" / "x" / "clip.mp4"
        adapter.generate("anime hero", out)
        assert out.exists()


def test_generate_success_with_mocked_urlopen() -> None:
    """End-to-end generate() succeeds with mocked HTTP sequence."""
    adapter = KlingAdapter(api_key="k-test", enabled=True, max_poll_attempts=3, poll_interval_seconds=0.0)

    responses = [
        _Resp(json.dumps({"job_id": "job-1"}).encode()),
        _Resp(json.dumps({"status": "completed", "video_url": "https://cdn.example/video.mp4"}).encode()),
        _Resp(b"mp4-bytes"),
    ]

    def _fake_urlopen(req, timeout=30):  # noqa: ANN001,ARG001
        return responses.pop(0)

    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "clip.mp4"
        with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
            adapter.generate("anime hero", out)
        assert out.read_bytes() == b"mp4-bytes"


def test_generate_raises_on_timeout() -> None:
    """Polling timeout raises RuntimeError."""
    adapter = KlingAdapter(api_key="k-test", enabled=True, max_poll_attempts=1, poll_interval_seconds=0.0)
    responses = [
        _Resp(json.dumps({"job_id": "job-1"}).encode()),
        _Resp(json.dumps({"status": "processing"}).encode()),
    ]

    with patch("urllib.request.urlopen", side_effect=lambda req, timeout=30: responses.pop(0)):  # noqa: ARG005
        with tempfile.TemporaryDirectory() as d:
            with pytest.raises(RuntimeError, match="timed out"):
                adapter.generate("anime hero", Path(d) / "clip.mp4")
