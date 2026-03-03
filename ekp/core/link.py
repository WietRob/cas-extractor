"""
Trace Link Model for Engineering Knowledge Plane.

Links connect artifacts with typed relations:
- verifies: REQ → TEST
- allocates_to: REQ → ARCH
- implements: ARCH → SWU
- tests: TEST → SWU
- derived_from: REQ → REQ
- satisfies: REQ → REQ (stakeholder)
- impacts: Change → *
- conflicts_with: * → *
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


# Relation types (ASPICE-aligned)
RelationType = Literal[
    "verifies",
    "allocates_to",
    "implements",
    "tests",
    "derived_from",
    "satisfies",
    "impacts",
    "conflicts_with",
]

RELATION_TYPES: frozenset[RelationType] = frozenset(
    {
        "verifies",
        "allocates_to",
        "implements",
        "tests",
        "derived_from",
        "satisfies",
        "impacts",
        "conflicts_with",
    }
)

# ASPICE references for relations
RELATION_ASPICE_REFS = {
    "verifies": "SYS.5 / SWE.5",
    "allocates_to": "SYS.3 / SWE.3",
    "implements": "SWE.3",
    "tests": "SWE.5",
    "derived_from": "SYS.2",
    "satisfies": "SYS.2",
    "impacts": "MAN.5",
    "conflicts_with": "(Governance)",
}


@dataclass
class TraceLink:
    """Trace link between two artifacts."""

    link_id: str  # e.g., trace-001
    source_id: str  # Source artifact ID
    target_id: str  # Target artifact ID
    relation_type: RelationType

    # Confidence
    confidence: float = 1.0  # 0.0 - 1.0

    # Provenance
    provenance_source: str = ""  # manual, trace_reconstruction, semantic_similarity
    provenance_algorithm: str = ""
    provenance_timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence_path: list[str] = field(default_factory=list)  # Derivation chain

    # Baseline membership
    baseline_membership: list[str] = field(default_factory=list)

    # Metadata
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate relation type and confidence."""
        if self.relation_type not in RELATION_TYPES:
            raise ValueError(
                f"Invalid relation_type: {self.relation_type}. "
                f"Must be one of: {RELATION_TYPES}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "link_id": self.link_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "provenance_source": self.provenance_source,
            "provenance_algorithm": self.provenance_algorithm,
            "provenance_timestamp": self.provenance_timestamp.isoformat(),
            "evidence_path": self.evidence_path,
            "baseline_membership": self.baseline_membership,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceLink":
        """Deserialize from dictionary."""
        data = data.copy()
        data["provenance_timestamp"] = datetime.fromisoformat(
            data["provenance_timestamp"]
        )
        return cls(**data)
