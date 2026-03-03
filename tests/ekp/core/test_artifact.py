"""Tests for EKP Core — CanonicalArtifact."""

import pytest
from datetime import datetime

from ekp.core.artifact import (
    CanonicalArtifact,
    ARTIFACT_TYPES,
    TYPE_PREFIXES,
)


class TestCanonicalArtifact:
    def test_create_requirement(self):
        a = CanonicalArtifact(
            artifact_id="REQ-001",
            artifact_type="requirement",
            title="System shall provide login",
        )
        assert a.artifact_id == "REQ-001"
        assert a.artifact_type == "requirement"
        assert a.status == "draft"

    def test_create_sw_unit(self):
        a = CanonicalArtifact(
            artifact_id="SWU-042",
            artifact_type="sw_unit",
            title="Authentication Module",
            compliance_tags=["ISO26262", "ASIL-B"],
        )
        assert "ISO26262" in a.compliance_tags

    def test_invalid_prefix_raises(self):
        with pytest.raises(ValueError, match="artifact_id must start with REQ"):
            CanonicalArtifact(
                artifact_id="WRONG-001",
                artifact_type="requirement",
                title="Invalid ID",
            )

    def test_to_dict_and_from_dict(self):
        original = CanonicalArtifact(
            artifact_id="TEST-001",
            artifact_type="test",
            title="Login Test",
            status="approved",
            compliance_tags=["ASPICE.SYS.5"],
        )
        d = original.to_dict()
        restored = CanonicalArtifact.from_dict(d)
        assert restored.artifact_id == original.artifact_id
        assert restored.artifact_type == original.artifact_type
        assert restored.title == original.title
        assert restored.status == original.status

    def test_serialization_includes_timestamps(self):
        a = CanonicalArtifact(
            artifact_id="ARCH-001",
            artifact_type="architecture",
            title="System Architecture",
        )
        d = a.to_dict()
        assert "created_at" in d
        assert "updated_at" in d
        datetime.fromisoformat(d["created_at"])

    def test_artifact_types_registry(self):
        assert "requirement" in ARTIFACT_TYPES
        assert "architecture" in ARTIFACT_TYPES
        assert "sw_unit" in ARTIFACT_TYPES
        assert "test" in ARTIFACT_TYPES

    def test_type_prefixes(self):
        assert TYPE_PREFIXES["requirement"] == "REQ"
        assert TYPE_PREFIXES["sw_unit"] == "SWU"
