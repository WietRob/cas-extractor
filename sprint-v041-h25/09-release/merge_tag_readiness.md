# Merge & Tag Readiness — v0.4.1 H2.5

**Release:** v0.4.1
**Feature:** H2.5 — Intra-Method Non-`__init__` Self-Attr Resolution
**Date:** 2026-02-22

---

## Merge Readiness Checklist

### Code Changes

| Item | Status | Notes |
|------|--------|-------|
| Implementation complete | ✅ | `_build_method_local_self_attr_types()` added |
| CLI flag added | ✅ | `--enable-h25-self-attr-noninit` |
| Default OFF | ✅ | Default value `false` |
| No type errors introduced | ✅ | Pre-existing LSP warnings only |
| No crashes/exceptions | ✅ | Verified in smoke tests |

### Testing

| Item | Status | Notes |
|------|--------|-------|
| Mini-fixture tests | ✅ | 11/11 cases pass |
| Smoke tests | ✅ | 307 edges both modes |
| Spot checks | ✅ | 25/25 pass |
| Regression tests | ✅ | H1/H2/H3/H2.1 verified |
| False positive check | ✅ | 0 FP |

### Documentation

| Item | Status | Notes |
|------|--------|-------|
| Scope spec | ✅ | `H2.5_SCOPE_SPEC.md` |
| Implementation design | ✅ | `H2.5_IMPLEMENTATION_DESIGN.md` |
| CLI help text | ✅ | `--help` shows flag |
| Release report | ✅ | `v0.4.1-h25-report.md` |
| Release notes | ⏳ | To be added |

### Evidence

| Item | Status | Notes |
|------|--------|-------|
| Mini-fixture results | ✅ | `04-mini-fixture/` |
| Smoke results | ✅ | `05-smoke/` |
| Benchmark matrix | ✅ | `06-golden/benchmark_matrix.md` |
| Spot checks | ✅ | `07-quality/spot_checks.md` |
| Release gates | ✅ | `09-release/release_gates_validation.md` |
| GO/NO-GO decision | ✅ | `09-release/GO_NO_GO.md` |

---

## Tag Information

### Tag Name

```
v0.4.1
```

### Tag Message

```
v0.4.1 - H2.5 Intra-Method Non-__init__ Self-Attr Resolution

New Feature:
- H2.5: Resolve self.attr.method() where self.attr = ClassName()
  is assigned in non-__init__ methods (same method scope only)

Changes:
- Added _build_method_local_self_attr_types() to python_calls.py
- Added --enable-h25-self-attr-noninit CLI flag (default: false)
- Added CAS_ENABLE_H25_SELF_ATTR_NONINIT env variable

Scope:
- IN: Intra-method write-before-use, Assign/AnnAssign, last-wins
- OUT: Cross-method, factory inference, CFG sensitivity

Testing:
- 6/6 positive cases pass
- 5/5 negative cases pass
- 0 false positives
- 0 regressions in H1/H2/H3/H2.1

Evidence: sprint-v041-h25/
```

---

## Merge Commands (if git repo)

```bash
# If this were a git repo:

# 1. Stage all changes
git add cas_extractor/extractors/python_calls.py
git add extract_python.py
git add sprint-v041-h25/

# 2. Commit
git commit -m "feat: H2.5 intra-method non-__init__ self-attr resolution

- Add _build_method_local_self_attr_types() for H2.5 tracking
- Add --enable-h25-self-attr-noninit CLI flag (default: false)
- Add CAS_ENABLE_H25_SELF_ATTR_NONINIT env variable
- H2.5 priority: method-local > H2 class-level
- Scope: intra-method only, no cross-method propagation

Testing: 11/11 mini-fixture, 25/25 spot checks, 0 FP, 0 regressions
Evidence: sprint-v041-h25/"

# 3. Tag
git tag -a v0.4.1 -m "v0.4.1 - H2.5 Intra-Method Non-__init__ Self-Attr Resolution"

# 4. Push (if applicable)
git push origin main
git push origin v0.4.1
```

---

## Post-Merge Actions

| Action | Status | Owner |
|--------|--------|-------|
| Update RELEASE_NOTES.md | ⏳ Pending | - |
| Announce release | ⏳ Pending | - |
| Update documentation (if external) | ⏳ Pending | - |

---

## Files Changed

| File | Type | Lines Changed |
|------|------|---------------|
| `cas_extractor/extractors/python_calls.py` | Modified | +60 |
| `extract_python.py` | Modified | +9 |
| `sprint-v041-h25/*` | Added | ~100 files |

---

## Rollback Plan

If issues discovered post-release:

1. **Revert to v0.4.0:**
   ```bash
   git checkout v0.4.0
   ```

2. **Hotfix approach:**
   ```bash
   # Disable H2.5 by default (already done)
   # Remove flag if needed
   ```

3. **Point fix:**
   - H2.5 is isolated to specific functions
   - Can be disabled via flag without code changes

---

## Verification Commands

### Post-Merge Verification

```bash
# Verify H2.5 flag exists
python extract_python.py --help | grep "enable-h25"

# Verify H2.5 OFF by default
python extract_python.py \
  --repo-root cas_extractor \
  --repo-name repo://test \
  --revision git:test \
  --out /tmp/verify-off

# Verify H2.5 ON works
python extract_python.py \
  --repo-root cas_extractor \
  --repo-name repo://test \
  --revision git:test \
  --enable-h25-self-attr-noninit true \
  --out /tmp/verify-on
```

---

## Sign-Off

| Check | Status |
|-------|--------|
| All code reviewed | ✅ |
| All tests pass | ✅ |
| All gates pass | ✅ |
| GO decision made | ✅ |
| Documentation complete | ✅ |
| Evidence pack complete | ✅ |

---

**Merge Readiness: APPROVED** ✅

**Tag Readiness: APPROVED** ✅

---

**Document Generated:** 2026-02-22
