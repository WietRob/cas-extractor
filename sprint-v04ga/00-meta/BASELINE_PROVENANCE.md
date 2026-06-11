# CAS Extractor v0.4 GA — Baseline Provenance

**Sprint:** v0.4 GA Release Hardening & Reproducibility Pack
**Date:** 2026-02-22T09:27:14Z

---

## Extractor Code Stand

| Item | Value |
|------|-------|
| **Project Root** | `/home/roberto_schmidt/projects/Deterministic Knowledge System` |
| **Entry Point** | `extract_python.py` |
| **Core Module** | `cas_extractor/` |
| **Version Tag** | v0.4-rc (pre-GA) |
| **H2.1 Feature** | `--emit-unresolved-self-attr` CLI flag |

### Key Files

| File | Purpose |
|------|---------|
| `extract_python.py` | CLI entry point |
| `cas_extractor/extractors/python_calls.py` | Core call resolution with H2.1 skip logic |
| `cas_extractor/extractors/python_symbols.py` | Symbol extraction |
| `cas_extractor/extractors/python_imports.py` | Import graph extraction |
| `cas_extractor/writers/evidence_writer.py` | YAML evidence serialization |
| `cas_extractor/validators/schema_validate.py` | Structural validation |
| `schemas/cas.evidence.v0.1.schema.json` | Evidence schema definition |

---

## Target Repository

| Item | Value |
|------|-------|
| **Repository** | httpie/cli |
| **Revision** | git:HEAD (as of extraction) |
| **Reference Extraction** | `golden-v03b/`, `golden-v03c/`, `golden-v04rc/` |

---

## Referenzartefakte (Vor-Sprint)

| Version | Directory | Key Metrics |
|---------|-----------|-------------|
| v0.3b | `golden-v03b/` | 2810 edges, 204 method_call, 860 unresolved |
| v0.3c (TRUE) | `golden-v03c/` | 2899 edges, 208 method_call, 945 unresolved, 85 H2 unresolved |
| v0.4-rc (FALSE) | `golden-v04rc/` | 2814 edges, 208 method_call, 860 unresolved, 0 H2 unresolved |

### Delta v0.3b → v0.3c

| Metric | v0.3b | v0.3c | Delta |
|--------|-------|-------|-------|
| Total edges | 2810 | 2899 | +89 |
| method_call | 204 | 208 | +4 |
| Unresolved | 860 | 945 | +85 |
| H2 unresolved | N/A | 85 | +85 |

### Delta v0.3c → v0.4-rc (FALSE mode)

| Metric | v0.3c (TRUE) | v0.4-rc (FALSE) | Delta |
|--------|--------------|-----------------|-------|
| Total edges | 2899 | 2814 | -85 |
| method_call | 208 | 208 | 0 |
| Unresolved | 945 | 860 | -85 |
| H2 unresolved | 85 | 0 | -85 |

---

## Runner-Umgebung

| Item | Value |
|------|-------|
| **OS** | Linux tuxedoschmidt 6.14.0-123037-tuxedo x86_64 |
| **Python** | 3.12.3 |
| **pip** | 25.3 |
| **jsonschema** | 4.10.3 |
| **Date** | 2026-02-22 |
| **Timezone** | Europe/Berlin |

---

## Validation Logs (Referenz)

| Version | Log File |
|---------|----------|
| v0.3b | `validation-v03b.txt` |
| v0.3c | `validation-v03c.txt` |
| v0.4-rc | (to be generated) |

---

## Reports (Referenz)

| Report | Path |
|--------|------|
| v0.3b Final | `v0.3b-final-report.md` |
| v0.3c | `v0.3c-report.md` |
| v0.4-rc | `v0.4rc-report.md` |
| H2.1 Spec | `H2.1-specification.md` |

---

## Sprint Scope

**In Scope:**
- H2.1 Feature-Flag hardening
- Reproducibility Pack (commands, baselines, artifacts)
- GA-Report (A–F Format)
- Release Notes finalization
- CLI/README documentation
- CI/Smoke recipes for Coverage vs Comparability Mode
- Final Gates + GO/NO-GO decision

**Out of Scope:**
- New heuristics (H2.5, Factory inference, cross-method propagation)
- Schema changes
- Refactorings without direct release benefit
- Performance optimization without reproducible measurement

---

## Evidence Structure

```
sprint-v04ga/
├── 00-meta/
│   ├── BASELINE_PROVENANCE.md  (this file)
│   ├── ENV.txt
│   └── RUNLOG.md
├── 01-mini-fixture/
│   ├── true/
│   ├── false/
│   └── comparisons/
├── 02-smoke/
│   ├── coverage/
│   └── comparability/
├── 03-golden/
│   ├── v03b-baseline/
│   ├── v03c-coverage/
│   ├── v04ga-comparability/
│   ├── metrics/
│   └── validation/
├── 04-spot-checks/
│   ├── spot_checks.md
│   └── samples/
├── 05-release/
│   ├── v0.4-ga-report.md
│   ├── GO_NO_GO.md
│   └── release-notes-delta.md
└── 06-commands/
    ├── repro_commands.md
    └── benchmark_commands.md
```

---

**Frozen:** 2026-02-22T09:27:14Z
