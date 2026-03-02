# v0.5.0 Migration Design Spec

## 1. Overview

**What**: Migrate from monolithic `_resolve_call()` function to ResolutionEngine architecture.

**Why**: Cleaner architecture, better testability, explainability, maintainability.

**Scope**: H1-H3, H2.5-H2.8 heuristics. No new features, only refactoring.

## 2. Architecture

### Current (Legacy)
```
python_calls.py:755-942
_extract_calls_from_tree()
  → builds context (local_var_types, etc.)
  → calls _resolve_call(func_node, context...)
  → returns (callee, resolution_type)
```

### Target (Engine)
```
python_calls.py:755-942 (modified)
_extract_calls_from_tree()
  → builds CallContext
  → if engine_enabled:
      → ResolutionEngine.resolve(context)
    else:
      → _resolve_call(legacy path)
  → maps ResolutionResult → CallEntry
```

### Data Flow
```
AST Walk → Build Context → Resolve (Legacy/Engine) → Map Result → CallEntry
```

## 3. Resolver Priority Order

| Priority | Resolver | Heuristic |
|----------|----------|-----------|
| 10 | StaticResolver | static |
| 15 | LocalVarResolver | H1 |
| 20 | MethodLocalSelfAttrResolver | H2.5 |
| 30 | PropagatedSelfAttrResolver | H2.6/2.7 |
| 40 | FactoryReturnResolver | H2.8 |
| 50 | ClassInitSelfAttrResolver | H2 |
| 60 | ConstructorResolver | H3 |
| 70 | SelfDispatchResolver | self.method |
| 80 | ClsDispatchResolver | cls.method |
| 90 | SuperDispatchResolver | super.method |
| 100 | UnresolvedSelfAttrResolver | skip |

## 4. CallContext Fields

```python
@dataclass
class CallContext:
    func_node: ast.expr
    enclosing_func: str
    enclosing_class: ClassInfo | None
    local_var_types: dict[str, str]          # H1
    method_local_self_attr_types: dict[str, str]  # H2.5
    propagated_self_attr_types: dict[str, str | None]  # H2.6/2.7
    self_attr_types: dict[str, str]          # H2
    factory_return_types: dict[str, str]      # H2.8
    module_qname: str
    local_symbols: set[str]
    local_imports: dict[str, str]
    local_classes: dict[str, ClassInfo]
    all_classes: dict[str, ClassInfo]
    emit_unresolved_self_attr: bool = True
```

## 5. ResolutionResult Fields

```python
@dataclass
class ResolutionResult:
    callee: str                    # "module.Class.method" or "?.xxx"
    resolution_type: str           # "static", "self_dispatch", etc.
    heuristic: str                 # "H1", "H2.5", "self_dispatch", etc.
    trace: list[ResolutionStep]    # Explainability
    confidence: float = 1.0
```

## 6. Resolution Type Mapping

| Legacy Type | Engine Value |
|-------------|--------------|
| static | static |
| qualified | qualified |
| self_dispatch | self_dispatch |
| cls_dispatch | cls_dispatch |
| super_dispatch | super_dispatch |
| ctor_dispatch | ctor_dispatch |
| local_var_dispatch | local_var_dispatch |
| self_attr_dispatch | self_attr_dispatch |
| unresolved | unresolved |
| skip | skip |

## 7. Integration Points

### Entry
- `extract_calls()` in `cas_extractor/extractors/python_calls.py`
- Passes all H2.x flags through

### Integration
- In `_extract_calls_from_tree()` around line 712
- Build `CallContext` from existing context data
- Call `engine.resolve(context)` when flag enabled
- Fall back to `_resolve_call()` when flag disabled

### Exit
- Map `ResolutionResult.callee` → `CallEntry.callee`
- Map `ResolutionResult.resolution_type` → `CallEntry.resolution`
- Map `ResolutionResult.heuristic` → `CallEntry.resolution_source` (if H2.9 enabled)

## 8. Flag Contract

| Flag | Type | Default | Purpose |
|------|------|---------|---------|
| `--enable-v050-resolution-engine` | bool | false | Switch between legacy and engine |
| `--v050-dual-run-compare` | bool | false | Run both, output diff |
| `--v050-emit-resolution-trace` | bool | false | Include trace in output |

## 9. Parity Criteria

**Exact Parity** means:
- Same edge count
- Same (from, to, kind) tuples
- Same resolution types
- Same resolution_source values (if H2.9 enabled)

**Acceptable Diff Categories**:
- Metadata-only (trace, confidence)
- Documented alias mappings

**Unacceptable**:
- Missing edges
- Extra edges
- Different resolution targets

## 10. Known Gaps

1. **FactoryReturnResolver (H2.8)** - NOT in `resolvers/heuristics.py`
   - Exists in `python_calls.py:479-540` but not as resolver class
   - Needs: Implement `FactoryReturnResolver` class

2. **CallContext.factory_return_types** - Field missing
   - Needs: Add to CallContext dataclass

3. **No dual-run mode** - Needs implementation
   - Will be separate script: `sprint-v050-engine/08-commands/compare_results.py`

## 11. Testing Strategy

### Phase 1: Dual-Run Comparison
```bash
./run-dual.sh  # runs both modes
python3 compare_results.py legacy/ engine/
```

### Phase 2: Mini-Fixture
- Small Python file with all heuristics
- Must pass 100% parity

### Phase 3: Smoke + Golden
- Self-repo extraction
- httpie benchmark

## 12. Rollback Plan

If parity fails:
1. Keep `--enable-v050-resolution-engine false` as default
2. Document delta in release notes
3. Fix in next sprint, not this one

**No scope reduction allowed.**
