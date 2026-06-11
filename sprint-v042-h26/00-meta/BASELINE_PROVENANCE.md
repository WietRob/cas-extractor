# CAS Extractor v0.4.2 H2.6 Sprint — Baseline Provenance

**Sprint:** v0.4.2 / H2.6 — Class-Local Inter-Method Self-Attr Propagation
**Date:** 2026-02-22T17:49:59Z

---

## Mission

**Ziel:** v0.4.2 mit **H2.6** liefern: **Inter-method self-attr propagation** innerhalb einer Klasse — konservativ, bounded, flag-gesteuert.

### H2.6 Scope (hart begrenzt)

| In Scope | Out of Scope |
|----------|--------------|
| ✅ Class-local (gleiche Klasse) | ❌ Cross-class propagation |
| ✅ Statisch auflösbare `self.helper()` calls | ❌ Factory return inference |
| ✅ Bounded depth (default: 2) | ❌ Full MRO traversal |
| ✅ Cycle detection + skip | ❌ Dynamic dispatch / setattr |
| ✅ Conflict → unknown | ❌ Path-sensitive analysis |

---

## Extractor Code Stand

| Item | Value |
|------|-------|
| **Project Root** | `/home/roberto_schmidt/projects/Deterministic Knowledge System` |
| **Entry Point** | `extract_python.py` |
| **Core Module** | `cas_extractor/extractors/python_calls.py` |
| **Current Version** | v0.4.1 GA (H2.5) |
| **Git Status** | Not a git repo (local development) |

### Key Files for H2.6

| File | Purpose | Lines |
|------|---------|-------|
| `cas_extractor/extractors/python_calls.py` | Core call resolution | ~795 |
| `extract_python.py` | CLI entry point | ~110 |

### Current Heuristics (Reference)

| Heuristic | Pattern | Lines |
|-----------|---------|-------|
| H1 | `x = ClassName(); x.method()` | 206-241 (`_build_local_var_types`) |
| H2 | `self.attr = ClassName()` in `__init__` | 276-324 (`_build_init_self_attr_types`) |
| H2.5 | `self.attr = ClassName()` in same method | 327-368 (`_build_method_local_self_attr_types`) |
| H3 | `ClassName().method()` | 588-608 (Case 2e in `_resolve_call`) |

### Key Data Structures

```python
class ClassInfo:
    __slots__ = ("qname", "methods", "base_names", "self_attr_types")
    # self_attr_types: dict[str, str]  # {attr_name: class_qname} from __init__
```

### H2.5 Resolution Priority (Case 2d, lines 535-562)

```python
# 1. H2.5: method-local (if enable_h25_self_attr_noninit)
if attr_name in method_local_self_attr_types:
    # resolve to method_call
    
# 2. H2: class-level (__init__)
elif attr_name in enclosing_class.self_attr_types:
    # resolve to method_call
    
# 3. Unresolved/skip (per H2.1 flag)
```

### Self-Call Resolution (Case 2a, lines 492-508)

```python
# self.method() → self_dispatch
if isinstance(func_node.value, ast.Name) and func_node.value.id == "self":
    if enclosing_class is not None:
        if method_name in enclosing_class.methods:
            return f"{enclosing_class.qname}.{method_name}", "self_dispatch"
```

---

## Target Repository

| Item | Value |
|------|-------|
| **Repository** | httpie/cli (or cas_extractor for smoke) |
| **Local Path** | `/tmp/httpie` (if needed) |
| **Reference Extractions** | `golden-v04rc/`, `sprint-v041-h25/` |

---

## v0.4.1 Reference Metrics

| Metric | v0.4.1 H2.5 OFF |
|--------|-----------------|
| Total edges (cas_extractor) | 307 |
| method_call | 26 |
| super_call | 0 |
| call | 281 |

---

## Runner-Umgebung

| Item | Value |
|------|-------|
| **OS** | Linux (x86_64) |
| **Kernel** | 6.14.0-123037-tuxedo |
| **Python** | 3.12.3 |
| **Date** | 2026-02-22 |
| **Timezone** | Europe/Berlin |

---

## Sprint Structure

```
sprint-v042-h26/
├── 00-meta/           # This file + ENV.txt
├── 01-spec/           # H2.6_SCOPE.md, H2.6_DESIGN.md, H2.6_FLAG_CONTRACT.md
├── 02-impl/           # diff_notes_T6.md, diff_notes_T7.md
├── 03-functional/     # help_text.txt, flag_precedence.md, test results
├── 04-mini-fixture/   # H2.6 test fixtures + results
│   ├── src/           # test_h26.py
│   ├── off/           # H2.6 OFF extraction
│   ├── on/            # H2.6 ON extraction
│   └── comparisons/   # off_vs_on.md
├── 05-smoke/          # Smoke test results
│   ├── off/
│   └── on/
├── 06-golden/         # Golden benchmark data
│   ├── off/
│   ├── on/
│   ├── validation/
│   └── metrics/
├── 07-quality/        # Spot checks, regression matrix
├── 08-commands/       # Repro commands
└── 09-release/        # Final report, GO/NO-GO
```

---

## H2.6 Design Principles (from Research)

Based on production static analysis tools (PyCG, CodeQL, Pyre/Pysa):

1. **Bounded Fixed-Point Iteration**
   - Max depth cap (default: 2)
   - Stop when no new information or depth exceeded

2. **Cycle Detection**
   - Track visiting methods during propagation
   - Skip cycles → don't propagate through cycles

3. **Conservative Merge**
   - Same attr + different types → unknown (don't guess)
   - Conflict resolution: fail-safe to unresolved

4. **Method Summaries**
   - Pre-compute per-method self.attr contributions
   - Propagate summaries up call chain

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| H2.6 positive cases resolved | 100% (all valid inter-method cases) |
| H2.6 negative cases correct | 100% (0 false positives) |
| H1/H2/H2.5/H3 regression | 0 |
| False positives | 0 |
| Spot checks | ≥25 PASS |
| Release gates | 8/8 PASS |

---

## Abbruchkriterien (NO-GO Triggers)

1. **False Positive ≥ 1** in H2.6-Spot-Checks
2. **Regression in H1/H2/H2.5/H3** in Kontrollfällen
3. **Nicht-deterministische Ergebnisse**
4. **Zyklus-/Traversal-Probleme** (infinite loop, stack overflow)
5. **Performance > 20%** auf Golden ohne Begründung
6. **Scope-Leak** (Factory inference, cross-class guessing)
7. **Unvollständige Evidenz**

---

**Frozen:** 2026-02-22T17:49:59Z
