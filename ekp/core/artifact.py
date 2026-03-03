"""
Canonical Artifact Model for Engineering Knowledge Plane.

Each artifact is a versioned, traceable entity with:
- Unique ID with type prefix
- Type classification
- Compliance tags
- Source references
- Evidence links
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CanonicalArtifact:
    """Canonical representation of an engineering artifact."""

    artifact_id: str  # e.g., REQ-001, SWU-042
    artifact_type: str  # requirement, architecture, sw_unit, test, evidence, baseline
    title: str
    status: str = "draft"  # draft, reviewed, approved, baseline
    version: str = "1.0.0"
    owner: str = ""

    # Content
    description: str = ""
    content: dict = field(default_factory=dict)  # Type-specific content

    # Traceability
    source_refs: list[str] = field(
        default_factory=list
    )  # Git refs, file paths, external IDs
    links: list[str] = field(default_factory=list)  # Link IDs
    evidence: list[str] = field(default_factory=list)  # Evidence IDs

    # Compliance
    compliance_tags: list[str] = field(
        default_factory=list
    )  # ASPICE.SYS.3, ISO26262.Part3

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    extra: dict = field(default_factory=dict)

    # Provenance
    provenance_source: str = ""  # manual, extracted, reconstructed
    provenance_confidence: float = 1.0

    def __post_init__(self):
        """Validate artifact_id prefix matches type."""
        prefix_map = {
            "requirement": "REQ",
            "architecture": "ARCH",
            "sw_unit": "SWU",
            "test": "TEST",
            "evidence": "EV",
            "baseline": "BL",
        }
        expected_prefix = prefix_map.get(self.artifact_type)
        if expected_prefix and not self.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id must start with {expected_prefix} for type {self.artifact_type}, "
                f"got {self.artifact_id}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "status": self.status,
            "version": self.version,
            "owner": self.owner,
            "description": self.description,
            "content": self.content,
            "source_refs": self.source_refs,
            "links": self.links,
            "evidence": self.evidence,
            "compliance_tags": self.compliance_tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "extra": self.extra,
            "provenance_source": self.provenance_source,
            "provenance_confidence": self.provenance_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalArtifact":
        """Deserialize from dictionary."""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


# Type registry
ARTIFACT_TYPES = frozenset(
    {
        "requirement",
        "architecture",
        "sw_unit",
        "test",
        "evidence",
        "baseline",
    }
)

TYPE_PREFIXES = {
    "requirement": "REQ",
    "architecture": "ARCH",
    "sw_unit": "SWU",
    "test": "TEST",
    "evidence": "EV",
    "baseline": "BL",
}
