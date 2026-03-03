"""
Rule Base Classes for Engineering Knowledge Plane.

Rules validate artifacts and links, producing violations when conditions are not met.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ekp.core.artifact import CanonicalArtifact
from ekp.core.link import TraceLink


class Severity(str, Enum):
    """Violation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Violation:
    """A rule violation found during validation."""

    rule_id: str
    severity: Severity
    artifact_id: str  # The artifact that caused the violation
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)

    # Additional context
    related_artifacts: list[str] = field(default_factory=list)
    related_links: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "artifact_id": self.artifact_id,
            "message": self.message,
            "evidence": self.evidence,
            "related_artifacts": self.related_artifacts,
            "related_links": self.related_links,
        }


class Rule(ABC):
    """Base class for all validation rules."""

    rule_id: str
    description: str
    severity: Severity
    aspice_ref: str = ""  # ASPICE process reference

    @abstractmethod
    def evaluate(
        self, artifacts: list[CanonicalArtifact], links: list[TraceLink]
    ) -> list[Violation]:
        """
        Evaluate the rule against artifacts and links.

        Args:
            artifacts: All artifacts in scope
            links: All trace links in scope

        Returns:
            List of violations found (empty if rule passes)
        """
        pass

    def __repr__(self) -> str:
        return f"Rule({self.rule_id})"
