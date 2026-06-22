"""Phase 5 — WeeklyReportGenerator (EPIC 5.5, T-360–T-371).

Generates a Markdown weekly performance report from SQLite metrics.

Algorithm
---------
ascii_bar(): O(width) = O(1) — constant width
_top_videos(): O(n log n) — sort by RPM
_bottom_videos(): O(n log n) — sort by retention
generate(): O(n log n) dominated by sorting

Examples
--------
>>> from modules.reporting.weekly_report import WeeklyReportGenerator, ascii_bar
>>> ascii_bar(7.5, 10.0, width=20)
'|███████████████▛▛▛▛▛| 7.50'
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPORTS_DIR = Path("docs/WEEKLY_REPORTS")


# ---------------------------------------------------------------------------
# T-365: ASCII bar chart helper
# ---------------------------------------------------------------------------

def ascii_bar(value: float, max_val: float, width: int = 30) -> str:
    """Render a horizontal ASCII bar proportional to value/max_val.

    Parameters
    ----------
    value:
        Current metric value.
    max_val:
        Maximum value (used to scale the bar).
    width:
        Total bar width in characters (default 30).

    Returns
    -------
    str
        Formatted bar string, e.g. ``|█████▛▛▛▛▛| 7.50``

    Complexity
    ----------
    O(width) = O(1) — constant width.

    Examples
    --------
    >>> ascii_bar(5.0, 10.0, width=10)
    '|█████▛▛▛▛▛| 5.00'
    >>> ascii_bar(0.0, 10.0, width=10)
    '|▛▛▛▛▛▛▛▛▛▛| 0.00'
    >>> ascii_bar(10.0, 0.0, width=10)  # max_val=0 edge case
    '|▛▛▛▛▛▛▛▛▛▛| 10.00'
    """
    filled = int((value / max_val) * width) if max_val > 0 else 0
    filled = max(0, min(filled, width))
    bar = "█" * filled + "▛" * (width - filled)
    return f"|{bar}| {value:.2f}"


# ---------------------------------------------------------------------------
# T-361: WeeklyReportGenerator
# ---------------------------------------------------------------------------

class WeeklyReportGenerator:
    """Generates a Markdown weekly performance report from pipeline metrics.

    Parameters
    ----------
    storage:
        StorageAdapter with access to video and metrics data.
    reports_dir:
        Directory where weekly reports are saved.
        Default: ``docs/WEEKLY_REPORTS/``.

    Complexity
    ----------
    generate(): O(n log n) — dominated by sorting videos by metric.

    Examples
    --------
    >>> from modules.adapters.synthetic import InMemoryStorage
    >>> gen = WeeklyReportGenerator(storage=InMemoryStorage())
    >>> report = gen.generate(week=1, year=2026)
    >>> isinstance(report, str) and len(report) > 0
    True
    """

    def __init__(
        self,
        storage: Any,
        reports_dir: Path = _REPORTS_DIR,
    ) -> None:
        self._storage = storage
        self._reports_dir = Path(reports_dir)

    # ------------------------------------------------------------------
    # T-362: generate()
    # ------------------------------------------------------------------

    def generate(self, week: int | None = None, year: int | None = None) -> str:
        """Generate a Markdown weekly report.

        Parameters
        ----------
        week:
            ISO week number (1–53). Defaults to current week.
        year:
            Year. Defaults to current year.

        Returns
        -------
        str
            Full Markdown report string.

        Complexity
        ----------
        O(n log n) — sorting videos.
        """
        today = date.today()
        week = week or today.isocalendar()[1]
        year = year or today.year

        videos = self._storage.list_published_videos(limit=200)

        top = self._top_videos(videos, n=5)
        bottom = self._bottom_videos(videos, n=5)
        recommendations = self._recommendations(videos)

        report = self._render(
            week=week,
            year=year,
            videos=videos,
            top=top,
            bottom=bottom,
            recommendations=recommendations,
        )
        return report

    # ------------------------------------------------------------------
    # T-367: save()
    # ------------------------------------------------------------------

    def save(self, report: str, week: int, year: int) -> Path:
        """Save report to docs/WEEKLY_REPORTS/YYYY-WNN.md.

        Parameters
        ----------
        report:
            Markdown report string.
        week:
            ISO week number.
        year:
            Year.

        Returns
        -------
        Path
            Path to the saved file.

        Complexity
        ----------
        O(len(report)) — file write.
        """
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{year}-W{week:02d}.md"
        path = self._reports_dir / filename
        path.write_text(report, encoding="utf-8")
        logger.info("Weekly report saved: %s", path)
        return path

    def generate_and_save(self, week: int | None = None, year: int | None = None) -> Path:
        """Generate and save the weekly report in one call.

        Complexity: O(n log n)
        """
        today = date.today()
        week = week or today.isocalendar()[1]
        year = year or today.year
        report = self.generate(week=week, year=year)
        return self.save(report, week=week, year=year)

    # ------------------------------------------------------------------
    # T-363: _top_videos()
    # ------------------------------------------------------------------

    def _top_videos(self, videos: list[dict], n: int = 5) -> list[dict]:
        """Return top-N videos sorted by RPM descending.

        Complexity: O(n log n)
        """
        scored = [
            v for v in videos
            if v.get("rpm", 0.0) is not None
        ]
        return sorted(scored, key=lambda v: v.get("rpm", 0.0), reverse=True)[:n]

    # ------------------------------------------------------------------
    # T-364: _bottom_videos()
    # ------------------------------------------------------------------

    def _bottom_videos(self, videos: list[dict], n: int = 5) -> list[dict]:
        """Return bottom-N videos sorted by retention ascending.

        Complexity: O(n log n)
        """
        scored = [
            v for v in videos
            if v.get("retention_30s") is not None
        ]
        return sorted(scored, key=lambda v: v.get("retention_30s", 1.0))[:n]

    # ------------------------------------------------------------------
    # T-366: _recommendations()
    # ------------------------------------------------------------------

    def _recommendations(self, videos: list[dict]) -> list[str]:
        """Generate data-driven recommendations based on metrics.

        Complexity: O(n)
        """
        recs: list[str] = []

        if not videos:
            recs.append("📤 No videos published yet — start the pipeline!")
            return recs

        ctrs = [v.get("ctr", 0.0) or 0.0 for v in videos]
        avg_ctr = sum(ctrs) / len(ctrs) if ctrs else 0.0

        retentions = [v.get("retention_30s", 0.0) or 0.0 for v in videos]
        avg_ret = sum(retentions) / len(retentions) if retentions else 0.0

        rpms = [v.get("rpm", 0.0) or 0.0 for v in videos]
        avg_rpm = sum(rpms) / len(rpms) if rpms else 0.0

        if avg_ctr < 0.04:
            recs.append(
                f"📌 CTR is low ({avg_ctr*100:.1f}%) — "
                "try stronger thumbnails and power-word titles."
            )
        elif avg_ctr >= 0.06:
            recs.append(
                f"✅ CTR is strong ({avg_ctr*100:.1f}%) — "
                "keep current thumbnail style."
            )

        if avg_ret < 0.50:
            recs.append(
                f"📌 Retention is low ({avg_ret*100:.1f}%) — "
                "improve hook (first 30s) and pacing."
            )
        elif avg_ret >= 0.70:
            recs.append(
                f"✅ Retention is strong ({avg_ret*100:.1f}%) — "
                "current script structure works well."
            )

        if avg_rpm < 2.0:
            recs.append(
                f"📌 RPM is low (${avg_rpm:.2f}) — "
                "consider Finance or Tech niches for higher RPM."
            )
        elif avg_rpm >= 5.0:
            recs.append(
                f"✅ RPM is excellent (${avg_rpm:.2f}) — "
                "double down on current niche."
            )

        if len(videos) < 30:
            recs.append(
                f"📌 Only {len(videos)} videos published — "
                "publish at least 30 before drawing conclusions."
            )

        if not recs:
            recs.append("✅ All metrics look healthy — keep the current strategy.")

        return recs

    # ------------------------------------------------------------------
    # _render()
    # ------------------------------------------------------------------

    def _render(
        self,
        week: int,
        year: int,
        videos: list[dict],
        top: list[dict],
        bottom: list[dict],
        recommendations: list[str],
    ) -> str:
        """Render the full Markdown report string.

        Complexity: O(n) — linear in number of videos.
        """
        lines: list[str] = []

        # Header
        lines += [
            f"# 📊 YTAIMBot Weekly Report — {year} W{week:02d}",
            f"",
            f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"> Total videos: **{len(videos)}**",
            f"",
            "---",
            "",
        ]

        # Summary stats
        if videos:
            ctrs = [v.get("ctr", 0.0) or 0.0 for v in videos]
            rets = [v.get("retention_30s", 0.0) or 0.0 for v in videos]
            rpms = [v.get("rpm", 0.0) or 0.0 for v in videos]
            views_list = [v.get("views", 0) or 0 for v in videos]

            avg_ctr = sum(ctrs) / len(ctrs)
            avg_ret = sum(rets) / len(rets)
            avg_rpm = sum(rpms) / len(rpms)
            total_views = sum(views_list)
            max_ctr = max(ctrs) if ctrs else 1.0
            max_ret = max(rets) if rets else 1.0
            max_rpm = max(rpms) if rpms else 1.0

            lines += [
                "## 📊 Summary",
                "",
                f"| Metric | Value | Bar |",
                f"|--------|-------|-----|",
                f"| Avg CTR | {avg_ctr*100:.2f}% | {ascii_bar(avg_ctr*100, max_ctr*100)} |",
                f"| Avg Retention 30s | {avg_ret*100:.2f}% | {ascii_bar(avg_ret*100, max_ret*100)} |",
                f"| Avg RPM | ${avg_rpm:.2f} | {ascii_bar(avg_rpm, max_rpm)} |",
                f"| Total Views | {total_views:,} | — |",
                "",
            ]
        else:
            lines += ["## 📊 Summary", "", "_No videos published yet._", ""]

        # Top 5 videos
        lines += ["## 🏆 Top 5 Videos (by RPM)", ""]
        if top:
            lines += ["| # | Title | RPM | CTR | Retention |",
                      "|---|-------|-----|-----|-----------|",]
            for i, v in enumerate(top, 1):
                title = (v.get("title") or v.get("video_id", "?"))[:40]
                rpm = v.get("rpm", 0.0) or 0.0
                ctr = v.get("ctr", 0.0) or 0.0
                ret = v.get("retention_30s", 0.0) or 0.0
                lines.append(
                    f"| {i} | {title} | ${rpm:.2f} | {ctr*100:.1f}% | {ret*100:.1f}% |"
                )
            lines.append("")
        else:
            lines += ["_No data yet._", ""]

        # Bottom 5 videos
        lines += ["## ⚠️ Bottom 5 Videos (by Retention)", ""]
        if bottom:
            lines += ["| # | Title | Retention | CTR | RPM |",
                      "|---|-------|-----------|-----|-----|",]
            for i, v in enumerate(bottom, 1):
                title = (v.get("title") or v.get("video_id", "?"))[:40]
                ret = v.get("retention_30s", 0.0) or 0.0
                ctr = v.get("ctr", 0.0) or 0.0
                rpm = v.get("rpm", 0.0) or 0.0
                lines.append(
                    f"| {i} | {title} | {ret*100:.1f}% | {ctr*100:.1f}% | ${rpm:.2f} |"
                )
            lines.append("")
        else:
            lines += ["_No data yet._", ""]

        # Recommendations
        lines += ["## 💡 Recommendations", ""]
        for rec in recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        lines += [
            "---",
            "",
            "_Auto-generated by YTAIMBot — do not edit manually._",
        ]

        return "\n".join(lines)
