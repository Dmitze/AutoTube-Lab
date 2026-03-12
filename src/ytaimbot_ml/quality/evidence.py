"""Evidence artifact chain for audit trail and tamper detection.

Roadmap: T-511–T-514 (Phase 8, EPIC 8.3)
Implements a Merkle-inspired append-only chain where each artifact
hashes the previous artifact's chain_hash, making tampering detectable.

Algorithm: SHA-256 chaining → O(1) per append, O(n) for full verify
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceArtifact:
    """Immutable audit record for one video pipeline run.

    Forms a chain via chain_hash: each artifact hashes its own fields
    plus the previous artifact's chain_hash.

    Complexity: O(1) creation; O(fields) hashing

    Examples
    --------
    >>> genesis = EvidenceArtifact.create_genesis()
    >>> genesis.chain_hash != ""
    True
    >>> genesis.verify(None)
    True
    """

    video_id: str
    script_hash: str        # SHA-256 of the script text
    similarity_score: float
    bayes_score: float
    operator_decision: str  # "approve" | "reject"
    previous_hash: str      # chain_hash of previous artifact ("" for genesis)
    timestamp: str          # ISO-8601 UTC
    chain_hash: str         # SHA-256(video_id+script_hash+...+previous_hash)

    @classmethod
    def create(
        cls,
        video_id: str,
        script_hash: str,
        similarity_score: float,
        bayes_score: float,
        operator_decision: str,
        previous_hash: str = "",
    ) -> EvidenceArtifact:
        """Create a new artifact and compute its chain_hash.

        Parameters
        ----------
        video_id:
            Unique identifier of the video pipeline run.
        script_hash:
            SHA-256 hex digest of the generated script text.
        similarity_score:
            Cosine similarity score from the trend ranker, in [0, 1].
        bayes_score:
            P(bad|features) from BayesQualityFilter, in [0, 1].
        operator_decision:
            Human or system decision: "approve", "reject", or "genesis".
        previous_hash:
            chain_hash of the immediately preceding artifact ("" for first).

        Returns
        -------
        EvidenceArtifact
            Fully populated, hash-linked immutable record.

        Complexity: O(1)

        Examples
        --------
        >>> a = EvidenceArtifact.create("v1", "abc123", 0.8, 0.1, "approve")
        >>> len(a.chain_hash)
        64
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        chain_hash = cls._compute_hash(
            video_id, script_hash, similarity_score,
            bayes_score, operator_decision, previous_hash, timestamp,
        )
        return cls(
            video_id=video_id,
            script_hash=script_hash,
            similarity_score=similarity_score,
            bayes_score=bayes_score,
            operator_decision=operator_decision,
            previous_hash=previous_hash,
            timestamp=timestamp,
            chain_hash=chain_hash,
        )

    @classmethod
    def create_genesis(cls) -> EvidenceArtifact:
        """Create the first (genesis) artifact with empty previous_hash.

        Returns
        -------
        EvidenceArtifact
            A sentinel artifact that anchors the chain.

        Complexity: O(1)

        Examples
        --------
        >>> g = EvidenceArtifact.create_genesis()
        >>> g.video_id
        'genesis'
        >>> g.previous_hash
        ''
        """
        return cls.create(
            video_id="genesis",
            script_hash="",
            similarity_score=0.0,
            bayes_score=0.0,
            operator_decision="genesis",
            previous_hash="",
        )

    @staticmethod
    def _compute_hash(*args: object) -> str:
        """Compute SHA-256 of concatenated string representations.

        Parameters
        ----------
        *args:
            Arbitrary values whose ``str()`` representations are joined.

        Returns
        -------
        str
            64-character lowercase hex digest.

        Complexity: O(fields)
        """
        payload = "".join(str(a) for a in args)
        return hashlib.sha256(payload.encode()).hexdigest()

    def verify(self, previous: EvidenceArtifact | None) -> bool:
        """Verify this artifact's chain_hash is internally consistent.

        Parameters
        ----------
        previous:
            The preceding artifact in the chain, or ``None`` for genesis.

        Returns
        -------
        bool
            True if both the previous_hash linkage and chain_hash are valid.

        Complexity: O(1)

        Examples
        --------
        >>> g = EvidenceArtifact.create_genesis()
        >>> g.verify(None)
        True
        """
        prev_hash = previous.chain_hash if previous is not None else ""
        if prev_hash != self.previous_hash:
            return False
        expected = self._compute_hash(
            self.video_id,
            self.script_hash,
            self.similarity_score,
            self.bayes_score,
            self.operator_decision,
            self.previous_hash,
            self.timestamp,
        )
        return self.chain_hash == expected


class EvidenceChain:
    """Append-only chain of EvidenceArtifacts for tamper detection.

    Each append verifies the new artifact links correctly to the last.
    ``verify_chain()`` walks the full chain in O(n).

    Algorithm: append O(1), verify_chain O(n), last_hash O(1)

    Examples
    --------
    >>> chain = EvidenceChain()
    >>> a = EvidenceArtifact.create("v1", "abc", 0.5, 0.9, "approve",
    ...                             chain.last_hash)
    >>> chain.append(a)
    >>> chain.verify_chain()
    True
    >>> len(chain)
    1
    """

    def __init__(self) -> None:
        self._artifacts: list[EvidenceArtifact] = []
        self._genesis = EvidenceArtifact.create_genesis()

    @property
    def last_hash(self) -> str:
        """chain_hash of the last artifact, or genesis hash if empty.

        Returns
        -------
        str
            64-character hex digest of the most-recently-appended artifact.

        Complexity: O(1)
        """
        if self._artifacts:
            return self._artifacts[-1].chain_hash
        return self._genesis.chain_hash

    def append(self, artifact: EvidenceArtifact) -> None:
        """Append artifact after verifying it links to last_hash.

        Parameters
        ----------
        artifact:
            The artifact to append; its ``previous_hash`` must equal
            the current ``last_hash``.

        Raises
        ------
        ValueError
            If ``artifact.previous_hash`` does not match ``last_hash``.

        Complexity: O(1)

        Examples
        --------
        >>> chain = EvidenceChain()
        >>> a = EvidenceArtifact.create("v1", "h", 0.5, 0.2, "approve",
        ...                             chain.last_hash)
        >>> chain.append(a)
        >>> len(chain)
        1
        """
        if artifact.previous_hash != self.last_hash:
            raise ValueError(
                f"EvidenceChain: artifact.previous_hash {artifact.previous_hash!r} "
                f"does not match last chain hash {self.last_hash!r}"
            )
        self._artifacts.append(artifact)
        log.debug("EvidenceChain: appended artifact video_id=%s", artifact.video_id)

    def verify_chain(self) -> bool:
        """Walk full chain and verify every artifact's hash.

        Returns
        -------
        bool
            True only if all artifacts are consistent and properly linked.

        Complexity: O(n)

        Examples
        --------
        >>> chain = EvidenceChain()
        >>> chain.verify_chain()
        True
        """
        prev: EvidenceArtifact | None = self._genesis
        for artifact in self._artifacts:
            if not artifact.verify(prev):
                log.warning(
                    "EvidenceChain: tamper detected at video_id=%s",
                    artifact.video_id,
                )
                return False
            prev = artifact
        return True

    def __len__(self) -> int:
        """Number of artifacts in chain (excluding genesis).

        Complexity: O(1)
        """
        return len(self._artifacts)

    def __iter__(self):
        """Iterate artifacts in append order.

        Complexity: O(n)
        """
        return iter(self._artifacts)
