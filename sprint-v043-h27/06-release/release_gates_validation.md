# CAS Extractor v0.4.3 H2.7 — Release Gates + Validation

**Date:** 2026-02-23
**Sprint:** v0.4.3 / H2.7 — Bounded Multi-Hop Self-Attr Propagation

---

## Gate Summary

| Gate | Description | Status | Evidence |
|------|-------------|--------|----------|
| G1 | Flag present, default OFF | ✅ PASS | Section G1 |
| G2 | Mini-fixture OFF reproducible | ✅ PASS | Section G2 |
| G3 | Mini-fixture ON resolves positive cases | ✅ PASS | Section G3 |
| G4 | Negative cases = 0 false positives | ✅ PASS | Section G4 |
| G5 | No regression in H1/H2/H2.5/H2.6/H3 | ✅ PASS | Section G5 |
| G6 | Cycle detection + bounded depth | ✅ PASS | Section G6 |
| G7 | Golden benchmark complete | ✅ PASS | Section G7 |
| G8 | Release pack complete | ✅ PASS | Section G8 |

**Overall:** 8/8 Gates PASS ✅

---

## G1: Flag Present, Default OFF

| Check | Result |
|-------|--------|
| `--enable-h27-self-attr-transitive` in help | ✅ |
| `--h27-max-chain-depth` in help | ✅ |
| Default `false` verified | ✅ |
| ENV variable supported | ✅ |

**G1 Result:** ✅ PASS

---

## G2: Mini-Fixture OFF Reproducible

| Metric | Value |
|--------|-------|
| Total edges | 75 |
| method_call | 35 |
| call | 40 |

**Baseline unchanged:** Same as v0.4.2 behavior when H2.7 OFF.

**G2 Result:** ✅ PASS

---

## G3: Mini-Fixture ON Resolves Positive Cases

| Metric | OFF | ON | Delta |
|--------|-----|-----|-------|
| method_call | 35 | 46 | **+11** |
| HTTPClient.send | 1 | 7 | **+6** |

### Positive Cases Verified

| ID | Pattern | Depth | Status |
|----|---------|-------|--------|
| P1 | Two-hop (run→prepare→init) | 2 | ✅ HTTPClient.send |
| P2 | Three-hop chain | 3 | ✅ HTTPClient.send |
| P3 | Multiple attrs from chain | 2 | ✅ |
| P4 | AnnAssign in chain | 2 | ✅ |
| P5 | H2.5 + H2.7 merge | 2 | ✅ |
| P6 | H2.7 overrides H2 | 2 | ✅ |
| P7 | Fan-in chain | 2 | ✅ |

**G3 Result:** ✅ PASS

---

## G4: Negative Cases = 0 False Positives

### Negative Cases Verified

| ID | Pattern | Expected | Actual | Status |
|----|---------|----------|--------|--------|
| N1 | Cycle detection | unresolved | unresolved | ✅ |
| N2 | Depth exceeded | unresolved | unresolved | ✅ |
| N3 | Cross-class helper | unresolved | unresolved | ✅ |
| N4 | Factory in chain | unresolved | unresolved | ✅ |
| N5 | Conflict from paths | unresolved | unresolved | ✅ |
| N6 | Unknown class | unresolved | unresolved | ✅ |
| N7 | Conditional in chain | unresolved | unresolved | ✅ |
| N8 | No chain call | unresolved | unresolved | ✅ |
| N9 | H2.5 wins over H2.7 | H2.5 class | H2.5 class | ✅ |
| N10 | Non-existent helper | unresolved | unresolved | ✅ |

### Smoke Test (cas_extractor)

| Mode | method_call | False Positives |
|------|-------------|-----------------|
| OFF | 0 | 0 |
| ON | 0 | 0 |

**False Positive Count: 0**

**G4 Result:** ✅ PASS

---

## G5: No Regression in H1/H2/H2.5/H2.6/H3

### H2.6 Compatibility Test

| Test | Expected | Actual | Status |
|-------|----------|--------|--------|
| H2.6 fixture HTTPClient.send | 8 | 8 | ✅ |

### Smoke Test Comparison

| Metric | v0.4.2 | v0.4.3 OFF | v0.4.3 ON | Status |
|--------|--------|------------|-----------|--------|
| Total edges | 326 | 326 | 326 | ✅ |
| method_call | 0 | 0 | 0 | ✅ |

**Regression Count: 0**

**G5 Result:** ✅ PASS

---

## G6: Cycle Detection + Bounded Depth

### Cycle Test

| Test | Pattern | Result | Status |
|------|---------|--------|--------|
| N1 | method_a ↔ method_b | No infinite loop, unresolved | ✅ |

### Depth Test

| Depth | Three-hop resolution | Status |
|-------|---------------------|--------|
| 2 | unresolved | ✅ (correct) |
| 3 | HTTPClient.send | ✅ (correct) |

**G6 Result:** ✅ PASS

---

## G7: Golden Benchmark Complete

| Benchmark | OFF | ON | Status |
|-----------|-----|-----|--------|
| cas_extractor edges | 326 | 326 | ✅ |
| cas_extractor method_call | 0 | 0 | ✅ |

**G7 Result:** ✅ PASS

---

## G8: Release Pack Complete

| Document | Path | Status |
|----------|------|--------|
| Baseline Provenance | `00-meta/BASELINE_PROVENANCE.md` | ✅ |
| H2.7 Scope Spec | `01-spec/H2.7_SCOPE.md` | ✅ |
| H2.7 Flag Contract | `01-spec/H2.7_FLAG_CONTRACT.md` | ✅ |
| Mini-fixture source | `/tmp/h27-verify/test_h27.py` | ✅ |
| Mini-fixture OFF | `03-evidence-runs/mini-off/` | ✅ |
| Mini-fixture ON | `03-evidence-runs/mini-on/` | ✅ |
| Smoke OFF | `03-evidence-runs/smoke-off/` | ✅ |
| Smoke ON | `03-evidence-runs/smoke-on/` | ✅ |
| Release Gates (this file) | `06-release/release_gates_validation.md` | ✅ |

**G8 Result:** ✅ PASS

---

## NO-GO Triggers Check

| Trigger | Status |
|---------|--------|
| False positives ≥ 1 | ✅ Not triggered (0 FP) |
| Unbounded recursion | ✅ Not triggered |
| Regression in H1/H2/H2.5/H2.6/H3 | ✅ Not triggered |
| Flag OFF alters baseline | ✅ Not triggered |
| Non-reproducible benchmarks | ✅ Not triggered |
| Runtime blow-up > 2x | ✅ Not triggered |
| Evidence gaps | ✅ Not triggered |

---

## Conclusion

**All 8 release gates PASS.**

**No NO-GO triggers activated.**

**v0.4.3 H2.7 is ready for GA release.**

---

**Validated:** 2026-02-23
