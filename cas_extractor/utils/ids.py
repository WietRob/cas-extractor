"""
CAS ID generation — strict schema-compliant IDs.

Patterns (from common.v0.1.schema.json):
  entity_id:   ^(PYFUNC|PYCLS|PYMOD|WEB-COMP|WEB-HOOK|WEB-MOD|API-EP|DATA-MDL)-[a-zA-Z0-9_.]+$
  evidence_id: ^EVID-[a-z0-9._]+-[a-f0-9]{8}$
  issue_id:    ^ISSUE-[0-9]{4,}$
  relation_id: ^REL-[0-9]+$
"""
import hashlib

# Global counters for sequential IDs
_issue_counter = 0
_relation_counter = 0


def reset_counters():
    """Reset sequential counters (call at start of each generation run)."""
    global _issue_counter, _relation_counter
    _issue_counter = 0
    _relation_counter = 0


def entity_id(kind: str, qualified_name: str) -> str:
    """Generate a CAS entity ID matching ^(PYFUNC|PYCLS|PYMOD|...)-[a-zA-Z0-9_.]+$"""
    prefix_map = {
        "function": "PYFUNC",
        "method": "PYFUNC",
        "class": "PYCLS",
        "module": "PYMOD",
        "variable": "PYFUNC",  # fallback
    }
    prefix = prefix_map.get(kind, "PYFUNC")
    # Sanitize: only allow [a-zA-Z0-9_.]
    safe_name = "".join(c if c.isalnum() or c in "._" else "_" for c in qualified_name)
    return f"{prefix}-{safe_name}"


def evidence_id(evidence_type: str, scope: str) -> str:
    """Generate a CAS evidence ID matching ^EVID-[a-z0-9._]+-[a-f0-9]{8}$"""
    # type slug: py.symbols -> py.symbols (keep dots, lowercase)
    type_slug = evidence_type.lower()
    # hash8 from scope
    hash8 = hashlib.sha256(scope.encode()).hexdigest()[:8]
    return f"EVID-{type_slug}-{hash8}"


def relation_id(rel_type: str = "", source_id: str = "", target_id: str = "") -> str:
    """Generate a CAS relation ID matching ^REL-[0-9]+$"""
    global _relation_counter
    _relation_counter += 1
    return f"REL-{_relation_counter:04d}"


def issue_id(kind: str = "", target_id: str = "") -> str:
    """Generate a CAS issue ID matching ^ISSUE-[0-9]{4,}$"""
    global _issue_counter
    _issue_counter += 1
    return f"ISSUE-{_issue_counter:04d}"
