# CAS Extractor v0.4.1 H2.5 — Benchmark Commands

**Purpose:** Generate reproducible benchmark metrics for v0.4.0 / v0.4.1-H2.5-OFF / v0.4.1-H2.5-ON comparison.

---

## Quick Benchmark Script

```bash
#!/bin/bash
# benchmark_h25.sh — Generate complete H2.5 benchmark

PROJECT_ROOT="/home/roberto_schmidt/projects/Deterministic Knowledge System"
OUTPUT_DIR="$PROJECT_ROOT/sprint-v041-h25/06-golden"

mkdir -p "$OUTPUT_DIR"

echo "=== CAS Extractor v0.4.1 H2.5 Benchmark ===" > "$OUTPUT_DIR/benchmark_run.log"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUTPUT_DIR/benchmark_run.log"
echo "" >> "$OUTPUT_DIR/benchmark_run.log"

# Function to extract metrics
extract_metrics() {
    local DIR=$1
    local LABEL=$2
    
    echo "=== $LABEL ===" >> "$OUTPUT_DIR/benchmark_run.log"
    
    TOTAL=$(grep -h "to:" "$DIR"/*.yaml 2>/dev/null | wc -l)
    echo "Total edges: $TOTAL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    METHOD_CALL=$(grep -h "kind: method_call" "$DIR"/*.yaml 2>/dev/null | wc -l)
    echo "method_call: $METHOD_CALL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    SUPER_CALL=$(grep -h "kind: super_call" "$DIR"/*.yaml 2>/dev/null | wc -l)
    echo "super_call: $SUPER_CALL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    CALL=$(grep -h "kind: call" "$DIR"/*.yaml 2>/dev/null | wc -l)
    echo "call: $CALL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    UNRESOLVED=$(grep -h "to: '?\." "$DIR"/*.yaml 2>/dev/null | wc -l)
    echo "Unresolved: $UNRESOLVED" >> "$OUTPUT_DIR/benchmark_run.log"
    
    H2_3PART=$(grep -h "to: '?.self\." "$DIR"/*.yaml 2>/dev/null | grep -v "\.[^.]*$" | wc -l)
    echo "H2 3-part unresolved: $H2_3PART" >> "$OUTPUT_DIR/benchmark_run.log"
    
    echo "" >> "$OUTPUT_DIR/benchmark_run.log"
}

# v0.4.0 reference (from existing golden)
extract_metrics "$PROJECT_ROOT/golden-v04rc/evidence" "v0.4.0 Reference (FALSE)"

# v0.4.1 H2.5 OFF (if extracted)
if [ -d "$OUTPUT_DIR/v041-h25-off" ]; then
    extract_metrics "$OUTPUT_DIR/v041-h25-off" "v0.4.1 H2.5 OFF"
fi

# v0.4.1 H2.5 ON (if extracted)
if [ -d "$OUTPUT_DIR/v041-h25-on" ]; then
    extract_metrics "$OUTPUT_DIR/v041-h25-on" "v0.4.1 H2.5 ON"
fi

echo "Benchmark complete. See $OUTPUT_DIR/benchmark_run.log"
cat "$OUTPUT_DIR/benchmark_run.log"
```

---

## Individual Metric Commands

### v0.4.0 Reference (FALSE mode)

```bash
EVID_DIR="golden-v04rc/evidence"

echo "v0.4.0 Total edges: $(grep -h 'to:' $EVID_DIR/EVID-py.callgraph-*.yaml | wc -l)"
echo "v0.4.0 method_call: $(grep -h 'kind: method_call' $EVID_DIR/EVID-py.callgraph-*.yaml | wc -l)"
echo "v0.4.0 super_call: $(grep -h 'kind: super_call' $EVID_DIR/EVID-py.callgraph-*.yaml | wc -l)"
echo "v0.4.0 call: $(grep -h 'kind: call' $EVID_DIR/EVID-py.callgraph-*.yaml | wc -l)"
echo "v0.4.0 Unresolved: $(grep -h "to: '?\." $EVID_DIR/EVID-py.callgraph-*.yaml | wc -l)"
```

### v0.4.1 H2.5 OFF

```bash
EVID_DIR="sprint-v041-h25/06-golden/v041-h25-off"

echo "v0.4.1 OFF Total edges: $(grep -h 'to:' $EVID_DIR/EVID-py.callgraph-*.yaml 2>/dev/null | wc -l)"
echo "v0.4.1 OFF method_call: $(grep -h 'kind: method_call' $EVID_DIR/EVID-py.callgraph-*.yaml 2>/dev/null | wc -l)"
echo "v0.4.1 OFF Unresolved: $(grep -h "to: '?\." $EVID_DIR/EVID-py.callgraph-*.yaml 2>/dev/null | wc -l)"
```

### v0.4.1 H2.5 ON

```bash
EVID_DIR="sprint-v041-h25/06-golden/v041-h25-on"

echo "v0.4.1 ON Total edges: $(grep -h 'to:' $EVID_DIR/EVID-py.callgraph-*.yaml 2>/dev/null | wc -l)"
echo "v0.4.1 ON method_call: $(grep -h 'kind: method_call' $EVID_DIR/EVID-py.callgraph-*.yaml 2>/dev/null | wc -l)"
echo "v0.4.1 ON Unresolved: $(grep -h "to: '?\." $EVID_DIR/EVID-py.callgraph-*.yaml 2>/dev/null | wc -l)"
```

---

## Expected Results (Hypothesis)

| Metric | v0.4.0 | v0.4.1 OFF | v0.4.1 ON | Delta |
|--------|--------|------------|-----------|-------|
| Total edges | 2814 | 2814 | TBD | +? |
| method_call | 208 | 208 | TBD | +? |
| Unresolved | 919 | 919 | TBD | -? |

**H2.5 Effect:** Expect `method_call` to increase by the number of H2.5-resolvable patterns in the target repo.

---

## H2.5 Pattern Count in Golden

To estimate H2.5 impact before implementation:

```bash
# Find potential H2.5 patterns in golden repo
# (self.attr = ClassName() outside __init__)

# This is a heuristic search, not exact
grep -r "self\.[a-z_]* = [A-Z]" /path/to/httpie --include="*.py" | grep -v "__init__" | head -20
```

---

**Generated:** 2026-02-22T10:47:00Z
