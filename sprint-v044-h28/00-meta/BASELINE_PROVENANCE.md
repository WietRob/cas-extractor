# Baseline Provenance — v0.4.4 H2.8

**Sprint:** v0.4.4 / H2.8 — Factory Return Inference
**Baseline Version:** v0.4.3 GA
**Baseline Date:** 2026-02-23

---

## Baseline Reference

| Attribute | Value |
|-----------|-------|
| Version | v0.4.3 GA |
| Tag | `v0.4.3-h27-ga` |
| Sprint Directory | `sprint-v043-h27/` |
| Release Notes | `RELEASE_NOTES.md` (v0.4.3 section) |
| GO/NO-GO | `sprint-v043-h27/06-release/GO_NO_GO.md` |

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
| H3 Constructor Chain | v0.3a | ✅ Stable |

---

## Baseline Metrics (cas_extractor smoke test)

| Metric | v0.4.3 Value |
|--------|--------------|
| Total edges | 326 |
| method_call | 0 |
| call | 326 |
| unresolved | 0 |

---

## H2.8 Scope Delta

| Aspect | Baseline (v0.4.3) | Target (v0.4.4) |
|--------|-------------------|-----------------|
| Factory return inference | ❌ Not supported | ✅ Bounded inference |
| Factory index | N/A | Module-level factory detection |
| Resolution priority | H2.5 > H2.7 > H2.6 > H2 | H2.5 > H2.7 > H2.6 > H2.8 > H2 |

---

## Regression Prevention

### Must Not Change

- [ ] H1 local var dispatch behavior
- [ ] H2 class-level self.attr dispatch
- [ ] H2.5 intra-method resolution
- [ ] H2.6 inter-method propagation
- [ ] H2.7 multi-hop transitive propagation
- [ ] H3 constructor chain resolution
- [ ] Smoke test edge counts (326 edges)

### Must Add

- [ ] H2.8 factory return inference
- [ ] Factory function type index
- [ ] CLI flags `--enable-h28-factory-return`, `--h28-max-factory-depth`
- [ ] ENV variables `CAS_ENABLE_H28_FACTORY_RETURN`, `CAS_H28_MAX_FACTORY_DEPTH`

---

## Verification Commands

### Baseline Reproduction (v0.4.3 behavior)

```bash
python3 extract_python.py \
  --repo-root ./cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:HEAD \
  --out ./sprint-v044-h28/03-evidence-runs/smoke-off
```

Expected: 326 edges, 0 method_call

### H2.8 Enabled

```bash
python3 extract_python.py \
  --repo-root ./cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:HEAD \
  --enable-h28-factory-return true \
  --out ./sprint-v044-h28/03-evidence-runs/smoke-on
```

Expected: 326 edges (no factory patterns in cas_extractor)

---

**Recorded:** 2026-02-23
