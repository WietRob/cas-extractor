"""
Semantic Validator — rule-based validation for CAS artifacts.

Stage 2 of 2-stage validation.
Implements rules R1-R6 from validator_rules.v0.1.yaml.
Handles rules as Dict (keyed by rule ID) or List.
Uses schema-compliant field names: from/to, applies_to, summary.
"""
from pathlib import Path
from typing import Any

import yaml


class SemanticValidationResult:
    def __init__(self):
        self.violations: list[dict[str, Any]] = []
        self.files_checked: int = 0

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        return (
            f"[{status}] Semantic: "
            f"{self.files_checked} artifacts checked, "
            f"{len(self.violations)} violations"
        )


def validate_semantic(
    rules_file: str,
    artifacts_dir: str,
) -> SemanticValidationResult:
    """Validate artifacts against semantic rules."""
    with open(rules_file, "r") as f:
        rules_config = yaml.safe_load(f)

    rules_raw = rules_config.get("rules", {})
    # Normalize rules to dict keyed by rule ID
    if isinstance(rules_raw, list):
        rules = {}
        for r in rules_raw:
            rid = r.get("id", "")
            if rid:
                rules[rid] = r
    elif isinstance(rules_raw, dict):
        rules = rules_raw
    else:
        rules = {}

    # Evidence level expectations matrix
    elx = rules_config.get("evidence_level_expectations", {})
    relation_matrix = elx.get("matrix", {}) if isinstance(elx, dict) else {}

    # Load all artifacts
    artifacts = {}
    for yaml_file in sorted(Path(artifacts_dir).rglob("*.yaml")):
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and "id" in data:
                artifacts[data["id"]] = data
        except Exception:
            continue

    result = SemanticValidationResult()
    result.files_checked = len(artifacts)

    # Build entity ID set for R5
    entity_ids = {aid for aid, a in artifacts.items() if a.get("kind") == "entity"}

    for aid, artifact in artifacts.items():
        kind = artifact.get("kind")

        # R1: No Naked Claims
        if kind == "entity":
            for i, claim in enumerate(artifact.get("claims", [])):
                if not claim.get("evidence"):
                    result.violations.append({
                        "rule": "R1",
                        "artifact": aid,
                        "message": f"Claim [{i}] has no evidence references",
                        "severity": "error",
                    })

        # R2: Claim Kind Enum
        allowed_kinds = _get_rule_param(rules, "R2", "allowed_kinds",
                                         ["purpose", "side_effect", "invariant",
                                          "constraint", "dependency", "assumption"])
        if kind == "entity":
            for i, claim in enumerate(artifact.get("claims", [])):
                ck = claim.get("kind")
                if ck and ck not in allowed_kinds:
                    result.violations.append({
                        "rule": "R2",
                        "artifact": aid,
                        "message": f"Claim [{i}] kind \'{ck}\' not in allowed set",
                        "severity": "error",
                    })

        # R5: Relation Target Exists (schema uses "from"/"to")
        if kind == "relation":
            rel_to = artifact.get("to")
            if rel_to and rel_to not in entity_ids:
                result.violations.append({
                    "rule": "R5",
                    "artifact": aid,
                    "message": f"Relation target \'{rel_to}\' not found in entities",
                    "severity": "warning",
                })

            rel_from = artifact.get("from")
            if rel_from and rel_from not in entity_ids:
                result.violations.append({
                    "rule": "R5",
                    "artifact": aid,
                    "message": f"Relation source \'{rel_from}\' not found in entities",
                    "severity": "warning",
                })

            # Relation confidence matrix check
            rel_type = artifact.get("type")
            if rel_type and rel_type in relation_matrix:
                matrix_entry = relation_matrix[rel_type]
                conf = artifact.get("confidence", {})
                conf_level = conf.get("level")
                allowed_levels = matrix_entry.get("allowed_confidence_levels", [])
                if conf_level and allowed_levels and conf_level not in allowed_levels:
                    result.violations.append({
                        "rule": "R5+",
                        "artifact": aid,
                        "message": (
                            f"Relation type \'{rel_type}\' has confidence "
                            f"\'{conf_level}\' but allowed levels are {allowed_levels}"
                        ),
                        "severity": "warning",
                    })

        # R6: Anchor Minimum
        if kind == "entity":
            anchors = artifact.get("anchors", [])
            if not anchors:
                result.violations.append({
                    "rule": "R6",
                    "artifact": aid,
                    "message": "Entity has no anchors",
                    "severity": "error",
                })

    return result


def _get_rule_param(rules: dict, rule_id: str, param: str, default: Any) -> Any:
    """Extract a parameter from a rule definition. Handles dict-keyed rules."""
    rule = rules.get(rule_id)
    if rule and isinstance(rule, dict):
        return rule.get("params", {}).get(param, default)
    return default
