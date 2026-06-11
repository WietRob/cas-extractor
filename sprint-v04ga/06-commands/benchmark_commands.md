# CAS Extractor v0.4 GA — Benchmark Commands

**Purpose:** Generate reproducible benchmark metrics for v0.3b / v0.3c / v0.4-ga comparison.

---

## Benchmark Script (All-in-One)

```bash
#!/bin/bash
# benchmark_all.sh — Generate complete benchmark matrix

PROJECT_ROOT="/home/roberto_schmidt/projects/Deterministic Knowledge System"
OUTPUT_DIR="$PROJECT_ROOT/sprint-v04ga/03-golden/metrics"

mkdir -p "$OUTPUT_DIR"

echo "=== CAS Extractor v0.4 GA Benchmark ===" > "$OUTPUT_DIR/benchmark_run.log"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUTPUT_DIR/benchmark_run.log"
echo "" >> "$OUTPUT_DIR/benchmark_run.log"

# Function to extract metrics from evidence directory
extract_metrics() {
    local EVID_DIR=$1
    local LABEL=$2
    
    echo "=== $LABEL ===" >> "$OUTPUT_DIR/benchmark_run.log"
    
    # Total edges
    TOTAL=$(grep -h "to:" "$EVID_DIR"/*.yaml 2>/dev/null | wc -l)
    echo "Total edges: $TOTAL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    # method_call
    METHOD_CALL=$(grep -h "kind: method_call" "$EVID_DIR"/*.yaml 2>/dev/null | wc -l)
    echo "method_call: $METHOD_CALL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    # super_call
    SUPER_CALL=$(grep -h "kind: super_call" "$EVID_DIR"/*.yaml 2>/dev/null | wc -l)
    echo "super_call: $SUPER_CALL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    # call
    CALL=$(grep -h "kind: call" "$EVID_DIR"/*.yaml 2>/dev/null | wc -l)
    echo "call: $CALL" >> "$OUTPUT_DIR/benchmark_run.log"
    
    # Unresolved total
    UNRESOLVED=$(grep -h "to: '?\." "$EVID_DIR"/*.yaml 2>/dev/null | wc -l)
    echo "Unresolved (?.*): $UNRESOLVED" >> "$OUTPUT_DIR/benchmark_run.log"
    
    # H2 unresolved (3-part)
    H2_UNRESOLVED=$(grep -h "to: '?.self\." "$EVID_DIR"/*.yaml 2>/dev/null | wc -l)
    echo "H2 unresolved (?.self.<attr>.<method>): $H2_UNRESOLVED" >> "$OUTPUT_DIR/benchmark_run.log"
    
    echo "" >> "$OUTPUT_DIR/benchmark_run.log"
}

# v0.3b baseline
extract_metrics "$PROJECT_ROOT/golden-v03b/evidence" "v0.3b Baseline"

# v0.3c coverage mode (TRUE)
extract_metrics "$PROJECT_ROOT/golden-v03c/evidence" "v0.3c Coverage (TRUE)"

# v0.4-rc comparability mode (FALSE)
extract_metrics "$PROJECT_ROOT/golden-v04rc/evidence" "v0.4-rc Comparability (FALSE)"

echo "Benchmark complete. See $OUTPUT_DIR/benchmark_run.log"
cat "$OUTPUT_DIR/benchmark_run.log"
```

---

## Individual Metric Commands

### v0.3b Baseline

```bash
EVID_DIR="/home/roberto_schmidt/projects/Deterministic Knowledge System/golden-v03b/evidence"

# Total edges
echo "v0.3b Total edges: $(grep -h 'to:' $EVID_DIR/*.yaml | wc -l)"

# method_call
echo "v0.3b method_call: $(grep -h 'kind: method_call' $EVID_DIR/*.yaml | wc -l)"

# super_call
echo "v0.3b super_call: $(grep -h 'kind: super_call' $EVID_DIR/*.yaml | wc -l)"

# call
echo "v0.3b call: $(grep -h 'kind: call' $EVID_DIR/*.yaml | wc -l)"

# Unresolved
echo "v0.3b Unresolved: $(grep -h "to: '?\." $EVID_DIR/*.yaml | wc -l)"
```

