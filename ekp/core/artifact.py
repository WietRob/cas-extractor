"""Canonical Artifact Model for Engineering Knowledge Plane."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalArtifact:
    artifact_id: str
    artifact_type: str  # req|arch|sw_unit|test|evidence|baseline
    title: str
    status: str = "draft"  # draft|review|approved|baseline
    version: str = "1.0"
    owner: str | None = None
    source_refs: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    compliance_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        expected_prefix = TYPE_PREFIXES.get(self.artifact_type)
        if expected_prefix and not self.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id must start with {expected_prefix} for type {self.artifact_type}, "
                f"got {self.artifact_id}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "status": self.status,
            "version": self.version,
            "owner": self.owner,
            "source_refs": self.source_refs,
            "links": self.links,
            "compliance_tags": self.compliance_tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalArtifact":
        return cls(**data)


ARTIFACT_TYPES = frozenset(
    {
        "req",
        "arch",
        "sw_unit",
        "test",
        "evidence",
        "baseline",
    }
)

TYPE_PREFIXES = {
    "req": "REQ",
    "arch": "ARCH",
    "sw_unit": "SWU",
    "test": "TEST",
    "evidence": "EV",
    "baseline": "BL",
}
