"""Phase 7 — AlertManager: threshold-based alerting via Slack/webhook.

Roadmap tasks: T-566 through T-575 (EPIC 7.3 Alerts)

Alert conditions (roadmap spec):
  CRITICAL: pipeline_status == "error" for 3 consecutive runs
  WARNING:  ctr_ema < 0.04  (below 4%)
  WARNING:  retention_ema < 0.50 (below 50%)
  WARNING:  yt_quota_used > 8000 (80% of daily quota)
  INFO:     video published successfully

Algorithm
---------
Alert dedup: sliding window (cooldown_hours) per (message, level) → O(1) set lookup
HTTP POST to SLACK_WEBHOOK_URL via urllib.request → O(1)
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Alert:
    """Immutable alert event emitted by AlertManager.

    Algorithm: O(1) construction.

    Parameters
    ----------
    level:
        Severity — one of "info", "warning", or "critical".
    message:
        Human-readable description of the alert condition.
    source:
        Component that fired the alert (e.g. "threshold_check").
    fired_at:
        UTC datetime when the alert was created.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> a = Alert(level="warning", message="CTR low", source="check", fired_at=datetime.now(timezone.utc))
    >>> a.level
    'warning'
    """

    level: Literal["info", "warning", "critical"]
    message: str
    source: str
    fired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AlertManager:
    """Threshold-based alerting via Slack webhook (HTTP POST).

    Uses a sliding-window deduplicator: the same (message, level) pair will
    not be sent again until cooldown_hours have elapsed since the last send.
    HTTP calls use stdlib urllib.request — no third-party HTTP library needed.
    The real webhook URL is read from the constructor (or env var
    SLACK_WEBHOOK_URL).

    Algorithm: alert dedup = set lookup O(1); send = O(1) HTTP POST

    Parameters
    ----------
    webhook_url:
        Slack incoming webhook URL. Pass "" or leave blank to disable sending.
    cooldown_hours:
        Minimum hours between identical alerts. Default 1.0.
    http_timeout_seconds:
        Timeout for the HTTP POST to Slack. Default 5.0.

    Examples
    --------
    >>> mgr = AlertManager(webhook_url="")
    >>> mgr.send("Pipeline failed!", level="critical")
    False
    >>> mgr.check_thresholds({"ctr_ema": 0.03, "retention_ema": 0.45})
    [Alert(level='warning', ...), Alert(level='warning', ...)]
    """

    CTR_WARNING_THRESHOLD: float = 0.04
    RETENTION_WARNING_THRESHOLD: float = 0.50
    QUOTA_WARNING_THRESHOLD: int = 8_000

    def __init__(
        self,
        webhook_url: str = "",
        cooldown_hours: float = 1.0,
        http_timeout_seconds: float = 5.0,
    ) -> None:
        self._webhook_url = webhook_url
        self._cooldown = timedelta(hours=cooldown_hours)
        self._timeout = http_timeout_seconds
        # Maps (message, level) → last-sent datetime
        self._sent_at: dict[tuple[str, str], datetime] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, message: str, level: str = "info") -> bool:
        """Send an alert to the configured Slack webhook.

        Returns True if the message was successfully POSTed, False if
        deduplicated, no webhook URL is configured, or a network error occurs.

        Algorithm: O(1) dedup lookup + O(1) HTTP POST.

        Parameters
        ----------
        message:
            Alert body text.
        level:
            Severity label added to the Slack message.

        Examples
        --------
        >>> mgr = AlertManager(webhook_url="")
        >>> mgr.send("test", level="info")
        False
        """
        if not self._webhook_url:
            log.debug("AlertManager.send(): no webhook_url configured — skipping")
            return False

        if self._is_duplicate(message, level):
            log.debug("AlertManager.send(): duplicate suppressed — %s [%s]", message, level)
            return False

        payload = json.dumps({
            "text": f"[{level.upper()}] {message}",
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                self._webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout):  # nosec B310
                pass
            self._sent_at[(message, level)] = datetime.now(timezone.utc)
            log.info("Alert sent [%s]: %s", level, message)
            return True
        except urllib.error.URLError:
            log.exception("AlertManager.send(): network error posting to webhook")
            return False
        except Exception:
            log.exception("AlertManager.send(): unexpected error")
            return False

    def check_thresholds(self, metrics: dict[str, float]) -> list[Alert]:
        """Check metric values against roadmap thresholds and return alerts.

        Does NOT automatically send the alerts — call send() separately if
        desired.

        Algorithm: O(k) where k = number of threshold checks (constant = 3).

        Parameters
        ----------
        metrics:
            Dict of metric_name → value. Recognised keys:
            "ctr_ema", "retention_ema", "yt_quota_used".

        Returns
        -------
        list[Alert]:
            One Alert per breached threshold; empty list when all are healthy.

        Examples
        --------
        >>> mgr = AlertManager()
        >>> mgr.check_thresholds({"ctr_ema": 0.02})
        [Alert(level='warning', message='CTR below threshold...', ...)]
        """
        alerts: list[Alert] = []
        now = datetime.now(timezone.utc)

        ctr = metrics.get("ctr_ema")
        if ctr is not None and ctr < self.CTR_WARNING_THRESHOLD:
            alerts.append(Alert(
                level="warning",
                message=f"CTR below threshold: {ctr:.4f} < {self.CTR_WARNING_THRESHOLD}",
                source="threshold_check",
                fired_at=now,
            ))

        retention = metrics.get("retention_ema")
        if retention is not None and retention < self.RETENTION_WARNING_THRESHOLD:
            alerts.append(Alert(
                level="warning",
                message=f"Retention below threshold: {retention:.4f} < {self.RETENTION_WARNING_THRESHOLD}",
                source="threshold_check",
                fired_at=now,
            ))

        quota = metrics.get("yt_quota_used")
        if quota is not None and quota > self.QUOTA_WARNING_THRESHOLD:
            alerts.append(Alert(
                level="warning",
                message=f"YouTube quota high: {quota:.0f} > {self.QUOTA_WARNING_THRESHOLD}",
                source="threshold_check",
                fired_at=now,
            ))

        return alerts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_duplicate(self, message: str, level: str) -> bool:
        """Return True if the same (message, level) was sent within cooldown.

        Algorithm: O(1) dict lookup + datetime comparison.

        Parameters
        ----------
        message:
            Alert message text.
        level:
            Alert severity level.

        Examples
        --------
        >>> mgr = AlertManager(cooldown_hours=1.0)
        >>> mgr._is_duplicate("test", "info")
        False
        """
        key = (message, level)
        last = self._sent_at.get(key)
        if last is None:
            return False
        return datetime.now(timezone.utc) - last < self._cooldown
