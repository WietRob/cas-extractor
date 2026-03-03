"""Tests for EKP Rules — Rule Engine."""

import pytest

from ekp.core.artifact import CanonicalArtifact
from ekp.core.link import TraceLink
from ekp.rules.base import Rule, Violation, Severity
from ekp.rules.engine import RuleEngine, ValidationResult
from ekp.rules.aspice import ReqWithoutVerification


class TestRuleEngine:
    def test_register_and_list_rules(self):
        engine = RuleEngine()
        engine.register(ReqWithoutVerification())
        assert "REQ_WITHOUT_VERIFICATION" in engine.list_rules()

    def test_register_duplicate_raises(self):
        engine = RuleEngine()
        engine.register(ReqWithoutVerification())
        with pytest.raises(ValueError, match="already registered"):
            engine.register(ReqWithoutVerification())

    def test_unregister_rule(self):
        engine = RuleEngine()
        engine.register(ReqWithoutVerification())
        engine.unregister("REQ_WITHOUT_VERIFICATION")
        assert "REQ_WITHOUT_VERIFICATION" not in engine.list_rules()

    def test_evaluate_empty_artifacts(self):
        engine = RuleEngine()
        engine.register(ReqWithoutVerification())
        result = engine.evaluate([], [])
        assert result.passed
        assert result.total_violations == 0

    def test_evaluate_with_rule_filter(self):
        engine = RuleEngine()
        engine.register(ReqWithoutVerification())
        result = engine.evaluate([], [], rule_filter={"NONEXISTENT"})
        assert result.total_rules == 0


class TestReqWithoutVerification:
    def test_safety_req_without_verification_violates(self):
        rule = ReqWithoutVerification()
        artifacts = [
            CanonicalArtifact(
                artifact_id="REQ-001",
                artifact_type="requirement",
                title="Brake shall stop vehicle",
                compliance_tags=["ISO26262", "ASIL-D"],
            ),
        ]
        violations = rule.evaluate(artifacts, [])
        assert len(violations) == 1
        assert violations[0].rule_id == "REQ_WITHOUT_VERIFICATION"
        assert violations[0].artifact_id == "REQ-001"

    def test_safety_req_with_verification_passes(self):
        rule = ReqWithoutVerification()
        artifacts = [
            CanonicalArtifact(
                artifact_id="REQ-001",
                artifact_type="requirement",
                title="Brake shall stop vehicle",
                compliance_tags=["ISO26262", "ASIL-D"],
            ),
            CanonicalArtifact(
                artifact_id="TEST-001",
                artifact_type="test",
                title="Brake Test",
            ),
        ]
        links = [
            TraceLink(
                link_id="trace-001",
                source_id="REQ-001",
                target_id="TEST-001",
                relation_type="verifies",
            ),
        ]
        violations = rule.evaluate(artifacts, links)
        assert len(violations) == 0

    def test_non_safety_req_without_verification_passes(self):
        rule = ReqWithoutVerification()
        artifacts = [
            CanonicalArtifact(
                artifact_id="REQ-002",
                artifact_type="requirement",
                title="UI shall be blue",
                compliance_tags=["UI"],  # Not safety-relevant
            ),
        ]
        violations = rule.evaluate(artifacts, [])
        assert len(violations) == 0

    def test_multiple_safety_reqs(self):
        rule = ReqWithoutVerification()
        artifacts = [
            CanonicalArtifact(
                artifact_id="REQ-001",
                artifact_type="requirement",
                title="Safety Req 1",
                compliance_tags=["ASIL-A"],
            ),
            CanonicalArtifact(
                artifact_id="REQ-002",
                artifact_type="requirement",
                title="Safety Req 2",
                compliance_tags=["safety"],
            ),
            CanonicalArtifact(
                artifact_id="REQ-003",
                artifact_type="requirement",
                title="Non-safety Req",
                compliance_tags=["info"],
            ),
        ]
        links = [
            TraceLink(
                link_id="trace-001",
                source_id="REQ-001",
                target_id="TEST-001",
                relation_type="verifies",
            ),
        ]
        violations = rule.evaluate(artifacts, links)
        assert len(violations) == 1
        assert violations[0].artifact_id == "REQ-002"


class TestValidationResult:
    def test_passed_with_no_errors(self):
        result = ValidationResult(
            total_rules=1,
            total_violations=2,
            errors=0,
            warnings=2,
            info=0,
        )
        assert result.passed

    def test_failed_with_errors(self):
        result = ValidationResult(
            total_rules=1,
            total_violations=1,
            errors=1,
            warnings=0,
            info=0,
        )
        assert not result.passed

    def test_to_dict(self):
        result = ValidationResult(
            total_rules=2,
            total_violations=3,
            errors=1,
            warnings=2,
            info=0,
        )
        d = result.to_dict()
        assert d["summary"]["total_rules"] == 2
        assert d["summary"]["errors"] == 1
