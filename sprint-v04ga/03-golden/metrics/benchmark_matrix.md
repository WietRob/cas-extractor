# CAS Extractor v0.4 GA — Benchmark Matrix

**Generated:** 2026-02-22T09:35:00Z
**Source:** golden-v03b, golden-v03c, golden-v04rc

---

## Summary Matrix

| Metric | v0.3b | v0.3c (TRUE) | v0.4-rc (FALSE) | v0.3b→v0.3c | v0.3c→v0.4-rc | v0.3b→v0.4-rc |
|--------|-------|--------------|-----------------|-------------|---------------|---------------|
| **Total edges** | 2810 | 2899 | 2814 | +89 | -85 | +4 |
| **method_call** | 204 | 208 | 208 | +4 | 0 | +4 |
| **super_call** | 8 | 8 | 8 | 0 | 0 | 0 |
| **call** | 2598 | 2683 | 2598 | +85 | -85 | 0 |
| **Unresolved (?.*)** | 919 | 1004 | 919 | +85 | -85 | 0 |
| **H2 3-part unresolved** | N/A | 85 | **0** | +85 | **-85** | N/A |
| **H2 2-part unresolved** | 57 | 57 | 57 | 0 | 0 | 0 |

---

## H2 Unresolved Pattern Analysis

### 3-part Patterns (`?.self.<attr>.<method>`)

| Version | Count | Status |
|---------|-------|--------|
| v0.3c (TRUE) | 85 | Present (coverage mode) |
| v0.4-rc (FALSE) | **0** | **Skipped** (comparability mode) |

### 2-part Patterns (`?.self.<method>`)

| Version | Count | Status |
|---------|-------|--------|
| v0.3c (TRUE) | 57 | Present |
| v0.4-rc (FALSE) | 57 | Present (not affected by H2.1 flag) |

---

## Delta Analysis

### v0.3b → v0.3c (H2 Coverage Expansion)

- **+89 total edges**: New coverage from H2 instance-attribute dispatch
- **+4 method_call**: H2 resolved dispatches (quality gain)
- **+85 unresolved**: H2 3-part patterns now visible (coverage gain)
- **Behavior**: Maximum visibility, but breaks metric comparability

### v0.3c → v0.4-rc (H2.1 Comparability Mode)

- **-85 total edges**: H2 3-part unresolved skipped in FALSE mode
- **0 method_call**: H2 resolved dispatches preserved
- **-85 unresolved**: All H2 3-part patterns removed
- **Behavior**: Restores metric comparability while keeping quality gain

### v0.3b → v0.4-rc (Net Effect)

- **+4 total edges**: Net gain from H2 quality improvements
- **+4 method_call**: H2 resolved dispatches (permanent quality gain)
- **0 unresolved**: Comparability restored
- **Behavior**: Best of both worlds - quality gain + comparability

---

## Key Findings

### G1: H2 Quality Gain Preserved ✅

- `method_call` increased from 204 → 208 in both v0.3c and v0.4-rc
- The +4 resolved H2 dispatches are never lost

### G2: H2 Coverage Gain Controllable ✅

- TRUE mode (v0.3c): 85 additional 3-part unresolved edges visible
- FALSE mode (v0.4-rc): 0 additional 3-part unresolved edges
- Flag provides clean on/off for coverage vs comparability

### G3: Historical Comparability Restored ✅

- v0.4-rc (FALSE) has identical unresolved count to v0.3b (919)
- v0.4-rc (FALSE) has identical call count to v0.3b (2598)
- Total edge delta v0.3b → v0.4-rc is exactly +4 (the H2 quality gain)

### G4: 2-part Patterns Unaffected ✅

- 57 2-part `?.self.<method>` patterns remain in both modes
- H2.1 flag only affects 3-part patterns
- No regression in other unresolved detection

---

## Mode Recommendations

| Use Case | Recommended Mode | Flag Value |
|----------|------------------|------------|
| Production analysis | Coverage | `true` (default) |
| Historical metric comparison | Comparability | `false` |
| CI/CD quality gates | Comparability | `false` |
| Debugging / code review | Coverage | `true` |
| Release benchmarking | Comparability | `false` |

---

## Evidence Paths

| Version | Path |
|---------|------|
| v0.3b | `golden-v03b/evidence/` |
| v0.3c | `golden-v03c/evidence/` |
| v0.4-rc | `golden-v04rc/evidence/` |

---

## Verification Commands

```bash
# Count 3-part H2 unresolved
grep -h "to: ?.self\." golden-v*/evidence/EVID-py.callgraph-*.yaml | grep -v "to: ?.self\.[^.]*$" | wc -l

# Count 2-part H2 unresolved
grep -h "to: ?.self\." golden-v*/evidence/EVID-py.callgraph-*.yaml | grep "to: ?.self\.[^.]*$" | wc -l

# Count total edges
grep -h "to:" golden-v*/evidence/EVID-py.callgraph-*.yaml | wc -l
```

---

**Conclusion:** H2.1 implementation is correct. v0.4-rc in FALSE mode provides H2 quality gain (+4 method_call) while restoring historical metric comparability (identical unresolved/call counts to v0.3b).
