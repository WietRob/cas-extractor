# CAS Extractor v0.4.1 H2.5 — Spot Checks

**Date:** 2026-02-22
**Scope:** H2.5-specific + H1/H2/H3/H2.1 regression

---

## Spot Check Summary

| Category | Count | Status |
|----------|-------|--------|
| E.1 H2.5 Positive | 6 | ✅ PASS |
| E.2 H2.5 Negative | 5 | ✅ PASS |
| E.3 H2 Regression | 5 | ✅ PASS |
| E.4 H1 Regression | 5 | ✅ PASS |
| E.5 H3 Regression | 4 | ✅ PASS |
| **Total** | **25** | **25/25 PASS** |

---

## E.1 H2.5 Positive Cases

| # | Pattern | H2.5 ON | H2.5 OFF | Status |
|---|---------|---------|----------|--------|
| 1 | `setup(): self.client = HTTPClient(); self.client.send()` | HTTPClient.send (method_call) | unresolved | ✅ |
| 2 | `configure(): self.status = DownloadStatus(); self.status.started()` | DownloadStatus.started (method_call) | unresolved | ✅ |
| 3 | `reconnect(): self.client = HTTPClient(); self.client = WebSocketClient(); self.client.send()` | WebSocketClient.send (method_call) | unresolved | ✅ |
| 4 | `initialize(): self.client: HTTPClient = HTTPClient(); self.client.send()` | HTTPClient.send (method_call) | unresolved | ✅ |
| 5 | `reconnect(): self.client = WebSocketClient()` (override H2) | WebSocketClient.send (method_call) | HTTPClient.send (H2) | ✅ |
| 6 | `run(): self.client.send()` (H2 fallback) | HTTPClient.send (method_call) | HTTPClient.send (method_call) | ✅ |

**Evidence:** `sprint-v041-h25/04-mini-fixture/positive_case_matrix.md`

---

## E.2 H2.5 Negative Cases

| # | Pattern | H2.5 ON | H2.5 OFF | Status |
|---|---------|---------|----------|--------|
| 1 | Cross-method: `setup()` assigns, `run()` calls | unresolved | unresolved | ✅ |
| 2 | Factory: `self.client = self._create()` | unresolved | unresolved | ✅ |
| 3 | Unknown class: `self.handler = SomeUnknownClass()` | unresolved | unresolved | ✅ |
| 4 | No assignment: `self.client.send()` without prior assignment | unresolved | unresolved | ✅ |
| 5 | Conditional: `if x: self.client = ...` | unresolved | unresolved | ✅ |

**Evidence:** `sprint-v041-h25/04-mini-fixture/negative_case_matrix.md`

---

## E.3 H2 Regression (v0.4 H2 should work in v0.4.1)

| # | Pattern | v0.4.1 ON | v0.4.1 OFF | Status |
|---|---------|-----------|------------|--------|
| 1 | `__init__: self.client = HTTPClient()` + `run(): self.client.send()` | HTTPClient.send | HTTPClient.send | ✅ |
| 2 | Multiple attrs in __init__ | resolved | resolved | ✅ |
| 3 | Reassign in __init__ | last wins | last wins | ✅ |
| 4 | AnnAssign in __init__ | resolved | resolved | ✅ |
| 5 | No __init__ | unresolved | unresolved | ✅ |

**Evidence:** `/tmp/h2-verify/test_h2.py` existing tests

---

## E.4 H1 Regression (local var dispatch)

| # | Pattern | v0.4.1 ON | v0.4.1 OFF | Status |
|---|---------|-----------|------------|--------|
| 1 | `x = HTTPClient(); x.send()` | HTTPClient.send | HTTPClient.send | ✅ |
| 2 | Multiple local vars | resolved | resolved | ✅ |
| 3 | Reassign local var | last wins | last wins | ✅ |
| 4 | AnnAssign local var | resolved | resolved | ✅ |
| 5 | Cross-function | unresolved | unresolved | ✅ |

**Evidence:** Existing H1 tests in codebase

---

## E.5 H3 Regression (constructor chain)

| # | Pattern | v0.4.1 ON | v0.4.1 OFF | Status |
|---|---------|-----------|------------|--------|
| 1 | `HTTPClient().send()` | HTTPClient.send | HTTPClient.send | ✅ |
| 2 | `DownloadStatus().started()` | DownloadStatus.started | DownloadStatus.started | ✅ |
| 3 | Imported class ctor | resolved | resolved | ✅ |
| 4 | Unknown class ctor | unresolved | unresolved | ✅ |

**Evidence:** Existing H3 tests in codebase

---

## False Positive Check

| Check | Result |
|-------|--------|
| Any incorrect resolution in H2.5 ON? | No |
| Any incorrect skip in H2.5 ON? | No |
| Any regression in H1/H2/H3? | No |

**Total False Positives: 0**
**Total False Negatives: 0**

---

## Evidence Paths

| Evidence | Path |
|----------|------|
| Mini-fixture ON | `sprint-v041-h25/04-mini-fixture/on/` |
| Mini-fixture OFF | `sprint-v041-h25/04-mini-fixture/off/` |
| Positive matrix | `sprint-v041-h25/04-mini-fixture/positive_case_matrix.md` |
| Negative matrix | `sprint-v041-h25/04-mini-fixture/negative_case_matrix.md` |

---

**Status:** 25/25 PASS ✅
