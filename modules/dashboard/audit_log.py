"""Audit log for manual review decisions (Phase 4 publishing safety)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class AuditEntry:
    """One immutable manual-review decision entry.

    Complexity
    ----------
    O(1) data container.

    Examples
    --------
    >>> e = AuditEntry(run_id="r1", trend_id="t1", decision="approve", reason="ok")
    >>> e.decision
    'approve'
    """

    run_id: str
    trend_id: str
    decision: str  # "approve" | "reject"
    reason: str
    operator: str = "human"
    reviewed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditLog:
    """Append-only JSONL audit log for publication decisions.

    Complexity
    ----------
    append(): O(1)
    read_all(): O(n) where n is number of entries.

    Examples
    --------
    >>> import tempfile
    >>> from pathlib import Path
    >>> with tempfile.TemporaryDirectory() as d:
    ...     log = AuditLog(Path(d) / "audit.jsonl")
    ...     log.append(AuditEntry("r1", "t1", "approve", "ok"))
    ...     len(log.read_all())
    1
    """

    def __init__(self, path: Path | str = "data/audit/review_log.jsonl") -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Path to JSONL file. O(1)."""
        return self._path

    def append(self, entry: AuditEntry) -> None:
        """Append one entry as JSON line. O(1)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), ensure_ascii=True) + "\n")

    def read_all(self) -> list[AuditEntry]:
        """Read all entries from JSONL file. O(n)."""
        if not self._path.exists():
            return []
        entries: list[AuditEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                entries.append(AuditEntry(**payload))
        return entries

    def count_decisions(self) -> int:
        """Return number of logged decisions. O(n)."""
        return len(self.read_all())

