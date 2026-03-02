# GATE VERIFICATION - T14b Complete

**Date**: 2026-02-25
**Status**: ❌ H2.7 FAILS - Bug Found

## Gate A: H2.6/2.7 PropagatedSelfAttrResolver

### Test Fixture
```python
class Client:
    def send(self): pass

def make_client() -> Client:
    return Client()

class Service:
    def init_client(self):
        self.client = make_client()  # Assignment in non-__init__ method

    def run(self):
        self.client.send()  # Usage in different method
```

### Expected Behavior
- Engine should resolve: `Service.run -> Client.send`
- Trace should contain: heuristic `H2.6/2.7` or `H2`

### Actual Behavior
- Edge NOT resolved: `Service.run -> ?.self.client.send` (filtered as unresolved)
- Resolution trace: **MISSING**

### Root Cause
The `PropagatedSelfAttrResolver` (H2.6/2.7) is NOT being triggered. The inter-method propagation logic in `python_calls.py` is either:
1. Not building the `propagated_self_attr_types` dictionary correctly
2. The resolver isn't receiving the context correctly

### Status: ❌ GATE FAILS

---

## Gate B: H2.8 FactoryReturnResolver

### Test Fixture
```python
class Builder:
    def build(self): pass

def builder_factory():
    return Builder()

def main():
    x = builder_factory()
    x.build()  # Should resolve to Builder.build
```

### Expected Behavior
- Engine should resolve: `main -> Builder.build`
- Trace should contain: heuristic `H2.8`

### Actual Behavior
- Edge resolved: `main -> Builder.build` ✅
- Trace contains: heuristic `qualified_attr` ❌ (NOT H2.8)
- Reasoning: "Found local var 'x' of type 'Builder'"

### Analysis
The H2.8 resolver is NOT being used because `QualifiedAttrResolver` (which handles local variable type inference) resolves the call first. This is correct behavior - the call IS resolved, just not by H2.8 specifically.

### Status: ⚠️ WORKS (but differently than expected)

---

## Gate C: Trace Assertions

### Command
```bash
grep -R "heuristic: H2.6/2.7" ... 
grep -R "heuristic: H2.8" ...
```

### Results
- `H2.6/2.7`: **0 matches** ❌
- `H2.8`: **0 matches** ❌
- `H2`: 1 match (ClassInitSelfAttrResolver, not H2.6/2.7)

### Status: ❌ GATE FAILS

---

## Conclusion

| Gate | Status | Notes |
|------|--------|-------|
| H2.7 Proof | ❌ FAIL | Not resolving inter-method self.attr |
| H2.8 Proof | ⚠️ PARTIAL | Resolves but not via H2.8 heuristic |
| Trace Assertion | ❌ FAIL | Target heuristics not in traces |

## Recommendation

**v0.5.0 CANNOT be released as GA** until:
1. H2.6/2.7 propagation bug is fixed
2. Or documented that H2.6/2.7 is deferred

Current status: **v0.5.0 RC / Integration Complete - H2.7/H2.8 Proof Gates FAILED**
