# CAS Extractor v0.4.1 H2.5 — Release Gates + Validation

**Date:** 2026-02-22
**Sprint:** v0.4.1 / H2.5 — Intra-Method Non-`__init__` Self-Attr Resolution
**Status:** T19 Final Validation

---

## Gate Summary

| Gate | Description | Status | Evidence |
|------|-------------|--------|----------|
| G1 | Implementation Completeness | ✅ PASS | Section G1 |
| G2 | Test Coverage | ✅ PASS | Section G2 |
| G3 | Zero False Positives | ✅ PASS | Section G3 |
| G4 | Zero Regressions | ✅ PASS | Section G4 |
| G5 | Feature Flag Correct | ✅ PASS | Section G5 |
| G6 | Documentation Complete | ✅ PASS | Section G6 |
| G7 | Evidence Pack Complete | ✅ PASS | Section G7 |
| G8 | Reproducibility | ✅ PASS | Section G8 |

**Overall:** 8/8 Gates PASS ✅

---

## G1: Implementation Completeness

### Requirement
All H2.5 scope items implemented as specified in `H2.5_SCOPE_SPEC.md`.

### Validation Checklist

| Item | Spec Requirement | Implementation | Status |
|------|------------------|----------------|--------|
| G1.1 | `self.attr = ClassName()` in non-`__init__` method | `_build_method_local_self_attr_types()` lines 327-368 | ✅ |
| G1.2 | `AnnAssign` support | Lines 355-366 in `_build_method_local_self_attr_types()` | ✅ |
| G1.3 | Write-before-use in same method | Method-local dict built before `_resolve_call()` | ✅ |
| G1.4 | Last-assignment-wins | Dict overwrites on reassignment (lines 353-354) | ✅ |
| G1.5 | H2.5 priority over H2 | Case 2d: H2.5 check before H2 check | ✅ |
| G1.6 | Feature flag `--enable-h25-self-attr-noninit` | `extract_python.py` lines 60-68 | ✅ |
| G1.7 | ENV variable `CAS_ENABLE_H25_SELF_ATTR_NONINIT` | `extract_python.py` lines 63-65 | ✅ |
| G1.8 | Default OFF | Default `false` (line 63-64) | ✅ |

### Out-of-Scope Verified (NOT implemented)

| Item | Status |
|------|--------|
| Cross-method propagation | ✅ NOT implemented (correct) |
| Factory return inference | ✅ NOT implemented (correct) |
| CFG/Path-sensitive analysis | ✅ NOT implemented (correct) |

**G1 Result:** ✅ PASS

---

## G2: Test Coverage

### Requirement
Mini-fixture tests cover all positive and negative H2.5 cases.

### Positive Cases (6)

| ID | Pattern | Expected | Actual | Status |
|----|---------|----------|--------|--------|
| P1 | Basic non-`__init__` | HTTPClient.send | HTTPClient.send | ✅ |
| P2a | Multiple attrs #1 | HTTPClient.send | HTTPClient.send | ✅ |
| P2b | Multiple attrs #2 | DownloadStatus.started | DownloadStatus.started | ✅ |
| P3 | Reassign (last wins) | WebSocketClient.send | WebSocketClient.send | ✅ |
| P4 | AnnAssign | HTTPClient.send | HTTPClient.send | ✅ |
| P5 | H2.5 override H2 | WebSocketClient.send | WebSocketClient.send | ✅ |

**Positive Coverage:** 6/6 PASS ✅

### Negative Cases (5)

| ID | Pattern | Expected | Actual | Status |
|----|---------|----------|--------|--------|
| N1 | Cross-method | unresolved | `?.self.client.send` | ✅ |
| N2 | Factory | unresolved | `?.self.client.send` | ✅ |
| N3 | Unknown class | unresolved | `?.self.handler.process` | ✅ |
| N4 | No assignment | unresolved | `?.self.client.send` | ✅ |
| N5 | Conditional | unresolved | `?.self.client.send` | ✅ |

**Negative Coverage:** 5/5 PASS ✅

### Evidence

- Positive matrix: `sprint-v041-h25/04-mini-fixture/positive_case_matrix.md`
- Negative matrix: `sprint-v041-h25/04-mini-fixture/negative_case_matrix.md`
- ON results: `sprint-v041-h25/04-mini-fixture/on/`
- OFF results: `sprint-v041-h25/04-mini-fixture/off/`

**G2 Result:** ✅ PASS

---

## G3: Zero False Positives

### Requirement
No incorrect resolutions in H2.5 ON mode.

### Validation

| Check | Result | Details |
|-------|--------|---------|
| H2.5 positive correct | ✅ 6/6 | All resolved to correct target class |
| H2.5 negative correct | ✅ 5/5 | All remain unresolved |
| No guessing | ✅ | Factory/unknown/conditional stay unresolved |
| No cross-method | ✅ | N1 cross-method correctly unresolved |

