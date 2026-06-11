# Baseline Provenance — v0.4.5 H2.9

**Sprint:** v0.4.5 / H2.9 — Enhanced Resolution Metadata
**Baseline Version:** v0.4.4 GA
**Baseline Date:** 2026-02-23

---

## Baseline Reference

| Attribute | Value |
|-----------|-------|
| Version | v0.4.4 GA |
| Tag | `v0.4.4-h28-ga` |
| Sprint Directory | `sprint-v044-h28/` |
| Release Notes | `RELEASE_NOTES.md` (v0.4.4 section) |
| GO/NO-GO | `sprint-v044-h28/06-release/GO_NO_GO.md` |

---

## Baseline Features

| Feature | Version | Status |
|---------|---------|--------|
| H1 Local Variable Dispatch | v0.3b | ✅ Stable |
| H2 Instance-Attribute Dispatch | v0.3c | ✅ Stable |
| H2.1 Unresolved Self-Attr Flag | v0.4 | ✅ Stable |
| H2.5 Intra-Method Non-Init | v0.4.1 | ✅ Stable |
| H2.6 Inter-Method Propagation | v0.4.2 | ✅ Stable |
| H2.7 Multi-Hop Transitive | v0.4.3 | ✅ Stable |
| H2.8 Factory Return Inference | v0.4.4 | ✅ Stable |
| H3 Constructor Chain | v0.3a | ✅ Stable |

---

## Baseline Metrics (cas_extractor smoke test)

| Metric | v0.4.4 Value |
|--------|--------------|
| Total edges | 338 |
| method_call | 0 |
| call | 338 |
| unresolved | 0 |

---

## H2.9 Scope Delta

| Aspect | Baseline (v0.4.4) | Target (v0.4.5) |
|--------|-------------------|-----------------|
| Resolution metadata | ❌ Not supported | ✅ Add heuristic tracking |
| Source location | ❌ Not tracked | ✅ file:line |
| Inferred type | ❌ Not tracked | ✅ class_qname |
| Behavior | 0 change | 0 change |

---

## Regression Prevention

### Must Not Change

- [ ] H1 local var dispatch behavior
- [ ] H2 class-level self.attr dispatch
- [ ] H2.5 intra-method resolution
- [ ] H2.6 inter-method propagation
- [ ] H2.7 multi-hop transitive propagation
- [ ] H2.8 factory return inference
- [ ] H3 constructor chain resolution
- [ ] Smoke test edge counts (338 edges)

### Must Add

- [ ] H2.9 resolution metadata
- [ ] CLI flag `--enable-h29-resolution-metadata`
- [ ] ENV variable `CAS_ENABLE_H29_RESOLUTION_METADATA`

---

## Verification Commands

### Baseline Reproduction (v0.4.4 behavior)

```bash
python3 extract_python.py \
  --repo-root ./cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:HEAD \
  --out ./sprint-v045-h29/03-evidence-runs/smoke-off
```

Expected: 338 edges, 0 method_call

### H2.9 Enabled

```bash
python3 extract_python.py \
  --repo-root ./cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:HEAD \
  --enable-h29-resolution-metadata true \
  --out ./sprint-v045-h29/03-evidence-runs/smoke-on
```

Expected: 338 edges (no behavior change), metadata field added

---

**Recorded:** 2026-02-23
