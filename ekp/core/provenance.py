"""
Provenance Record for Engineering Knowledge Plane.

Tracks the origin and derivation chain of trace links and artifacts.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


@dataclass
class ProvenanceRecord:
    """Records the origin and derivation of a trace relationship."""

    source: str  # manual|extracted|reconstructed|derived
    algorithm: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    evidence_path: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source": self.source,
            "algorithm": self.algorithm,
            "timestamp": self.timestamp,
            "evidence_path": self.evidence_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProvenanceRecord":
        """Deserialize from dictionary."""
        return cls(**data)


# Valid provenance sources
PROVENANCE_SOURCES = frozenset(
    {
        "manual",
        "extracted",
        "reconstructed",
        "derived",
    }
)
