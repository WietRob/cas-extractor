"""
Rule Engine for Engineering Knowledge Plane.

Evaluates registered rules against artifacts and links.
"""

from dataclasses import dataclass, field
from typing import Any

from ekp.core.artifact import CanonicalArtifact
from ekp.core.link import TraceLink
from .base import Rule, Violation, Severity


@dataclass
class ValidationResult:
    """Result of rule evaluation."""

    total_rules: int
    total_violations: int
    errors: int
    warnings: int
    info: int
    violations: list[Violation] = field(default_factory=list)
    rule_results: dict[str, list[Violation]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "summary": {
                "total_rules": self.total_rules,
                "total_violations": self.total_violations,
                "errors": self.errors,
                "warnings": self.warnings,
                "info": self.info,
            },
            "violations": [v.to_dict() for v in self.violations],
            "by_rule": {
                rule_id: [v.to_dict() for v in violations]
                for rule_id, violations in self.rule_results.items()
            },
        }

    @property
    def passed(self) -> bool:
        """True if no errors (warnings/info allowed)."""
        return self.errors == 0


class RuleEngine:
    """
    Rule evaluation engine.

    Usage:
        engine = RuleEngine()
        engine.register(ReqWithoutVerification())
        result = engine.evaluate(artifacts, links)
    """

    def __init__(self):
        self._rules: dict[str, Rule] = {}

    def register(self, rule: Rule) -> None:
        """Register a rule."""
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule {rule.rule_id} already registered")
        self._rules[rule.rule_id] = rule

    def unregister(self, rule_id: str) -> None:
        """Unregister a rule."""
        self._rules.pop(rule_id, None)

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a registered rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(self) -> list[str]:
        """List all registered rule IDs."""
        return list(self._rules.keys())

    def evaluate(
        self,
        artifacts: list[CanonicalArtifact],
        links: list[TraceLink],
        rule_filter: set[str] | None = None,
    ) -> ValidationResult:
        """
        Evaluate all (or filtered) rules against artifacts and links.

        Args:
            artifacts: All artifacts in scope
            links: All trace links in scope
            rule_filter: Optional set of rule IDs to evaluate (all if None)

        Returns:
            ValidationResult with all violations
        """
        all_violations: list[Violation] = []
        rule_results: dict[str, list[Violation]] = {}

        errors = 0
        warnings = 0
        info = 0

        rules_to_run = (
            {rid: r for rid, r in self._rules.items() if rid in rule_filter}
            if rule_filter
            else self._rules
        )

        for rule_id, rule in rules_to_run.items():
            violations = rule.evaluate(artifacts, links)
            rule_results[rule_id] = violations
            all_violations.extend(violations)

            for v in violations:
                if v.severity == Severity.ERROR:
                    errors += 1
                elif v.severity == Severity.WARNING:
                    warnings += 1
                else:
                    info += 1

        return ValidationResult(
            total_rules=len(rules_to_run),
            total_violations=len(all_violations),
            errors=errors,
            warnings=warnings,
            info=info,
            violations=all_violations,
            rule_results=rule_results,
        )
