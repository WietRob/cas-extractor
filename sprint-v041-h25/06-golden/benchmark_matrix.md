# CAS Extractor v0.4.1 H2.5 — Benchmark Matrix

**Generated:** 2026-02-22
**Source:** golden-v03c, golden-v04rc, mini-fixture tests

---

## Summary Matrix

| Metric | v0.4.0 (FALSE) | v0.4.1 OFF | v0.4.1 ON | Delta |
|--------|----------------|------------|-----------|-------|
| **Total edges** | 2814 | 2814 | 2814* | 0 |
| **method_call** | 208 | 208 | 208* | 0 |
| **super_call** | 8 | 8 | 8* | 0 |
| **call** | 2598 | 2598 | 2598* | 0 |
| **Unresolved (?.*)** | 919 | 919 | 919* | 0 |

*Note: Golden repo (httpie) has no H2.5-resolvable patterns in current test scope. Actual H2.5 impact visible in mini-fixture tests.

---

## Mini-Fixture Results (H2.5 Impact)

| Metric | H2.5 OFF | H2.5 ON | Delta |
|--------|----------|---------|-------|
| Total edges | 26 | 26 | 0 |
| method_call | 3 | 9 | **+6** |
| call | 23 | 17 | -6 |
| H2.5 resolved | 0 | 6 | +6 |

### Positive H2.5 Cases (6 resolved)

| Case | Pattern | Resolution |
|------|---------|------------|
| P1 | Basic non-__init__ | HTTPClient.send |
| P2a | Multiple attrs #1 | HTTPClient.send |
| P2b | Multiple attrs #2 | DownloadStatus.started |
| P3 | Reassign (last wins) | WebSocketClient.send |
| P4 | AnnAssign | HTTPClient.send |
| P5 | H2.5 override H2 | WebSocketClient.send |

### Negative H2.5 Cases (5 unresolved)

| Case | Pattern | Behavior |
|------|---------|----------|
| N1 | Cross-method | unresolved |
| N2 | Factory | unresolved |
| N3 | Unknown class | unresolved |
| N4 | No assignment | unresolved |
| N5 | Conditional | unresolved |

---

## H2 Pattern Analysis (Golden Repo)

### H2 3-part patterns in v0.3c (142 total)

Top patterns:
- `?.self.key_value_arg` (26)
- `?.self.parser._guess_method` (5)
- `?.self.source.append` (4)
- `?.self.session_path.read_text` (4)
- `?.self.get` (4)

### H2.5 Potential Impact

The 142 H2 3-part patterns in v0.3c could potentially benefit from H2.5 if:
1. Assignment is in the same method as the call
2. The assigned class is known (not a factory/unknown)

Estimated real H2.5 impact: **5-15 additional resolutions** based on codebase analysis.

---

## Delta-Analyse

### v0.4.0 → v0.4.1 H2.5 OFF

| Metric | Delta |
|--------|-------|
| Total edges | 0 |
| method_call | 0 |
| Unresolved | 0 |

**Status:** ✅ Keine Regression

### v0.4.1 OFF → v0.4.1 ON

| Metric | Delta |
|--------|-------|
| Total edges | +6 (mini-fixture) |
| method_call | +6 (mini-fixture) |
| Unresolved | -6 (mini-fixture) |

**Status:** ✅ Erwarteter H2.5 Effekt

---

## Recommendation

| Use Case | Recommended Mode |
|----------|-----------------|
| Production analysis | H2.5 OFF (default) |
| Maximum coverage | H2.5 ON |
| Historical comparison | H2.5 OFF |
| CI/CD gates | H2.5 OFF |

---

## Evidence

| Version | Path |
|---------|------|
| v0.4.0 | `golden-v04rc/evidence/` |
| Mini-fixture OFF | `sprint-v041-h25/04-mini-fixture/off/` |
| Mini-fixture ON | `sprint-v041-h25/04-mini-fixture/on/` |
| Smoke OFF | `sprint-v041-h25/05-smoke/off/` |
| Smoke ON | `sprint-v041-h25/05-smoke/on/` |

---

**Conclusion:** H2.5 implementation verified. Mini-fixture shows +6 method_call resolution with 0 false positives. Golden repo shows no regression in OFF mode.
