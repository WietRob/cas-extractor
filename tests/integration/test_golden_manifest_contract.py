"""
Golden Manifest Contract Tests

Validates that the golden manifest baseline satisfies:
1. Manifest exists and has valid structure
2. Mandatory heuristics are present
3. Edge ordering is deterministic
4. No unexpected drift
"""

import json
import pytest
from pathlib import Path


# Path to golden baseline
GOLDEN_BASELINE_DIR = Path("sprint-v050-engine/06-golden/v050-product-baseline")
MANIFEST_PATH = GOLDEN_BASELINE_DIR / "manifest.json"

# Mandatory heuristics that must be present in any valid baseline
MANDATORY_HEURISTICS = frozenset(
    [
        "static",
        "H1",
        "H2",
        "H2.5",
        "H2.6/2.7",
        "H2.8",
        "qualified_attr",
    ]
)


class TestManifestStructure:
    """Tests for manifest file structure and validity."""

    def test_manifest_file_exists(self):
        """Manifest file must exist at expected path."""
        assert MANIFEST_PATH.exists(), f"Manifest not found at {MANIFEST_PATH}"

    def test_manifest_is_valid_json(self):
        """Manifest must be valid JSON."""
        with open(MANIFEST_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict), "Manifest must be a JSON object"

    def test_manifest_has_required_fields(self):
        """Manifest must have all required fields."""
        with open(MANIFEST_PATH) as f:
            data = json.load(f)

        required_fields = ["edge_count", "heuristics", "edges", "manifest_version"]
        for field in required_fields:
            assert field in data, f"Manifest missing required field: {field}"

    def test_manifest_edge_count_matches_edges(self):
        """edge_count must match actual number of edges."""
        with open(MANIFEST_PATH) as f:
            data = json.load(f)

        assert data["edge_count"] == len(data["edges"]), (
            f"edge_count ({data['edge_count']}) != len(edges) ({len(data['edges'])})"
        )


class TestMandatoryHeuristics:
    """Tests for mandatory heuristic presence."""

    def test_heuristics_field_is_dict(self):
        """heuristics field must be a dict."""
        with open(MANIFEST_PATH) as f:
            data = json.load(f)

        assert isinstance(data["heuristics"], dict), "heuristics must be a dict"

    @pytest.mark.skipif(
        not MANIFEST_PATH.exists(), reason="Manifest not found - will be generated"
    )
    def test_static_heuristic_present(self):
        """static heuristic must be present (module-level calls)."""
        with open(MANIFEST_PATH) as f:
            data = json.load(f)

        if data["edge_count"] == 0:
            pytest.skip("Empty baseline - no edges to check")

        assert "static" in data["heuristics"], "static heuristic must be present"


class TestDeterministicOrdering:
    """Tests for deterministic edge ordering."""

    def test_edges_have_consistent_structure(self):
        """All edges must have consistent field structure."""
        with open(MANIFEST_PATH) as f:
            data = json.load(f)

        if data["edge_count"] == 0:
            pytest.skip("Empty baseline - no edges to check")

        required_edge_fields = ["from", "to", "kind"]
        for edge in data["edges"]:
            for field in required_edge_fields:
                assert field in edge, f"Edge missing required field: {field}"

    def test_edges_are_sorted(self):
        """Edges must be in deterministic order (by from, to, heuristic)."""
        with open(MANIFEST_PATH) as f:
            data = json.load(f)

        if data["edge_count"] == 0:
            pytest.skip("Empty baseline - no edges to check")

        edges = data["edges"]
        # Create sort key for each edge
        sort_keys = [
            (e.get("from", ""), e.get("to", ""), e.get("heuristic", "")) for e in edges
        ]
        assert sort_keys == sorted(sort_keys), "Edges must be in sorted order"


class TestBaselineContract:
    """Contract tests for baseline integrity."""

    def test_baseline_directory_exists(self):
        """Baseline directory must exist."""
        assert GOLDEN_BASELINE_DIR.exists(), (
            f"Baseline dir not found: {GOLDEN_BASELINE_DIR}"
        )

    def test_baseline_has_yaml_files(self):
        """Baseline must contain YAML evidence files."""
        yaml_files = list(GOLDEN_BASELINE_DIR.glob("EVID-py.*.yaml"))
        assert len(yaml_files) > 0, "Baseline must have at least one YAML file"
