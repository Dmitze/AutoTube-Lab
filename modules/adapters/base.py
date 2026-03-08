"""Abstract base adapter interfaces for the YTAIMBot pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod

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
