"""ytaimbot_ml.quality — content quality filtering sub-package."""
from ytaimbot_ml.quality.bayes_filter import BayesQualityFilter, TopicBlacklist
from ytaimbot_ml.quality.blocklist import BlocklistTrie
from ytaimbot_ml.quality.compliance import ComplianceChecker, ComplianceResult
from ytaimbot_ml.quality.evidence import EvidenceArtifact, EvidenceChain
from ytaimbot_ml.quality.sanitizer import ContentSanitizer
from ytaimbot_ml.learner.drift_detector import KSDriftDetector # Added import
from ytaimbot_ml.quality.similarity_gate import SimilarityGate # Added import

__all__ = [
    "BayesQualityFilter",
    "BlocklistTrie",
    "ComplianceChecker",
    "ComplianceResult",
    "ContentSanitizer",
    "EvidenceArtifact",
    "EvidenceChain",
    "TopicBlacklist",
    "KSDriftDetector",
    "SimilarityGate", # Added to __all__
]
