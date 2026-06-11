# CAS Extractor v0.4.1 H2.5 Sprint — Baseline Provenance

**Sprint:** v0.4.1 / H2.5 — Intra-Method Non-`__init__` Self-Attr Resolution
**Date:** 2026-02-22T10:46:09Z

---

## Mission

**Ziel:** v0.4.1 mit **H2.5** liefern: Erweiterung der H2-Heuristik auf **`self.attr = ClassName(...)` außerhalb von `__init__`** — mit **intra-method write-before-use** Resolution.

### H2.5 Scope (hart begrenzt)

| In Scope | Out of Scope |
|----------|--------------|
| ✅ Intra-Method (write-before-use im gleichen Methoden-Body) | ❌ Cross-Method-Propagation |
| ✅ `Assign` + `AnnAssign` | ❌ Factory-Return-Inference |
| ✅ Last-assignment-wins (innerhalb derselben Methode) | ❌ CFG/Branch-Merge/Path-Sensitivity |
| ✅ Nur konservative Resolution | ❌ Interprocedural State Analysis |

---

## Extractor Code Stand

| Item | Value |
|------|-------|
| **Project Root** | `/home/roberto_schmidt/projects/Deterministic Knowledge System` |
| **Entry Point** | `extract_python.py` |
| **Core Module** | `cas_extractor/extractors/python_calls.py` |
| **Current Version** | v0.4.0 GA |
| **Git Status** | Not a git repo (local development) |

### Key Files for H2.5

| File | Purpose | Lines |
|------|---------|-------|
| `cas_extractor/extractors/python_calls.py` | Core call resolution | 795 |
| `extract_python.py` | CLI entry point | 104 |

### H2 Current Implementation (Reference)

| Function | Lines | Purpose |
|----------|-------|---------|
| `_build_init_self_attr_types()` | 272-320 | Tracks `self.attr = ClassName()` in `__init__` only |
| `_resolve_call()` Case 2d | 476-492 | Resolves `self.attr.method()` using `self_attr_types` |
| `ClassInfo.self_attr_types` | 191-192 | Dict `{attr_name: class_qname}` |

### H1 Reference (Method-Local Pattern)

| Function | Lines | Purpose |
|----------|-------|---------|
| `_build_local_var_types()` | 202-237 | Tracks `x = ClassName()` in current method |
| `_resolve_call()` Case 2e H1 | 508-513 | Resolves `x.method()` using `local_var_types` |

---

## Target Repository

| Item | Value |
|------|-------|
| **Repository** | httpie/cli |
| **Local Path** | `/tmp/httpie` (to be cloned if needed) |
| **Reference Extractions** | `golden-v03b/`, `golden-v03c/`, `golden-v04rc/` |

---

## v0.4.0 Reference Metrics

| Metric | v0.4.0 (FALSE mode) |
|--------|---------------------|
| Total edges | 2814 |
| method_call | 208 |
| super_call | 8 |
| call | 2598 |
| Unresolved (?.*) | 919 |
| H2 3-part unresolved | 0 |
| H2 2-part unresolved | 57 |

---

## Runner-Umgebung

| Item | Value |
|------|-------|
| **OS** | Linux (x86_64) |
| **Python** | 3.12.3 |
| **jsonschema** | 4.10.3 |
| **Date** | 2026-02-22 |
| **Timezone** | Europe/Berlin |

---

## Sprint Structure

```
sprint-v041-h25/
├── 00-meta/           # This file + ENV.txt
├── 01-spec/           # H2.5_SCOPE_SPEC.md, H2.5_IMPLEMENTATION_DESIGN.md
├── 02-analysis/       # h25_candidate_inventory.md
├── 03-impl/           # Implementation notes
├── 04-mini-fixture/   # H2.5 test fixtures + results
├── 05-smoke/          # Smoke test results
├── 06-golden/         # Golden benchmark data
├── 07-quality/        # Spot checks, gates, validation
├── 08-commands/       # Repro commands
└── 09-release/        # Final report, GO/NO-GO
```

---

## Success Criteria

| Criterion | Status |
|-----------|--------|
| H2.5 positive cases resolved (method_call) | ⬜ Pending |
| H2.5 negative cases unresolved/skipped | ⬜ Pending |
| No H1/H2/H3/H2.1 regression | ⬜ Pending |
| Golden benchmark reproducible | ⬜ Pending |
| 25+ spot checks PASS | ⬜ Pending |
| 8 Release Gates PASS | ⬜ Pending |

---

## Abbruchkriterien (NO-GO Triggers)

1. **False Positive ≥ 1** in H2.5-Spot-Checks
2. **Regression in H1/H2/H3/H2.1** in Kontrollfällen
3. **Structural Validation < 100%**
4. **Nicht reproduzierbare Metriken**
5. **Scope-Verletzung** (Cross-Method-Propagation / Guessing)
6. **Golden Extractor Crash/Exception** durch H2.5
7. **Metrik-Deltas nicht erklärbar**

---

**Frozen:** 2026-02-22T10:46:09Z
