# CAS Extractor v0.4 GA — Release Gates

**Date:** 2026-02-22
**Status:** GO ✅

---

## Gate Summary

| Gate | Description | Status |
|------|-------------|--------|
| G1 | Flag vorhanden + Default korrekt | ✅ PASS |
| G2 | Mini-Fixture TRUE/FALSE PASS | ✅ PASS |
| G3 | Positive H2 identisch (TRUE vs FALSE) | ✅ PASS |
| G4 | H2 unresolved in FALSE vollständig geskippt | ✅ PASS |
| G5 | H1/H3 Regression = none | ✅ PASS |
| G6 | Benchmark Matrix konsistent + reproduzierbar | ✅ PASS |

**Overall:** 6/6 PASS → **GO** ✅

---

## G1: Flag vorhanden + Default korrekt

**PASS Criteria:**
- CLI-Flag `--emit-unresolved-self-attr` vorhanden
- ENV-Variable `CAS_EMIT_UNRESOLVED_SELF_ATTR` funktioniert
- Default = `true`
- Help-Text korrekt

**Evidence:**
```
--emit-unresolved-self-attr EMIT_UNRESOLVED_SELF_ATTR
    Emit unresolved self.attr.method() calls (default:
    true). Set CAS_EMIT_UNRESOLVED_SELF_ATTR env var or
    use --emit-unresolved-self-attr false
```

**Status:** ✅ PASS

---

## G2: Mini-Fixture TRUE/FALSE PASS

**PASS Criteria:**
- TRUE mode: extraction completes, edges generated
- FALSE mode: extraction completes, edges generated
- Both modes: no errors

**Evidence:**
```
TRUE mode:  → 20 call edges found
FALSE mode: → 16 call edges found
```

**Status:** ✅ PASS

---

## G3: Positive H2 identisch (TRUE vs FALSE)

**PASS Criteria:**
- Resolved H2 dispatches present in both modes
- `method_call` count identical

**Evidence:**
```
✅ test_h2.HTTPClient.send: present in both modes
✅ test_h2.ClassB.foo: present in both modes
✅ test_h2.Session.load: present in both modes
✅ test_h2.DownloadStatus.started: present in both modes
✅ test_h2.DownloadStatus.finished: present in both modes

method_call: TRUE=7 FALSE=7 (identical)
```

**Status:** ✅ PASS

---

## G4: H2 unresolved in FALSE vollständig geskippt

**PASS Criteria:**
- 3-part H2 unresolved (`?.self.<attr>.<method>`) present in TRUE
- 3-part H2 unresolved absent in FALSE
- Golden: 85 → 0 delta

**Evidence:**
```
Mini-Fixture:
  TRUE: 4 H2 unresolved edges
  FALSE: 0 H2 unresolved edges

Golden:
  v0.3c (TRUE): 85 3-part H2 unresolved
  v0.4-rc (FALSE): 0 3-part H2 unresolved
```

**Status:** ✅ PASS

---

## G5: H1/H3 Regression = none

**PASS Criteria:**
- Keine Unterschiede außerhalb H2-unresolved Skip-Verhalten
- method_call/super_call außer H2-Delta stabil

**Evidence:**
```
Mini-Fixture:
  method_call: TRUE=7 FALSE=7 ✅
  
Golden:
  method_call: v0.3c=208 v0.4-rc=208 ✅
  super_call: v0.3c=8 v0.4-rc=8 ✅
  call (non-H2): v0.3c=2598 v0.4-rc=2598 ✅
  2-part H2 unresolved: v0.3c=57 v0.4-rc=57 ✅
```

**Status:** ✅ PASS

---

## G6: Benchmark Matrix konsistent + reproduzierbar

**PASS Criteria:**
- A–F Report vollständig
- Benchmark-Matrix vorhanden
- Metrics mit Provenance
- Deltas erklärbar

**Evidence:**
```
v0.3b → v0.3c: +89 edges, +4 method_call, +85 H2 unresolved
v0.3c → v0.4-rc: -85 edges, 0 method_call, -85 H2 unresolved
v0.3b → v0.4-rc: +4 edges, +4 method_call, 0 unresolved delta

All deltas match expected behavior.
```

**Status:** ✅ PASS

---

## Gate Check Commands

```bash
# G1: Check flag
python3 extract_python.py --help | grep emit-unresolved-self-attr

# G2: Run mini-fixture
python3 extract_python.py --repo-root /tmp/h2-verify --emit-unresolved-self-attr true --out /tmp/test-true
python3 extract_python.py --repo-root /tmp/h2-verify --emit-unresolved-self-attr false --out /tmp/test-false

# G3: Compare positive H2
diff <(grep "kind: method_call" /tmp/test-true/*.yaml) <(grep "kind: method_call" /tmp/test-false/*.yaml)

# G4: Check H2 unresolved skip
grep "to: ?.self\." /tmp/test-true/*.yaml | grep -v "\.[^.]*$"
grep "to: ?.self\." /tmp/test-false/*.yaml | grep -v "\.[^.]*$"  # should be empty

# G5: Regression check
grep "kind: super_call" golden-v03c/evidence/*.yaml | wc -l
grep "kind: super_call" golden-v04rc/evidence/*.yaml | wc -l

# G6: Verify benchmark matrix
cat sprint-v04ga/03-golden/metrics/benchmark_matrix.md
```

---

## Conclusion

**All 6 gates PASS. v0.4 GA is ready for release.**

**Decision:** GO ✅

---

**Gates Verified:** 2026-02-22T09:36:00Z
