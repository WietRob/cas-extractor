# CAS Extractor v0.4 GA — Spot Checks

**Date:** 2026-02-22
**Scope:** Formal verification of H2.1 behavior

---

## Spot Check Categories

| Category | Count | Status |
|----------|-------|--------|
| E.1 Positive H2 (both modes) | 6 | ✅ |
| E.2 Negative H2 (flag effect) | 4 | ✅ |
| E.3 H1/H3 Regression | 10 | ✅ |
| E.4 Golden Comparison | 5 | ✅ |
| **Total** | **25** | **25/25 PASS** |

---

## E.1 Positive H2 Cases (identical in TRUE and FALSE)

These resolved H2 dispatches should appear in both modes:

| # | From | To | TRUE | FALSE | Status |
|---|------|-----|------|-------|--------|
| 1 | TestBasic.run | HTTPClient.send | ✅ present | ✅ present | ✅ |
| 2 | TestMultipleAttrs.start | DownloadStatus.started | ✅ present | ✅ present | ✅ |
| 3 | TestMultipleAttrs.finish | DownloadStatus.finished | ✅ present | ✅ present | ✅ |
| 4 | TestMultipleAttrs.send | HTTPClient.send | ✅ present | ✅ present | ✅ |
| 5 | TestReassignment.run | ClassB.foo | ✅ present | ✅ present | ✅ |
| 6 | TestAnnotated.run | Session.load | ✅ present | ✅ present | ✅ |

**Evidence:** `sprint-v04ga/01-mini-fixture/comparisons/t7-positive-h2-diff.txt`

---

## E.2 Negative H2 Cases (flag effect)

These unresolved H2 dispatches should appear in TRUE but be skipped in FALSE:

| # | Pattern | TRUE | FALSE | Status |
|---|---------|------|-------|--------|
| 1 | `?.self.client.send` (not in __init__) | ✅ present | ❌ skipped | ✅ |
| 2 | `?.self.session.load` (no __init__) | ✅ present | ❌ skipped | ✅ |
| 3 | `?.self.handler.process` (unknown class) | ✅ present | ❌ skipped | ✅ |
| 4 | Any `?.self.<attr>.<method>` in golden | 85 found | 0 found | ✅ |

**Evidence:** `sprint-v04ga/01-mini-fixture/comparisons/t8-negative-h2-flag-effect.txt`

---

## E.3 H1/H3 Regression Checks

These non-H2 dispatches should be identical in both modes:

| # | Check | TRUE | FALSE | Status |
|---|-------|------|-------|--------|
| 1 | method_call count (mini-fixture) | 7 | 7 | ✅ |
| 2 | method_call count (golden) | 208 | 208 | ✅ |
| 3 | super_call count (golden) | 8 | 8 | ✅ |
| 4 | call count (golden, non-H2) | 2598 | 2598 | ✅ |
| 5 | Unresolved count (golden, non-H2-3part) | 919 | 919 | ✅ |
| 6 | 2-part H2 unresolved (`?.self.<method>`) | 57 | 57 | ✅ |
| 7 | Total edges delta (mini-fixture) | 20 | 16 | ✅ (-4 expected) |
| 8 | Total edges delta (golden) | 2899 | 2814 | ✅ (-85 expected) |
| 9 | smoke-test edges | 302 | 302 | ✅ |
| 10 | smoke-test symbols | 88 | 88 | ✅ |

**Evidence:** `sprint-v04ga/01-mini-fixture/comparisons/t9-h1-h3-regression.txt`

---

## E.4 Golden Comparison Checks

Verify golden test consistency:

| # | Check | Expected | Actual | Status |
|---|-------|----------|--------|--------|
| 1 | v0.3b → v0.3c total edge delta | +89 | +89 | ✅ |
| 2 | v0.3b → v0.3c method_call delta | +4 | +4 | ✅ |
| 3 | v0.3c → v0.4-rc 3-part H2 delta | -85 | -85 | ✅ |
| 4 | v0.3b → v0.4-rc method_call delta | +4 | +4 | ✅ |
| 5 | v0.4-rc 3-part H2 unresolved | 0 | 0 | ✅ |

**Evidence:** `sprint-v04ga/03-golden/metrics/benchmark_matrix.md`

---

## Sample Evidence

### Mini-Fixture TRUE mode (20 edges, 7 method_call, 13 call)

```
    to: ?.self.client.send
    to: ?.self.handler.process
    to: ?.self.session.load
    to: ?.SomeUnknownClass
    to: test_h2.ClassB
    to: test_h2.ClassB.foo
    to: test_h2.DownloadStatus
    to: test_h2.DownloadStatus.finished
    to: test_h2.DownloadStatus.started
    to: test_h2.HTTPClient
    to: test_h2.HTTPClient.send
    to: test_h2.Session
    to: test_h2.Session.load
```

### Mini-Fixture FALSE mode (16 edges, 7 method_call, 9 call)

```
    to: ?.SomeUnknownClass
    to: test_h2.ClassB
    to: test_h2.ClassB.foo
    to: test_h2.DownloadStatus
    to: test_h2.DownloadStatus.finished
    to: test_h2.DownloadStatus.started
    to: test_h2.HTTPClient
    to: test_h2.HTTPClient.send
    to: test_h2.Session
    to: test_h2.Session.load
```

### Delta Analysis

- **Removed in FALSE:** 4 edges (all `?.self.<attr>.<method>` patterns)
- **Preserved in FALSE:** All resolved H2 dispatches (`test_h2.*` targets)
- **False positives:** 0

---

## Summary

| Metric | Value |
|--------|-------|
| Total spot checks | 25 |
| Passed | 25 |
| Failed | 0 |
| False positives | 0 |
| False negatives | 0 |

**Status:** ✅ ALL CHECKS PASS

---

**Verified:** 2026-02-22T09:35:00Z
