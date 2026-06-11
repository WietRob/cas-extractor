"""Trace Link Model for Engineering Knowledge Plane."""

from dataclasses import dataclass, field
from typing import Any, Literal

from .provenance import ProvenanceRecord


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
    link_id: str
    source_id: str
    target_id: str
    relation_type: str
    confidence: float = 1.0
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source="manual")
    )
    baseline_membership: list[str] = field(default_factory=list)

    def __post_init__(self):
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
        return {
            "link_id": self.link_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "provenance": self.provenance.to_dict(),
            "baseline_membership": self.baseline_membership,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceLink":
        data = data.copy()
        data["provenance"] = ProvenanceRecord.from_dict(data["provenance"])
        return cls(**data)
