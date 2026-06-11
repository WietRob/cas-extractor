# v0.5.0 Specification — Unified Resolution Engine

**Sprint:** v0.5.0
**Goal:** Refactor H1-H2.8 heuristics into unified ResolutionEngine with explainability
**Status:** Draft Specification

---

## Problem Statement

Current `python_calls.py` has a monolithic `_resolve_call()` function with:
- 900+ lines of nested conditionals
- Heuristics hardcoded in resolution order
- No explainability - can't tell WHICH heuristic resolved a call
- Difficult to add new heuristics or modify priority
- No testability - hard to test individual heuristics

---

## Solution: ResolutionEngine Architecture

### Core Components

```python
class ResolutionEngine:
    """Unified resolution engine with pluggable heuristics."""
    
    def __init__(self, config: ResolutionConfig):
        self.resolvers: list[BaseResolver] = []
        self._register_default_resolvers()
    
    def resolve(self, call_context: CallContext) -> ResolutionResult:
        """Try each resolver in priority order until one succeeds."""
        for resolver in self.resolvers:
            result = resolver.try_resolve(call_context)
            if result:
                result.heuristic = resolver.name
                return result
        return ResolutionResult(unresolved=True)


class BaseResolver:
    """Base class for all heuristic resolvers."""
    
    name: str           # e.g., "H2.5", "H1"
    priority: int       # lower = higher priority
    enabled: bool       # controlled by feature flags
    
    def try_resolve(self, context: CallContext) -> ResolutionResult | None:
        """Attempt to resolve the call. Return None if not applicable."""


class CallContext:
    """Immutable context for a single call resolution."""
    
    func_node: ast.expr
    enclosing_func: str
    enclosing_class: ClassInfo | None
    local_var_types: dict[str, str]
    self_attr_types: dict[str, str]
    # ... all the type information built during analysis


class ResolutionResult:
    """Result of a resolution attempt."""
    
    callee: str                    # qualified name or "?.xxx"
    resolution_type: str            # "self_attr_dispatch", "local_var_dispatch", etc.
    heuristic: str                 # "H1", "H2.5", "H2.6", etc.
    trace: list[ResolutionStep]    # explainability trace
    confidence: float             # 0.0-1.0


class ResolutionStep:
    """Single step in resolution explainability trace."""
    
    heuristic: str
    pattern_matched: str
    inferred_type: str | None
    reasoning: str
```

---

## Resolver Registry

### Priority Order (lower = higher priority)

| Priority | Resolver | Heuristic | Flag |
|----------|----------|-----------|------|
| 10 | LocalVarResolver | H1 | Always |
| 20 | MethodLocalSelfAttrResolver | H2.5 | enable_h25_self_attr_noninit |
| 30 | TransitiveSelfAttrResolver | H2.7 | enable_h27_self_attr_transitive |
| 40 | InterMethodSelfAttrResolver | H2.6 | enable_h26_self_attr_intermethod |
| 50 | FactoryReturnResolver | H2.8 | enable_h28_factory_return |
| 60 | ClassInitSelfAttrResolver | H2 | Always |
| 70 | ConstructorResolver | H3 | Always |
| 80 | SelfDispatchResolver | self.method() | Always |
| 90 | ClsDispatchResolver | cls.method() | Always |
| 100 | SuperDispatchResolver | super().method() | Always |

---

## Explainability Feature

### Resolution Trace

Each resolved call includes a trace:

```python
{
    "caller": "module.Class.run",
    "callee": "module.HTTPClient.send",
    "resolution_type": "self_attr_dispatch",
    "heuristic": "H2.5",
    "trace": [
        {
            "heuristic": "H2.5",
            "pattern": "self.attr = Class() in same method",
            "inferred_type": "module.HTTPClient",
            "reasoning": "Found assignment 'self.client = HTTPClient()' in method 'run'"
        }
    ]
}
```

### Debug Mode

```bash
# Enable resolution trace in output
python3 extract_python.py --enable-resolution-trace true --out ./artifacts

# Output includes: EVID-py-callgraph-*.yaml + EVID-py-resolution-trace-*.json
```

---

## Migration Path

### Phase 1: Extract Resolvers (Non-Breaking)

1. Create `resolvers/` module with individual resolver classes
2. Each resolver extracts from current logic
3. Keep `_resolve_call()` as delegator to maintain behavior

### Phase 2: Add Engine (Non-Breaking)

1. Create `ResolutionEngine` class
2. Add parallel resolution with trace collection
3. Feature flag to switch between old/new

### Phase 3: Enable by Default (Breaking Change)

1. Flip default to use new engine
2. Add `--resolution-trace` flag
3. Update resolution_type names if needed

---

## CLI Changes

### New Flags

```bash
# Enable resolution trace output
--enable-resolution-trace true|false

# Resolution engine mode (legacy | engine)
--resolution-mode engine|legacy

# Print resolution decisions to stdout (debug)
--debug-resolver
```

---

## Test Strategy

### Unit Tests per Resolver

```python
def test_h25_resolver_simple():
    context = CallContext(...)
    resolver = MethodLocalSelfAttrResolver()
    
    result = resolver.try_resolve(context)
    assert result.callee == "module.HTTPClient.send"
    assert result.heuristic == "H2.5"

def test_h25_no_match_different_method():
    # H2.5 should NOT match when attr assigned in different method
    context = CallContext(...)
    resolver = MethodLocalSelfAttrResolver()
    
    result = resolver.try_resolve(context)
    assert result is None  # Pass through to next resolver
```

### Integration Tests

- Golden test (httpie) - must match v0.4.4 behavior
- Smoke test - must have 0 regressions

---

## Backward Compatibility

- Default resolution_type strings preserved
- Feature flags work exactly as before
- Output format unchanged (unless --enable-resolution-trace)

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Golden test match | 100% (v0.4.4 behavior) |
| Smoke test | 0 regressions |
| New heuristic addition | < 30 min (vs hours currently) |
| Resolution explainability | Every resolved call has trace |

---

## Open Questions

1. Should we merge H2.6 and H2.7 into single "SelfAttrResolver"?
2. How to handle conflicting resolvers (same attr, different types)?
3. Should resolution trace be in separate file or embedded?

---

**Status:** Ready for implementation design review
