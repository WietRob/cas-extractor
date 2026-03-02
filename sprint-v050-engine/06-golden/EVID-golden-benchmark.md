# GOLDEN BENCHMARK - T16-T18 Complete

**Date**: 2026-02-25
**Status**: ✅ BASELINE ESTABLISHED

## Golden Baseline

**Location**: `sprint-v050-engine/06-golden/v050-baseline/`

### Edge Count
```
Engine edges: 416
Resolution traces: 416 (100% coverage)
```

### Heuristics Distribution
| Heuristic | Edges |
|------------|-------|
| static | 298 |
| qualified_attr | 115 |
| super_dispatch | 3 |

### Parity Status
```
[EXACT] 291 unique edges, 416 total match legacy
[ONLY LEGACY] 239 unique edges, 368 total (internal noise)
[ONLY ENGINE] 0 edges
```

## Verification Command

To verify future runs match this baseline:

```bash
# Run engine
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-v050-resolution-engine true \
  --v050-emit-resolution-trace true \
  --out ./test-run

# Compare with golden
cd sprint-v050-engine/08-commands
python3 compare_results.py ../06-golden/v050-baseline ../test-run
```

Expected output: `[EXACT] 291 unique edges, 416 total match exactly`

## Change Log

| Version | Date | Edge Count | Notes |
|---------|------|------------|-------|
| v0.5.0-baseline | 2026-02-25 | 416 | Initial golden baseline |

## Stability Guarantee

This baseline represents the **deterministic output** of the ResolutionEngine v0.5.0. Any regression in edge count or resolution behavior will be detected by the comparison script.
