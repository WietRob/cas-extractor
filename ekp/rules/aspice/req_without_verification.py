"""
REQ_WITHOUT_VERIFICATION Rule.

ASPICE Reference: SYS.5 / SWE.5

Safety-relevant requirements must have verification tests.
"""

from ekp.core.artifact import CanonicalArtifact
from ekp.core.link import TraceLink
from ..base import Rule, Violation, Severity


class ReqWithoutVerification(Rule):
    rule_id = "REQ_WITHOUT_VERIFICATION"
    description = "Safety-relevant requirement must have verification test"
    severity = Severity.ERROR
    aspice_ref = "SYS.5 / SWE.5"

    SAFETY_TAGS = frozenset(
        {
            "iso26262",
            "asil-a",
            "asil-b",
            "asil-c",
            "asil-d",
            "safety",
            "safety-relevant",
            "functional-safety",
        }
    )

    def evaluate(
        self, artifacts: list[CanonicalArtifact], links: list[TraceLink]
    ) -> list[Violation]:
        req_to_tests: dict[str, list[str]] = {}
        for link in links:
            if link.relation_type == "verifies":
                req_id = link.source_id
                if req_id not in req_to_tests:
                    req_to_tests[req_id] = []
                req_to_tests[req_id].append(link.target_id)

        violations: list[Violation] = []

        for artifact in artifacts:
            if artifact.artifact_type != "req":
                continue

            is_safety_relevant = any(
                self._is_safety_tag(tag) for tag in artifact.compliance_tags
            )

            if not is_safety_relevant:
                continue

            tests = req_to_tests.get(artifact.artifact_id, [])
            if not tests:
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        artifact_id=artifact.artifact_id,
                        message=(
                            f"Safety-relevant requirement '{artifact.title}' "
                            f"has no verification test"
                        ),
                        evidence={
                            "compliance_tags": artifact.compliance_tags,
                            "status": artifact.status,
                        },
                    )
                )

        return violations

    def _is_safety_tag(self, tag: str) -> bool:
        tag_lower = tag.lower()
        return any(safety in tag_lower for safety in self.SAFETY_TAGS)
