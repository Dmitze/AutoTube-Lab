"""Secret masking logging filter (T-494, EPIC 8.1).

Prevents API keys, tokens, and credentials from appearing in logs.

Algorithm
---------
SecretMaskingFilter:
  - Compiles regex patterns once at class level (DFA) — O(1) amortized
  - Applies each pattern to log message — O(n_patterns × len(message))
  - Replaces matches with '***REDACTED***'

Complexity: O(P × N) per log record, P = patterns, N = message length.

Examples
--------
>>> import logging
>>> from src.ytaimbot_ml.utils.logging import SecretMaskingFilter, setup_logging
>>> logger = logging.getLogger("test")
>>> logger.addFilter(SecretMaskingFilter())
>>> # API keys in log messages will be redacted automatically
"""
from __future__ import annotations

import logging
import re

# ---------------------------------------------------------------------------
# Secret patterns (DFA-compiled regex)
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[str] = [
    r"AIza[0-9A-Za-z\-_]{35}",                          # Google API key
    r"ya29\.[0-9A-Za-z\-_]+",                           # OAuth2 access token
    r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",  # OAuth2 client ID
    r"sk-[a-zA-Z0-9]{48}",                              # OpenAI key
    r"gsk_[a-zA-Z0-9]{50,}",                            # Groq API key
    r"(?i)(password|secret|token|api[_-]?key)\s*[=:]\s*[\S]{8,}",  # generic
    r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",                 # Bearer token
    r"Basic\s+[A-Za-z0-9+/]+=*",                        # Basic auth
]


class SecretMaskingFilter(logging.Filter):
    """Logging filter that redacts secrets from log messages.

    Applies compiled regex patterns to each log record's message,
    replacing matches with '***REDACTED***'.

    Complexity
    ----------
    filter(): O(P × N) where P = number of patterns, N = message length.

    Examples
    --------
    >>> import logging
    >>> f = SecretMaskingFilter()
    >>> record = logging.LogRecord(
    ...     name="test", level=logging.INFO, pathname="", lineno=0,
    ...     msg="Key: AIzaSyABC123DEF456GHI789JKL012MNO345PQR",
    ...     args=(), exc_info=None
    ... )
    >>> f.filter(record)
    True
    >>> "REDACTED" in record.msg
    True
    """

    # Compile once at class level (DFA) — O(1) amortized per instance
    _compiled: list[re.Pattern] = [
        re.compile(p) for p in _SECRET_PATTERNS
    ]
    _REDACTED = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact secrets from log record message.

        Parameters
        ----------
        record:
            Log record to filter.

        Returns
        -------
        bool
            Always True (record is kept, just sanitized).

        Complexity
        ----------
        O(P × N) where P = patterns, N = message length.
        """
        try:
            msg = record.getMessage()
        except Exception:  # noqa: BLE001
            return True

        redacted = msg
        for pattern in self._compiled:
            redacted = pattern.sub(self._REDACTED, redacted)

        if redacted != msg:
            record.msg = redacted
            record.args = ()

        return True


def setup_logging(
    level: int = logging.INFO,
    mask_secrets: bool = True,
) -> None:
    """Configure root logger with optional secret masking.

    Parameters
    ----------
    level:
        Logging level (default: INFO).
    mask_secrets:
        If True, attach SecretMaskingFilter to root logger.

    Examples
    --------
    >>> setup_logging(level=logging.DEBUG, mask_secrets=True)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    if mask_secrets:
        root = logging.getLogger()
        root.addFilter(SecretMaskingFilter())
