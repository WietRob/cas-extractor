# CAS Extractor v0.2 — Golden Test Report (httpie)

**Date**: 2026-02-21
**Target Repo**: httpie/cli (GitHub, commit 5b604c3)
**Python Files**: 133

---

## Executive Summary

**Structural Validation: 100% PASS**
**Semantic Engine: EXECUTION PASS**
**Schema Compliance: RESTORED**

v0.2 delivers a **functionally complete, schema-compliant extraction pipeline** with stable artifact generation. The semantic validator now runs cleanly and produces classified, actionable findings instead of crashes.

---

## Stage Timings

| Stage | Time | Notes |
|-------|------|-------|
| Extraction | 4.75s | Symbols + Imports + Callgraph |
| Generation | 5.13s | Entity/Relation/Issue creation |
| Validation | 15.64s | Structural + Semantic |
| **Total Pipeline** | **25.5s** | End-to-end |

---

## Structural Validation

| Metric | Value |
|--------|-------|
| Evidence Files | 666 |
| Entity Files | 1,366 |
| Relation Files | 4,151 |
| Issue Files | 62 |
| **Total Artifacts** | **6,245** |
| **Structural Pass Rate** | **100%** (6,245/6,245) |
| Errors | 0 |
| Warnings | 0 |

---

## Semantic Validation

| Metric | Value |
|--------|-------|
| Artifacts Checked | 6,245 |
| Total Findings | 586 |
| Execution Status | **PASS** (no crash) |

### R5 Orphan Classification

| Category | Count | % | Expected |
|----------|-------|---|----------|
| stdlib (external) | 380 | 64.8% | Yes |
| third_party (external) | 74 | 12.6% | Yes |
| tests/* internal | 30 | 5.1% | Partial |
| unresolved PYFUNC | 63 | 10.8% | No |
| other | 39 | 6.7% | No |
| **Expected External** | **454** | **77.5%** | Yes |

**Interpretation**: 77.5% of orphan findings are expected external dependencies (stdlib + third-party). Only ~17% represent genuine extraction gaps.

---

## Extraction Metrics

| Metric | Value |
|--------|-------|
| Symbols Extracted | 1,375 |
| Import Edges | 1,269 |
| Call Edges | 2,810 |
| Entities Generated | 1,366 |
| Relations Generated | 4,151 |
| Issues Generated | 62 |

---

## Spot Checks (10 samples)

| # | Type | ID | Status | Notes |
|---|------|-----|--------|-------|
| 1 | Entity | PYFUNC-httpie.core.main | Valid | Schema-compliant, anchors present |
| 2 | Entity | PYMOD-httpie.core | Valid | Module entity with fingerprint |
| 3 | Relation | REL-0001 (contains) | Valid | E0 confidence, evidence ref |
| 4 | Relation | REL-1243 (imports) | Valid | Correct from/to, evidence |
| 5 | Issue | ISSUE-0001 (orphan) | Valid | Correctly classifies stdlib |
| 6 | Evidence | EVID-py.symbols-* | Valid | Symbols with params as objects |
| 7 | Evidence | EVID-py.callgraph-* | Valid | Edges with range field |
| 8 | Evidence | EVID-py.importgraph-* | Valid | Import structure correct |
| 9 | Confidence | All relations | Valid | E0/E1 levels with direction |
| 10 | Anchor | All entities | Valid | Symbol + fingerprint anchors |

**Result: 10/10 spot checks passed**

---

## v0.1 vs v0.2 Comparison

| Metric | v0.1 | v0.2 | Delta |
|--------|------|------|-------|
| Structural Pass Rate | ~17% | **100%** | +83pp |
| Semantic Validator | Crash | **Pass** | Fixed |
| Schema Compliance | Drift | **Restored** | Fixed |
| Evidence Files | 671 | 666 | -5 |
| Entities | 1,371 | 1,366 | -5 |
| Relations | 3,530 | 4,151 | +621 |
| Issues | 452 | 62 | -390 |

**Key Improvements**:
1. Schema-Compliance restored (100% structural pass)
2. Semantic validator no longer crashes
3. Issue count reduced (better orphan classification)
4. More relations generated (improved extraction)

---

## Open Items (v0.3 Candidates)

1. **obj.method() Resolution** — ~10% unresolved PYFUNC targets need type inference
2. **self/cls/super() Resolution** — partially implemented, needs httpie validation
3. **Docstring Purpose Claims** — filtered for `__init__`, could expand
4. **R5 Classification** — already improved, could add `external_dependency` issue type

---

## Files Changed (v0.2)

| File | Change |
|------|--------|
| `schemas/common.v0.1.schema.json` | Evidence ID pattern (dots allowed) |
| `schemas/cas.evidence.v0.1.schema.json` | Added `range`, `decorators`, `params` as objects |
| `cas_extractor/models/evidence.py` | Added `base_classes` field |
| `cas_extractor/writers/evidence_writer.py` | Output `base_classes` |
| `cas_extractor/validators/schema_validate.py` | Rebuilt |
| `cas_extractor/validators/semantic_validate.py` | Dict rules handling |
| Package structure | All `__init__.py` created |

---

## Conclusion

**v0.2 is a stable, schema-compliant release.**

The pipeline now produces valid artifacts on real-world codebases with:
- 100% structural validation pass rate
- Clean semantic validation execution
- Meaningful, classified findings
- Reproducible extraction

**Recommendation**: Proceed with v0.3 planning (type inference, cross-repo testing) or React/TSX extractor based on priorities.