### False Positive Count: 0

### False Negative Count: 0

**G3 Result:** ✅ PASS

---

## G4: Zero Regressions

### Requirement
H1/H2/H3/H2.1 behavior unchanged in v0.4.1.

### Smoke Test Comparison

| Metric | H2.5 OFF | H2.5 ON | Delta |
|--------|----------|---------|-------|
| Total edges (cas_extractor) | 307 | 307 | 0 |
| method_call | 26 | 26 | 0 |
| super_call | 0 | 0 | 0 |
| call | 281 | 281 | 0 |

**Status:** No regression in cas_extractor (has no H2.5 patterns)

### H1 Regression Check (Local Var Dispatch)

| Pattern | OFF | ON | Status |
|---------|-----|-----|--------|
| `x = HTTPClient(); x.send()` | HTTPClient.send | HTTPClient.send | ✅ |
| Multiple local vars | resolved | resolved | ✅ |
| Reassign local var | last wins | last wins | ✅ |
| AnnAssign local var | resolved | resolved | ✅ |
| Cross-function | unresolved | unresolved | ✅ |

**H1 Status:** ✅ No regression

### H2 Regression Check (Class-Level __init__)

| Pattern | OFF | ON | Status |
|---------|-----|-----|--------|
| `__init__: self.client = HTTPClient()` | HTTPClient.send | HTTPClient.send | ✅ |
| Multiple attrs in __init__ | resolved | resolved | ✅ |
| Reassign in __init__ | last wins | last wins | ✅ |
| AnnAssign in __init__ | resolved | resolved | ✅ |
| No __init__ | unresolved | unresolved | ✅ |

**H2 Status:** ✅ No regression

### H3 Regression Check (Constructor Chain)

| Pattern | OFF | ON | Status |
|---------|-----|-----|--------|
| `HTTPClient().send()` | HTTPClient.send | HTTPClient.send | ✅ |
| `DownloadStatus().started()` | DownloadStatus.started | DownloadStatus.started | ✅ |
| Imported class ctor | resolved | resolved | ✅ |
| Unknown class ctor | unresolved | unresolved | ✅ |

**H3 Status:** ✅ No regression

### H2.1 Flag Regression

| Pattern | `--emit-unresolved-self-attr true` | `--emit-unresolved-self-attr false` |
|---------|-------------------------------------|-------------------------------------|
| Unresolved self.attr | Edge emitted | Edge skipped |
| H2.5 unresolved | Edge emitted | Edge skipped |

**H2.1 Status:** ✅ No regression

**G4 Result:** ✅ PASS

---

## G5: Feature Flag Correct

### Requirement
H2.5 flag defaults to OFF, correctly enables/disables H2.5 resolution.

### Flag Behavior

| Test | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| Default | `python extract_python.py ...` | H2.5 OFF | H2.5 OFF | ✅ |
| CLI ON | `--enable-h25-self-attr-noninit true` | H2.5 ON | H2.5 ON | ✅ |
| CLI OFF | `--enable-h25-self-attr-noninit false` | H2.5 OFF | H2.5 OFF | ✅ |
| ENV ON | `CAS_ENABLE_H25_SELF_ATTR_NONINIT=true` | H2.5 ON | H2.5 ON | ✅ |
| ENV OFF | `CAS_ENABLE_H25_SELF_ATTR_NONINIT=false` | H2.5 OFF | H2.5 OFF | ✅ |

### Edge Cases

| Case | Behavior | Status |
|------|----------|--------|
| `__init__` method | H2.5 skipped (uses H2) | ✅ |
| Non-`__init__` method with no self.attr | No H2.5 applied | ✅ |
| Mixed __init__ + non-__init__ | H2 for __init__, H2.5 for others | ✅ |

**G5 Result:** ✅ PASS

---

## G6: Documentation Complete

### Requirement
All specification and design documents present.

### Documentation Checklist

| Document | Path | Status |
|----------|------|--------|
| Baseline Provenance | `sprint-v041-h25/00-meta/BASELINE_PROVENANCE.md` | ✅ |
| Environment Info | `sprint-v041-h25/00-meta/ENV.txt` | ✅ |
| H2.5 Scope Spec | `sprint-v041-h25/01-spec/H2.5_SCOPE_SPEC.md` | ✅ |
| Implementation Design | `sprint-v041-h25/01-spec/H2.5_IMPLEMENTATION_DESIGN.md` | ✅ |
| Repro Commands | `sprint-v041-h25/08-commands/repro_commands.md` | ✅ |
| Benchmark Commands | `sprint-v041-h25/08-commands/benchmark_commands.md` | ✅ |
| Positive Case Matrix | `sprint-v041-h25/04-mini-fixture/positive_case_matrix.md` | ✅ |
| Negative Case Matrix | `sprint-v041-h25/04-mini-fixture/negative_case_matrix.md` | ✅ |
| Benchmark Matrix | `sprint-v041-h25/06-golden/benchmark_matrix.md` | ✅ |
| Spot Checks | `sprint-v041-h25/07-quality/spot_checks.md` | ✅ |
| Release Gates (this file) | `sprint-v041-h25/09-release/release_gates_validation.md` | ✅ |

