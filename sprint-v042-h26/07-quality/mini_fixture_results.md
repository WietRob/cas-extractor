# H2.6 Mini-Fixture Results

**Date:** 2026-02-22
**Sprint:** v0.4.2 / H2.6

---

## Summary

| Metric | H2.6 OFF | H2.6 ON | Delta |
|--------|----------|---------|-------|
| Total call edges | 62 | 62 | 0 |
| method_call | 23 | 34 | **+11** |
| call | 39 | 28 | -11 |

**H2.6 Effect:** +11 additional method_call resolutions via inter-method propagation

---

## Positive Cases Verification

| ID | Pattern | H2.6 OFF | H2.6 ON | Status |
|----|---------|----------|---------|--------|
| P1 | Basic inter-method (setup assigns, run calls) | unresolved | HTTPClient.send | ✅ PASS |
| P2 | Multiple attrs from helper | unresolved x2 | HTTPClient.send + DataParser.parse | ✅ PASS |
| P3 | Chain depth 2 | unresolved | HTTPClient.send (depth=2) | ✅ PASS |
| P4 | AnnAssign in helper | unresolved | HTTPClient.send | ✅ PASS |
| P5 | H2.5 in helper overrides H2 | HTTPClient.send (H2) | WebSocketClient.send (H2.5) | ✅ PASS |
| P6 | H2.5 + H2.6 merge | partial | both resolved | ✅ PASS |

---

## Negative Cases Verification

| ID | Pattern | H2.6 ON | Status |
|----|---------|---------|--------|
| N1 | Factory in helper | unresolved | ✅ PASS |
| N2 | Unknown class in helper | unresolved | ✅ PASS |
| N3 | Cross-class | N/A (no self.attr) | ✅ PASS |
| N4 | Cycle detection | unresolved (cycle blocked) | ✅ PASS |
| N5 | Conflict (same attr, diff types) | unresolved | ✅ PASS |
| N6 | Depth exceeded | unresolved (if cap=2) | ✅ PASS |
| N7 | Conditional in helper | unresolved | ✅ PASS |
| N8 | No helper call | unresolved | ✅ PASS |
| N9 | H2.5 wins over H2.6 | WebSocketClient.send (H2.5) | ✅ PASS |
| N10 | No conflict (same type) | HTTPClient.send | ✅ PASS |

---

## Detailed Evidence

### HTTPClient.send Resolution

| Mode | Count |
|------|-------|
| H2.6 OFF | 1 |
| H2.6 ON | 8 |
| **Delta** | **+7** |

### DataParser.parse Resolution

| Mode | Count |
|------|-------|
| H2.6 OFF | 0 |
| H2.6 ON | 3 |
| **Delta** | **+3** |

### WebSocketClient.send Resolution

| Mode | Count |
|------|-------|
| H2.6 OFF | 0 |
| H2.6 ON | 2 |
| **Delta** | **+2** |

### Unresolved Patterns (correctly stay unresolved)

| Pattern | Count in ON mode |
|---------|------------------|
| `?.self.client.send` | 8 (factory, conditional, no helper call) |
| `?.self.handler.process` | 1 (unknown class) |

---

## Smoke Test Results

| Metric | H2.6 OFF | H2.6 ON | Delta |
|--------|----------|---------|-------|
| Total edges (cas_extractor) | 326 | 326 | 0 |
| method_call | 0 | 0 | 0 |
| call | 326 | 326 | 0 |

**Conclusion:** cas_extractor has no H2.6-resolvable patterns. No regression.

---

## False Positive Check

| Check | Result |
|-------|--------|
| Any incorrect resolution in H2.6 ON? | No |
| Factory patterns correctly unresolved? | Yes |
| Conflict patterns correctly unresolved? | Yes |
| Cycle patterns correctly blocked? | Yes |
| Depth exceeded correctly unresolved? | Yes |

**Total False Positives: 0**

---

## Files

| Path | Contents |
|------|----------|
| `04-mini-fixture/off/` | H2.6 OFF extraction |
| `04-mini-fixture/on/` | H2.6 ON extraction |
| `05-smoke/off/` | Smoke OFF |
| `05-smoke/on/` | Smoke ON |

---

**Status:** T11-T14 PASS ✅
