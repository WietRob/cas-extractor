# SMOKE TEST EVIDENCE - T15 Complete

**Date**: 2026-02-25
**Status**: ✅ ALL TESTS PASS

## Test Run

```
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-v050-resolution-engine true \
  --v050-emit-resolution-trace true \
  --out ./sprint-v050-engine/05-smoke/engine
```

## Results

### Edge Count
```
Legacy edges: 784
Engine edges: 416
Delta: -368 (filtered internal/unresolved)
```

### Parity Status
```
[EXACT] 291 unique edges, 416 total match exactly
[ONLY LEGACY] 239 unique edges, 368 total (all internal)
[ONLY ENGINE] 0 unique edges
```

### Resolution Traces
```
Total edges: 416
With trace: 416
Trace coverage: 100.0%
```

### Heuristics Used
| Heuristic | Edges Resolved |
|-----------|---------------|
| static | 298 |
| qualified_attr | 115 |
| super_dispatch | 3 |

## Conclusion

- ✅ Engine runs without errors
- ✅ All resolved edges have trace metadata
- ✅ All H2.x heuristics functional (qualified_attr, super_dispatch)
- ✅ Parity maintained (engine ⊆ legacy)
- ✅ No false positives (0 only-engine edges)
