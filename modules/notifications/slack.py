"""Slack webhook notifications with Bloom Filter dedup.

Roadmap: T-463–T-471 (Phase 7, EPIC 7.3)
Depends on: stdlib only (hashlib, urllib.request)

AlertDeduplicator: time-windowed probabilistic dedup using a simplified
Bloom Filter with SHA-256 hashing (2 hash functions).
False positive rate: ~1% for 1000 messages with m=10000 bits.
After cooldown_hours: filter resets (new window starts).
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SlackMessage:
    """Immutable Slack message container.

    Complexity: O(1) construction.

    Examples
    --------
    >>> msg = SlackMessage(text="hello", level="info")
    >>> msg.source
    'YTAIMBot'
    >>> msg.level
    'info'
    """

    text: str
    level: Literal["info", "warning", "critical"]
    channel: str = ""
    source: str = "YTAIMBot"
    sent_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AlertDeduplicator:
    """Time-windowed Bloom Filter for Slack alert deduplication.

    Uses 2 independent SHA-256-derived hash functions to set/check bits.
    Resets after cooldown_hours to start a fresh window.

    False positive rate ≈ (1 - e^(-kn/m))^k where k=2, m=10000, n=messages.
    For 100 messages: ~0.2% false positive rate.

    Complexity: O(k) per check/add where k = number of hash functions = 2.
    Space: O(m/8) bytes = ~1.25 KB for m=10000.

    Examples
    --------
    >>> dedup = AlertDeduplicator(cooldown_hours=1.0)
    >>> dedup.should_send("pipeline error")
    True
    >>> dedup.should_send("pipeline error")
    False
    >>> dedup.size
    10000
    """

    def __init__(
        self,
        size: int = 10_000,
        cooldown_hours: float = 1.0,
    ) -> None:
        """Initialise the Bloom Filter.

        Parameters
        ----------
        size:
            Bit-array width *m*. Larger values reduce false-positive rate.
        cooldown_hours:
            Hours before the filter window resets automatically.

        Complexity: O(m/8) for bytearray allocation.

        Examples
        --------
        >>> d = AlertDeduplicator(size=100, cooldown_hours=0.5)
        >>> d.size
        100
        """
        self._size = size
        self._cooldown_seconds = cooldown_hours * 3600
        self._bits = bytearray((size + 7) // 8)
        self._window_start = time.monotonic()

    def should_send(self, message: str) -> bool:
        """Return True if *message* should be sent (not seen in current window).

        Marks the message as seen regardless of the return value.

        Complexity: O(k) where k = 2 hash functions.

        Examples
        --------
        >>> d = AlertDeduplicator()
        >>> d.should_send("new alert")
        True
        >>> d.should_send("new alert")
        False
        """
        self._maybe_reset()
        h1, h2 = self._hashes(message)
        if self._get_bit(h1) and self._get_bit(h2):
            log.debug("AlertDeduplicator: suppressing duplicate message")
            return False
        self._set_bit(h1)
        self._set_bit(h2)
        return True

    def reset(self) -> None:
        """Force-reset the Bloom filter and start a fresh window.

        Complexity: O(m/8).

        Examples
        --------
        >>> d = AlertDeduplicator()
        >>> _ = d.should_send("msg")
        >>> d.reset()
        >>> d.should_send("msg")
        True
        """
        self._bits = bytearray((self._size + 7) // 8)
        self._window_start = time.monotonic()

    @property
    def size(self) -> int:
        """Bit-array width *m*.

        Complexity: O(1).

        Examples
        --------
        >>> AlertDeduplicator(size=512).size
        512
        """
        return self._size

    def _maybe_reset(self) -> None:
        if time.monotonic() - self._window_start >= self._cooldown_seconds:
            log.debug("AlertDeduplicator: cooldown expired — resetting window")
            self.reset()

    def _hashes(self, text: str) -> tuple[int, int]:
        """Return two independent bit positions derived from SHA-256. O(1)."""
        digest = hashlib.sha256(text.encode()).hexdigest()
        h1 = int(digest[:16], 16) % self._size
        h2 = int(digest[16:32], 16) % self._size
        return h1, h2

    def _get_bit(self, pos: int) -> bool:
        return bool(self._bits[pos // 8] & (1 << (pos % 8)))

    def _set_bit(self, pos: int) -> None:
        self._bits[pos // 8] |= 1 << (pos % 8)


class SlackNotifier:
    """Sends alerts and daily summaries to Slack via webhook.

    Uses AlertDeduplicator (Bloom Filter) to suppress duplicate messages
    within the cooldown window. Gracefully no-ops when no webhook URL is set.

    HTTP transport: stdlib ``urllib.request`` — no third-party dependency.

    Algorithm complexity:
    - send_alert: O(1)
    - send_daily_summary: O(n) where n = len(stats)

    Examples
    --------
    >>> notifier = SlackNotifier(webhook_url="")
    >>> notifier.send_alert("Pipeline error!", level="critical")
    False
    >>> notifier.send_daily_summary({"videos": 3, "revenue_est": 0.5})
    False
    """

    LEVEL_EMOJI: dict[str, str] = {
        "info": "ℹ️",
        "warning": "⚠️",
        "critical": "🚨",
    }

    def __init__(
        self,
        webhook_url: str = "",
        channel_alerts: str = "#ytaimbot-alerts",
        channel_daily: str = "#ytaimbot-daily",
        cooldown_hours: float = 1.0,
        http_timeout: float = 5.0,
    ) -> None:
        """Create a SlackNotifier.

        Parameters
        ----------
        webhook_url:
            Slack incoming-webhook URL. Empty string disables all sends.
            Prefer reading from ``SLACK_WEBHOOK_URL`` via :meth:`from_env`.
        channel_alerts:
            Override destination channel for :meth:`send_alert`.
        channel_daily:
            Override destination channel for :meth:`send_daily_summary`.
        cooldown_hours:
            Dedup window passed to :class:`AlertDeduplicator`.
        http_timeout:
            Seconds before the HTTP POST times out.

        Complexity: O(m/8) for Bloom Filter allocation.

        Examples
        --------
        >>> import os; os.environ.get("SLACK_WEBHOOK_URL", "")
        ''
        >>> n = SlackNotifier()
        >>> n.is_configured
        False
        """
        self._webhook_url = webhook_url
        self._channel_alerts = channel_alerts
        self._channel_daily = channel_daily
        self._http_timeout = http_timeout
        self._dedup = AlertDeduplicator(cooldown_hours=cooldown_hours)

    @property
    def is_configured(self) -> bool:
        """True if a webhook URL has been provided.

        Complexity: O(1).

        Examples
        --------
        >>> SlackNotifier(webhook_url="").is_configured
        False
        >>> SlackNotifier(webhook_url="https://hooks.slack.com/x").is_configured
        True
        """
        return bool(self._webhook_url)

    def send_alert(
        self,
        message: str,
        level: Literal["info", "warning", "critical"] = "info",
        source: str = "YTAIMBot",
    ) -> bool:
        """Send an alert message to the alerts channel.

        Deduplicates via :class:`AlertDeduplicator`: the same *message* text
        will not be sent more than once within the cooldown window.
        Returns ``True`` if the HTTP POST was attempted and succeeded.

        Complexity: O(1).

        Examples
        --------
        >>> n = SlackNotifier(webhook_url="")
        >>> n.send_alert("test")
        False
        """
        if not self.is_configured:
            log.debug("SlackNotifier.send_alert: no webhook configured — skipping")
            return False

        if not self._dedup.should_send(message):
            log.debug("SlackNotifier.send_alert: duplicate suppressed — %s", message)
            return False

        emoji = self.LEVEL_EMOJI.get(level, "ℹ️")
        payload = {
            "channel": self._channel_alerts,
            "text": f"{emoji} *[{level.upper()}]* {source}: {message}",
        }
        log.info("SlackNotifier: sending alert level=%s", level)
        return self._send(payload, self._channel_alerts)

    def send_daily_summary(self, stats: dict) -> bool:
        """Send daily pipeline statistics to the daily channel.

        Recognised *stats* keys (all optional):
        ``videos_published``, ``avg_ctr``, ``avg_retention``,
        ``quota_used``, ``revenue_estimate``, ``top_niche``, ``errors_count``.

        Complexity: O(n) where n = ``len(stats)``.

        Examples
        --------
        >>> n = SlackNotifier(webhook_url="")
        >>> n.send_daily_summary({"videos_published": 1})
        False
        """
        if not self.is_configured:
            log.debug("SlackNotifier.send_daily_summary: no webhook configured — skipping")
            return False

        lines = ["📊 *YTAIMBot Daily Summary*", ""]
        field_labels = {
            "videos_published": "Videos published",
            "avg_ctr": "Avg CTR",
            "avg_retention": "Avg 30s retention",
            "quota_used": "Quota used",
            "revenue_estimate": "Revenue estimate (USD)",
            "top_niche": "Top niche",
            "errors_count": "Errors",
        }
        for key, label in field_labels.items():
            if key in stats:
                lines.append(f"• *{label}*: {stats[key]}")
        for key, value in stats.items():
            if key not in field_labels:
                lines.append(f"• *{key}*: {value}")

        payload = {
            "channel": self._channel_daily,
            "text": "\n".join(lines),
        }
        log.info("SlackNotifier: sending daily summary with %d stat(s)", len(stats))
        return self._send(payload, self._channel_daily)

    def _send(self, payload: dict, channel: str) -> bool:
        """POST *payload* as JSON to the Slack webhook. Returns True on success.

        Complexity: O(1).

        Examples
        --------
        >>> n = SlackNotifier(webhook_url="")
        >>> n._send({}, "#test")
        False
        """
        if not self.is_configured:
            return False
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._http_timeout) as resp:
                status = resp.status
                log.debug("SlackNotifier: POST %s → HTTP %d", channel, status)
                return 200 <= status < 300
        except urllib.error.URLError as exc:
            log.exception("SlackNotifier: HTTP error posting to %s: %s", channel, exc)
            return False

    @classmethod
    def from_env(cls) -> SlackNotifier:
        """Build a :class:`SlackNotifier` from environment variables.

        Environment variables read:
        - ``SLACK_WEBHOOK_URL`` — webhook URL (default: empty string)
        - ``SLACK_CHANNEL_ALERTS`` — alerts channel (default: ``#ytaimbot-alerts``)
        - ``SLACK_CHANNEL_DAILY`` — daily channel (default: ``#ytaimbot-daily``)

        Complexity: O(1).

        Examples
        --------
        >>> import os
        >>> os.environ.pop("SLACK_WEBHOOK_URL", None)
        >>> n = SlackNotifier.from_env()
        >>> n.is_configured
        False
        """
        import os  # noqa: PLC0415

        return cls(
            webhook_url=os.environ.get("SLACK_WEBHOOK_URL", ""),
            channel_alerts=os.environ.get("SLACK_CHANNEL_ALERTS", "#ytaimbot-alerts"),
            channel_daily=os.environ.get("SLACK_CHANNEL_DAILY", "#ytaimbot-daily"),
        )
