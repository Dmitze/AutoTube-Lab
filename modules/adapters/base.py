"""Abstract base adapter interfaces for the YTAIMBot pipeline.

Adapters
--------
TrendSourceAdapter  : fetch() → list[TrendSignal]
StorageAdapter      : save_run / save_trends / save_compliance
PublisherAdapter    : publish(plan, report) → bool
LLMAdapter          : generate(prompt, max_tokens) → str          [Phase 2]
TTSAdapter          : speak(text, output_path) → Path             [Phase 2]
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ytaimbot_ml.schemas import ComplianceReport, ContentPlan, TrendSignal


class TrendSourceAdapter(ABC):
    """Provides raw trend signals from an external or synthetic source."""

    @abstractmethod
    def fetch(self) -> list[TrendSignal]:
        """Return a list of TrendSignal objects.

        Implementations must NOT make network calls during tests.
        """


class StorageAdapter(ABC):
    """Persists pipeline artefacts between runs."""

    @abstractmethod
    def save_run(self, run_id: str, status: str) -> None:
        """Record the outcome of a pipeline run."""

    @abstractmethod
    def save_trends(self, run_id: str, trends: list[TrendSignal]) -> None:
        """Persist ingested trend signals."""

    @abstractmethod
    def save_compliance(
        self, run_id: str, reports: list[ComplianceReport]
    ) -> None:
        """Persist compliance reports produced during the run."""


class PublisherAdapter(ABC):
    """Publishes approved content plans to the target platform."""

    @abstractmethod
    def publish(self, plan: ContentPlan, compliance_report: ComplianceReport) -> bool:
        """Publish a content plan that has passed the compliance gate.

        Returns
        -------
        bool
            ``True`` if publication succeeded, ``False`` otherwise.
        """


# ---------------------------------------------------------------------------
# Phase 2 ABCs — LLM + TTS
# ---------------------------------------------------------------------------


class LLMAdapter(ABC):
    """Abstract interface for LLM text generation.

    All implementations MUST:
    - Accept prompt string, return generated text string
    - Respect ``max_tokens`` hard limit
    - Apply ``@retry`` internally on transient errors
    - Fall back gracefully on quota / network exhaustion

    Complexity: O(tokens) — network I/O bound
    """

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text completion from a prompt.

        Parameters
        ----------
        prompt:
            Input prompt to the LLM.
        max_tokens:
            Maximum number of tokens to generate.

        Returns
        -------
        str
            Generated text (non-empty on success).

        Raises
        ------
        RetryableError
            On 429 / 5xx responses (handled by @retry decorator).
        NonRetryableError
            On 400 / 401 / 403 responses.

        Examples
        --------
        >>> adapter = GroqAdapter()
        >>> text = adapter.generate("Write a YouTube hook about Python", max_tokens=100)
        >>> isinstance(text, str) and len(text) > 0
        True
        """

    def health_check(self) -> bool:
        """Ping the LLM endpoint.

        Returns
        -------
        bool
            True if the service is reachable and responding.

        Complexity: O(1) — single HTTP request
        """
        try:
            result = self.generate("ping", max_tokens=1)
            return bool(result)
        except Exception:
            return False


class TTSAdapter(ABC):
    """Abstract interface for Text-to-Speech synthesis.

    All implementations MUST:
    - Accept text string + output Path
    - Write a valid audio file (MP3 or WAV) to output_path
    - Return the output_path on success

    Complexity: O(len(text)) — synthesis time proportional to text length
    """

    @abstractmethod
    def speak(self, text: str, output_path: Path) -> Path:
        """Synthesize speech from text and save to output_path.

        Parameters
        ----------
        text:
            Input text to synthesize (any length).
        output_path:
            Destination file path (MP3 or WAV).

        Returns
        -------
        Path
            Path to the generated audio file.

        Examples
        --------
        >>> adapter = EdgeTTSAdapter()
        >>> path = adapter.speak("Привіт!", Path("/tmp/hello.mp3"))
        >>> path.exists()
        True
        """