### v0.3c Coverage Mode (TRUE)

```bash
EVID_DIR="/home/roberto_schmidt/projects/Deterministic Knowledge System/golden-v03c/evidence"

# Total edges
echo "v0.3c Total edges: $(grep -h 'to:' $EVID_DIR/*.yaml | wc -l)"

# method_call
echo "v0.3c method_call: $(grep -h 'kind: method_call' $EVID_DIR/*.yaml | wc -l)"

# super_call
echo "v0.3c super_call: $(grep -h 'kind: super_call' $EVID_DIR/*.yaml | wc -l)"

# call
echo "v0.3c call: $(grep -h 'kind: call' $EVID_DIR/*.yaml | wc -l)"

# Unresolved
echo "v0.3c Unresolved: $(grep -h "to: '?\." $EVID_DIR/*.yaml | wc -l)"

# H2 unresolved
echo "v0.3c H2 unresolved: $(grep -h "to: '?.self\." $EVID_DIR/*.yaml | wc -l)"
```

### v0.4-rc Comparability Mode (FALSE)

```bash
EVID_DIR="/home/roberto_schmidt/projects/Deterministic Knowledge System/golden-v04rc/evidence"

# Total edges
echo "v0.4-rc Total edges: $(grep -h 'to:' $EVID_DIR/*.yaml | wc -l)"

# method_call
echo "v0.4-rc method_call: $(grep -h 'kind: method_call' $EVID_DIR/*.yaml | wc -l)"

# super_call
echo "v0.4-rc super_call: $(grep -h 'kind: super_call' $EVID_DIR/*.yaml | wc -l)"

# call
echo "v0.4-rc call: $(grep -h 'kind: call' $EVID_DIR/*.yaml | wc -l)"

# Unresolved
echo "v0.4-rc Unresolved: $(grep -h "to: '?\." $EVID_DIR/*.yaml | wc -l)"

# H2 unresolved (should be 0)
echo "v0.4-rc H2 unresolved: $(grep -h "to: '?.self\." $EVID_DIR/*.yaml | wc -l)"
```

---

## Expected Results

| Metric | v0.3b | v0.3c (TRUE) | v0.4-rc (FALSE) |
|--------|-------|--------------|-----------------|
| Total edges | 2810 | 2899 | 2814 |
| method_call | 204 | 208 | 208 |
| super_call | 8 | 8 | 8 |
| call | 2598 | 2683 | 2598 |
| Unresolved | 860 | 945 | 860 |
| H2 unresolved | N/A | 85 | 0 |

---

## Delta Analysis Commands

### v0.3b → v0.3c Delta

```bash
echo "Delta v0.3b → v0.3c:"
echo "  Total edges: 2899 - 2810 = +89"
echo "  method_call: 208 - 204 = +4"
echo "  Unresolved: 945 - 860 = +85"
echo "  H2 unresolved: 85 (new in v0.3c)"
```

### v0.3c → v0.4-rc Delta

```bash
echo "Delta v0.3c → v0.4-rc:"
echo "  Total edges: 2814 - 2899 = -85"
echo "  method_call: 208 - 208 = 0"
echo "  Unresolved: 860 - 945 = -85"
echo "  H2 unresolved: 0 - 85 = -85 (skipped in FALSE mode)"
```

### v0.3b → v0.4-rc Delta

```bash
echo "Delta v0.3b → v0.4-rc:"
echo "  Total edges: 2814 - 2810 = +4"
echo "  method_call: 208 - 204 = +4 (H2 quality gain preserved)"
echo "  Unresolved: 860 - 860 = 0 (comparability restored)"
echo "  H2 unresolved: 0 (not applicable)"
```

---

**Generated:** 2026-02-22T09:27:14Z
