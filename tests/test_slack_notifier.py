"""Tests for SlackNotifier, AlertDeduplicator, and SlackMessage (T-463–T-471)."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from modules.notifications import AlertDeduplicator, SlackMessage, SlackNotifier


# ---------------------------------------------------------------------------
# SlackMessage
# ---------------------------------------------------------------------------

class TestSlackMessage:
    def test_slack_message_dataclass(self) -> None:
        msg = SlackMessage(text="hello", level="info")
        assert msg.text == "hello"
        assert msg.level == "info"
        assert msg.source == "YTAIMBot"
        assert msg.channel == ""
        assert msg.sent_at  # non-empty ISO timestamp

    def test_slack_message_frozen(self) -> None:
        msg = SlackMessage(text="x", level="warning")
        with pytest.raises((AttributeError, TypeError)):
            msg.text = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AlertDeduplicator
# ---------------------------------------------------------------------------

class TestAlertDeduplicator:
    def test_dedup_first_message_sends(self) -> None:
        d = AlertDeduplicator()
        assert d.should_send("pipeline error") is True

    def test_dedup_duplicate_suppressed(self) -> None:
        d = AlertDeduplicator()
        d.should_send("pipeline error")
        assert d.should_send("pipeline error") is False

    def test_dedup_after_reset_sends_again(self) -> None:
        d = AlertDeduplicator()
        d.should_send("pipeline error")
        d.reset()
        assert d.should_send("pipeline error") is True

    def test_dedup_different_messages_both_send(self) -> None:
        d = AlertDeduplicator()
        assert d.should_send("error A") is True
        assert d.should_send("error B") is True

    def test_dedup_bloom_filter_size(self) -> None:
        d = AlertDeduplicator(size=512)
        assert d.size == 512

    def test_alert_deduplicator_reset(self) -> None:
        d = AlertDeduplicator(size=100)
        for i in range(10):
            d.should_send(f"msg-{i}")
        d.reset()
        # After reset the first message should pass again
        assert d.should_send("msg-0") is True

    def test_dedup_cooldown_triggers_reset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When elapsed time exceeds cooldown, filter auto-resets."""
        d = AlertDeduplicator(cooldown_hours=0.0001)
        d.should_send("auto-reset-msg")
        # Force monotonic clock past cooldown
        monkeypatch.setattr("time.monotonic", lambda: d._window_start + 1000)
        assert d.should_send("auto-reset-msg") is True


# ---------------------------------------------------------------------------
# SlackNotifier — no webhook (silent skip)
# ---------------------------------------------------------------------------

class TestSlackNotifierNoWebhook:
    def test_notifier_no_webhook_send_returns_false(self) -> None:
        n = SlackNotifier(webhook_url="")
        assert n.send_alert("test message") is False

    def test_notifier_no_webhook_daily_returns_false(self) -> None:
        n = SlackNotifier(webhook_url="")
        assert n.send_daily_summary({"videos_published": 1}) is False

    def test_notifier_is_configured_false_without_url(self) -> None:
        n = SlackNotifier(webhook_url="")
        assert n.is_configured is False

    def test_notifier_is_configured_true_with_url(self) -> None:
        n = SlackNotifier(webhook_url="https://hooks.slack.com/services/T/B/X")
        assert n.is_configured is True


# ---------------------------------------------------------------------------
# SlackNotifier — level emoji
# ---------------------------------------------------------------------------

class TestSlackNotifierEmoji:
    def test_notifier_level_emoji_info(self) -> None:
        assert "ℹ️" in SlackNotifier.LEVEL_EMOJI["info"]

    def test_notifier_level_emoji_critical(self) -> None:
        assert "🚨" in SlackNotifier.LEVEL_EMOJI["critical"]


# ---------------------------------------------------------------------------
# SlackNotifier — from_env
# ---------------------------------------------------------------------------

class TestSlackNotifierFromEnv:
    def test_notifier_from_env_no_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        monkeypatch.delenv("SLACK_CHANNEL_ALERTS", raising=False)
        monkeypatch.delenv("SLACK_CHANNEL_DAILY", raising=False)
        n = SlackNotifier.from_env()
        assert n.is_configured is False

    def test_notifier_from_env_with_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        url = "https://hooks.slack.com/services/TEST"
        monkeypatch.setenv("SLACK_WEBHOOK_URL", url)
        n = SlackNotifier.from_env()
        assert n.is_configured is True
        assert n._webhook_url == url


# ---------------------------------------------------------------------------
# SlackNotifier — deduplication wired through send_alert
# ---------------------------------------------------------------------------

class TestSlackNotifierDedup:
    def test_notifier_send_alert_deduplicates(self) -> None:
        """Second identical alert within window must be suppressed even with webhook."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            n = SlackNotifier(webhook_url="https://hooks.slack.com/services/X")
            assert n.send_alert("dup test") is True
            assert n.send_alert("dup test") is False  # dedup suppresses
            assert mock_open.call_count == 1  # only one HTTP call made


# ---------------------------------------------------------------------------
# SlackNotifier — mock urllib success
# ---------------------------------------------------------------------------

class TestSlackNotifierMockUrllib:
    def test_notifier_send_with_mock_urllib(self) -> None:
        """Successful HTTP 200 → send_alert returns True."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            n = SlackNotifier(webhook_url="https://hooks.slack.com/services/T/B/X")
            result = n.send_alert("test alert", level="warning")

        assert result is True
        mock_open.assert_called_once()
        call_args = mock_open.call_args[0][0]
        assert call_args.get_full_url() == "https://hooks.slack.com/services/T/B/X"
        body = json.loads(call_args.data.decode())
        assert "WARNING" in body["text"]
        assert "test alert" in body["text"]

    def test_notifier_send_daily_with_mock_urllib(self) -> None:
        """send_daily_summary posts correctly structured payload."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            n = SlackNotifier(webhook_url="https://hooks.slack.com/services/T/B/X")
            result = n.send_daily_summary({"videos_published": 3, "avg_ctr": "6.1%"})

        assert result is True

    def test_notifier_send_http_error_returns_false(self) -> None:
        """URLError during POST → send_alert returns False (no exception raised)."""
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            n = SlackNotifier(webhook_url="https://hooks.slack.com/services/T/B/X")
            result = n.send_alert("failing alert")

        assert result is False