**G6 Result:** ✅ PASS

---

## G7: Evidence Pack Complete

### Requirement
All evidence directories populated with extraction results.

### Evidence Structure

| Directory | Contents | Status |
|-----------|----------|--------|
| `04-mini-fixture/off/` | H2.5 OFF extraction | ✅ |
| `04-mini-fixture/on/` | H2.5 ON extraction | ✅ |
| `05-smoke/off/` | Smoke OFF (cas_extractor) | ✅ |
| `05-smoke/on/` | Smoke ON (cas_extractor) | ✅ |
| `06-golden/` | Benchmark matrix + metrics | ✅ |
| `07-quality/` | Spot checks (25/25) | ✅ |

### File Counts

| Directory | YAML Files | Status |
|-----------|------------|--------|
| `04-mini-fixture/on/` | 11 | ✅ |
| `04-mini-fixture/off/` | 3 | ✅ |
| `05-smoke/on/` | 38 | ✅ |
| `05-smoke/off/` | 38 | ✅ |

**G7 Result:** ✅ PASS

---

## G8: Reproducibility

### Requirement
All extractions reproducible with documented commands.

### Reproduction Commands Verified

| Command | Documented | Verifiable | Status |
|---------|------------|------------|--------|
| H2.5 Flag Help | ✅ `repro_commands.md` A.1 | ✅ | ✅ |
| H2.5 OFF Mini-Fixture | ✅ `repro_commands.md` B.2 | ✅ | ✅ |
| H2.5 ON Mini-Fixture | ✅ `repro_commands.md` B.3 | ✅ | ✅ |
| Smoke OFF | ✅ `repro_commands.md` C.1 | ✅ | ✅ |
| Smoke ON | ✅ `repro_commands.md` C.2 | ✅ | ✅ |
| ENV Variable Test | ✅ `repro_commands.md` A.4 | ✅ | ✅ |

### Determinism Check

| Run | Total Edges | method_call | Status |
|-----|-------------|-------------|--------|
| Mini-Fixture OFF Run 1 | 26 | 3 | ✅ |
| Mini-Fixture OFF Run 2 | 26 | 3 | ✅ |
| Mini-Fixture ON Run 1 | 26 | 9 | ✅ |
| Mini-Fixture ON Run 2 | 26 | 9 | ✅ |
| Smoke OFF | 307 | 26 | ✅ |
| Smoke ON | 307 | 26 | ✅ |

**G8 Result:** ✅ PASS

---

## Validation Summary

### Gate Results

| Gate | Result |
|------|--------|
| G1: Implementation Completeness | ✅ PASS |
| G2: Test Coverage | ✅ PASS |
| G3: Zero False Positives | ✅ PASS |
| G4: Zero Regressions | ✅ PASS |
| G5: Feature Flag Correct | ✅ PASS |
| G6: Documentation Complete | ✅ PASS |
| G7: Evidence Pack Complete | ✅ PASS |
| G8: Reproducibility | ✅ PASS |

### Metrics Summary

| Metric | Value |
|--------|-------|
| Positive H2.5 cases resolved | 6/6 |
| Negative H2.5 cases correct | 5/5 |
| False positives | 0 |
| False negatives | 0 |
| H1/H2/H3 regressions | 0 |
| Spot checks PASS | 25/25 |
| Release gates PASS | 8/8 |

### NO-GO Triggers Check

| Trigger | Status |
|---------|--------|
| False Positive ≥ 1 | ✅ Not triggered (0 FP) |
| Regression in H1/H2/H3/H2.1 | ✅ Not triggered |
| Structural Validation < 100% | ✅ Not triggered (100%) |
| Non-reproducible metrics | ✅ Not triggered |
| Scope violation | ✅ Not triggered |
| Golden extractor crash | ✅ Not triggered |
| Unexplained metric deltas | ✅ Not triggered |

---

## Conclusion

**All 8 release gates PASS.**

**No NO-GO triggers activated.**

**v0.4.1 H2.5 is ready for GA release.**

---

**Validated:** 2026-02-22
**Next Step:** T20 - v0.4.1 RC/GA Report + GO/NO-GO + Merge Readiness
