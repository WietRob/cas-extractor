# CAS Extractor v0.4.3 H2.7 Sprint — Baseline Provenance

**Sprint:** v0.4.3 / H2.7 — Bounded Multi-Hop Self-Attr Propagation
**Date:** 2026-02-23
**Baseline:** v0.4.2 GA (H2.6)

---

## Mission

**Ziel:** v0.4.3 mit **H2.7** liefern: **Bounded multi-hop self-attr propagation** across helper chains — konservativ, bounded, flag-gesteuert.

### H2.7 Scope (hart begrenzt)

| In Scope | Out of Scope |
|----------|--------------|
| ✅ Multi-hop helper chains (A→B→C where C assigns) | ❌ Cross-class propagation |
| ✅ Bounded depth (default: 2) | ❌ Dynamic factory return inference |
| ✅ Cycle detection + skip | ❌ Path-sensitive branch analysis |
| ✅ Conservative merge (conflict → unknown) | ❌ Inter-file whole-program recursion |

---

## Baseline Reference (v0.4.2 GA)

### Extractor Stand

| Item | Value |
|------|-------|
| **Project Root** | `/home/roberto_schmidt/projects/Deterministic Knowledge System` |
| **Entry Point** | `extract_python.py` |
| **Core Module** | `cas_extractor/extractors/python_calls.py` |
| **Current Version** | v0.4.2 GA (H2.6) |

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `cas_extractor/extractors/python_calls.py` | Core call resolution | ~930 |
| `extract_python.py` | CLI entry point | ~135 |

### Current Heuristics Stack

| Heuristic | Pattern | Lines |
|-----------|---------|-------|
| H1 | `x = ClassName(); x.method()` | Local var dispatch |
| H2 | `self.attr = ClassName()` in `__init__` | Class-level |
| H2.5 | `self.attr = ClassName()` in same method | Intra-method |
| H2.6 | `self.attr = ClassName()` in called helper | Inter-method (single-hop) |
| H3 | `ClassName().method()` | Constructor chain |

### H2.6 Implementation (Baseline for H2.7)

**Data Structure (ClassInfo):**
```python
class ClassInfo:
    __slots__ = (
        "qname",
        "methods",
        "base_names",
        "self_attr_types",
        "method_self_attr_summaries",  # H2.6: {method_name: {attr: class}}
    )
```

**Propagation Algorithm (H2.6 - Single-hop):**
```python
def _propagate_self_attr_summaries(
    class_node, initial_summaries, class_methods, max_depth=2
):
    # Bounded propagation with cycle detection
    # Max depth = 2 means: caller -> helper -> sub-helper
```

**Resolution Priority (H2.6):**
1. H2.5 method-local (highest)
2. H2.6 propagated (from called helpers)
3. H2 class-level (__init__)

---

## H2.7 Target Patterns

### Example: Multi-hop Chain

```python
class Example:
    def init_client(self):
        self.client = HTTPClient()  # Assignment at depth 2
    
    def prepare(self):
        self.init_client()           # Helper at depth 1
    
    def run(self):
        self.prepare()               # Helper at depth 0
        self.client.send()           # H2.7: Resolve via chain
```

### H2.6 vs H2.7 Comparison

| Pattern | H2.6 | H2.7 |
|---------|------|------|
| `run() -> helper() -> self.attr = Class()` | ❌ Single-hop only | ✅ Resolved |
| `run() -> h1() -> h2() -> self.attr = Class()` | ❌ Depth exceeded | ✅ If depth >= 3 |
| Cross-class helper | ❌ | ❌ |
| Factory return | ❌ | ❌ |
| Cycle A↔B | ❌ Blocked | ❌ Blocked |

---

## Runner-Umgebung

| Item | Value |
|------|-------|
| **OS** | Linux (x86_64) |
| **Python** | 3.12.3 |
| **Date** | 2026-02-23 |

---

## v0.4.2 Reference Metrics (Baseline)

| Metric | v0.4.2 H2.6 OFF | v0.4.2 H2.6 ON |
|--------|-----------------|----------------|
| Total edges (cas_extractor) | 326 | 326 |
| method_call (cas_extractor) | 0 | 0 |
| method_call (mini-fixture) | 23 | 34 |

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| H2.7 positive cases resolved | 100% |
| H2.7 negative cases correct | 100% (0 false positives) |
| H1/H2/H2.5/H2.6/H3 regression | 0 |
| False positives | 0 |
| Spot checks | ≥25 PASS |
| Release gates | 8/8 PASS |

---

## Abbruchkriterien (NO-GO Triggers)

1. **False positives ≥ 1** in H2.7 positive-looking but invalid cases
2. **Unbounded recursion / cycle failure**
3. **Regression in H1/H2/H2.5/H2.6/H3**
4. **Flag OFF alters baseline materially**
5. **Non-reproducible benchmarks**
6. **Runtime blow-up > 2x** without justification
7. **Evidence gaps** (no YAML proof for claimed wins)

---

**Frozen:** 2026-02-23
