# CAS Extractor v0.4 GA — Merge & Tag Readiness

**Date:** 2026-02-22
**Status:** READY

---

## Pre-Merge Checklist

- [x] All tests pass
- [x] No LSP errors in modified files
- [x] Release notes updated
- [x] GA report written
- [x] GO/NO-GO decision: GO
- [x] Evidence pack complete

---

## Merge Commands

```bash
# 1. Ensure clean working directory
git status

# 2. Stage all changes
git add extract_python.py
git add cas_extractor/extractors/python_calls.py
git add RELEASE_NOTES.md
git add sprint-v04ga/

# 3. Commit
git commit -m "feat(v0.4): add H2.1 feature-flag for comparability mode

- Add --emit-unresolved-self-attr CLI flag (default: true)
- Add CAS_EMIT_UNRESOLVED_SELF_ATTR env variable support
- Skip 3-part H2 unresolved patterns when flag=false
- Preserve H2 resolved dispatches in both modes
- Restore v0.3b metric comparability in FALSE mode
- Keep +4 method_call quality gain in all modes

Verified: 6/6 release gates pass, 25/25 spot checks pass, 0 false positives

Refs: sprint-v04ga/05-release/v0.4-ga-report.md"

# 4. Tag release
git tag -a v0.4.0 -m "CAS Extractor v0.4 GA

Features:
- H2.1 feature-flag for coverage vs comparability mode
- CLI flag: --emit-unresolved-self-attr true|false
- ENV variable: CAS_EMIT_UNRESOLVED_SELF_ATTR

Metrics (FALSE mode):
- Total edges: 2814
- method_call: 208
- H2 3-part unresolved: 0 (skipped)

Quality:
- 6/6 release gates pass
- 25/25 spot checks pass
- 0 false positives
- 0 H1/H3 regression"

# 5. Push (when ready)
git push origin main
git push origin v0.4.0
```

---

## Post-Merge Checklist

- [ ] Verify tag appears on GitHub
- [ ] Create GitHub Release with notes from RELEASE_NOTES.md
- [ ] Update documentation (if applicable)
- [ ] Announce release

---

## Files Changed

| File | Change |
|------|--------|
| `extract_python.py` | +18 lines |
| `cas_extractor/extractors/python_calls.py` | +8 lines |
| `RELEASE_NOTES.md` | +v0.4 section |
| `sprint-v04ga/` | New directory (evidence pack) |

---

## Rollback Procedure

```bash
# If rollback needed:
git revert HEAD
git tag -d v0.4.0
git push origin :v0.4.0
```

---

**Ready for merge and tag.**
