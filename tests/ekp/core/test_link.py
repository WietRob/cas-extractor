"""Tests for EKP Core — TraceLink."""

import pytest

from ekp.core.link import (
    TraceLink,
    RELATION_TYPES,
    RELATION_ASPICE_REFS,
)
from ekp.core.provenance import ProvenanceRecord


class TestTraceLink:
    def test_create_verifies_link(self):
        link = TraceLink(
            link_id="trace-001",
            source_id="REQ-001",
            target_id="TEST-101",
            relation_type="verifies",
        )
        assert link.link_id == "trace-001"
        assert link.source_id == "REQ-001"
        assert link.target_id == "TEST-101"
        assert link.relation_type == "verifies"
        assert link.confidence == 1.0

    def test_create_implements_link(self):
        link = TraceLink(
            link_id="trace-002",
            source_id="ARCH-001",
            target_id="SWU-001",
            relation_type="implements",
            confidence=0.95,
        )
        assert link.confidence == 0.95

    def test_invalid_relation_type_raises(self):
        with pytest.raises(ValueError, match="Invalid relation_type"):
            TraceLink(
                link_id="trace-003",
                source_id="REQ-001",
                target_id="REQ-002",
                relation_type="invalid",
            )

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValueError, match="confidence must be between"):
            TraceLink(
                link_id="trace-004",
                source_id="REQ-001",
                target_id="TEST-001",
                relation_type="verifies",
                confidence=1.5,
            )

    def test_to_dict_and_from_dict(self):
        original = TraceLink(
            link_id="trace-005",
            source_id="REQ-001",
            target_id="TEST-001",
            relation_type="verifies",
            confidence=0.9,
            provenance=ProvenanceRecord(
                source="extracted",
                algorithm="semantic_similarity",
                evidence_path=["REQ-001", "keyword:login", "TEST-001"],
            ),
        )
        d = original.to_dict()
        restored = TraceLink.from_dict(d)
        assert restored.link_id == original.link_id
        assert restored.confidence == original.confidence
        assert restored.provenance.evidence_path == original.provenance.evidence_path

    def test_relation_types_registry(self):
        assert "verifies" in RELATION_TYPES
        assert "allocates_to" in RELATION_TYPES
        assert "implements" in RELATION_TYPES

    def test_aspice_refs(self):
        assert RELATION_ASPICE_REFS["verifies"] == "SYS.5 / SWE.5"
        assert RELATION_ASPICE_REFS["allocates_to"] == "SYS.3 / SWE.3"

    def test_default_provenance_is_manual(self):
        link = TraceLink(
            link_id="trace-006",
            source_id="REQ-001",
            target_id="TEST-001",
            relation_type="verifies",
        )
        assert link.provenance.source == "manual"

    def test_provenance_nested_serialization(self):
        link = TraceLink(
            link_id="trace-007",
            source_id="REQ-001",
            target_id="TEST-001",
            relation_type="verifies",
            provenance=ProvenanceRecord(
                source="reconstructed",
                algorithm="trace_reconstruction",
            ),
        )
        d = link.to_dict()
        assert "provenance" in d
        assert d["provenance"]["source"] == "reconstructed"
        restored = TraceLink.from_dict(d)
        assert restored.provenance.source == "reconstructed"
        assert restored.provenance.algorithm == "trace_reconstruction"
