# CAS Extractor v0.5.0 GA Release

**Date**: 2026-02-26
**Status**: ✅ GA RELEASED

## Overview

v0.5.0 introduces the **ResolutionEngine** - a new inference system for resolving dynamic Python call targets with full metadata traceability.

## Features

### New Features
1. **ResolutionEngine Integration** - Pluggable resolver chain with priority-based resolution
2. **Resolution Trace Metadata** - Every resolved edge includes trace of which heuristic resolved it
3. **H2.8 FactoryReturnResolver** - Resolves `factory().method()` where factory returns known class
4. **QualifiedAttrResolver** - Resolves `module.func()` calls like `ast.walk()`

### CLI Flags
- `--enable-v050-resolution-engine true` - Enable ResolutionEngine
- `--enable-h27-self-attr-transitive true` - Enable H2.7 inter-method propagation
- `--enable-h28-factory-return true` - Enable H2.8 factory return inference
- `--v050-emit-resolution-trace true` - Include resolution trace in output

## Gate Verification (RC2 Fixes Applied)

### G-A: H2.6/2.7 PropagatedSelfAttrResolver
- **Status**: ✅ PASS
- **Evidence**: `test_gate_A_h27.Service.run -> Client.send` resolved with heuristic `H2.6/2.7`

### G-B: H2.8 FactoryReturnResolver  
- **Status**: ✅ PASS (fixed in RC2)
- **Evidence**: `test_gate_B_h28.main -> Builder.build` resolved with heuristic `H2.8`
- **Fix**: Changed priority from 40 to 1, updated to check local_var_types

### G-C: Trace Contract
- **Status**: ✅ PASS
- **Evidence**: 100% trace coverage on all resolved edges

### G-D: Clean Baseline
- **Status**: ✅ PASS
- **Evidence**: Product-only baseline (cas_extractor/) with 231 edges, 0 drift

## Technical Details

### Product Baseline Statistics
```
Legacy edges (product): 420
Engine edges (product): 231
Resolution traces: 231 (100% coverage)
```

### Heuristics Used (Product)
| Heuristic | Edges |
|------------|-------|
| static | 177 |
| qualified_attr | 54 |

### Parity Status
- ✅ Engine output ⊆ Legacy output (subset relationship)
- ✅ Zero behavior changes for resolved edges
- ✅ No false positives (0 only-engine edges)

## Breaking Changes

None. The engine is opt-in via CLI flag.

## Migration Path

```bash
# Basic engine enable
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-v050-resolution-engine true \
  --out ./output

# Full feature enable (H2.7 + H2.8)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-v050-resolution-engine true \
  --enable-h27-self-attr-transitive true \
  --enable-h28-factory-return true \
  --v050-emit-resolution-trace true \
  --out ./output
```

## Evidence

- Product Baseline: `sprint-v050-engine/06-golden/v050-product-baseline/`
- Gate Fixtures: `sprint-v050-engine/02-fixtures/`
- Trace Assertions: `sprint-v050-engine/04-functional-proof/trace_assertions.txt`

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v0.4.4 | 2026-02-24 | H2.7 GA (legacy) |
| v0.5.0 RC1 | 2026-02-25 | ResolutionEngine - gates pending |
| v0.5.0 | 2026-02-26 | ResolutionEngine GA - all gates passed |
