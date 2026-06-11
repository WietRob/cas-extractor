# CAS Extractor v0.4 GA — Reproducible Commands

**All commands are copy/paste-ready.**

---

## Prerequisites

```bash
# Working directory
cd "/home/roberto_schmidt/projects/Deterministic Knowledge System"

# Verify Python version
python3 --version  # Expected: Python 3.12.3
```

---

## A) CLI Flag Verification

### A.1 Check Help Text

```bash
python3 extract_python.py --help
```

**Expected:** `--emit-unresolved-self-attr` visible with help text, default=true

### A.2 Test TRUE Mode (Coverage)

```bash
python3 extract_python.py \
  --repo-root /tmp/h2-verify \
  --repo-name repo://test \
  --revision git:test \
  --emit-unresolved-self-attr true \
  --out /tmp/h2-test-true
```

**Expected:** Extraction completes, H2 unresolved edges present

### A.3 Test FALSE Mode (Comparability)

```bash
python3 extract_python.py \
  --repo-root /tmp/h2-verify \
  --repo-name repo://test \
  --revision git:test \
  --emit-unresolved-self-attr false \
  --out /tmp/h2-test-false
```

**Expected:** Extraction completes, H2 unresolved edges skipped

### A.4 Test ENV Variable

```bash
CAS_EMIT_UNRESOLVED_SELF_ATTR=false python3 extract_python.py \
  --repo-root /tmp/h2-verify \
  --repo-name repo://test \
  --revision git:test \
  --out /tmp/h2-test-env
```

**Expected:** Same behavior as A.3

---

## B) Mini-Fixture Tests

### B.1 Create Mini-Fixture

```bash
mkdir -p /tmp/h2-verify

cat > /tmp/h2-verify/test_h2.py << 'EOF'
# Positive H2: self.attr = Class() in __init__, then self.attr.method()
class HTTPClient:
    def send(self): pass
    def close(self): pass

class DownloadStatus:
    def started(self): pass
    def finished(self): pass

class Downloader:
    def __init__(self):
        self.status = DownloadStatus()  # H2 anchor
    
    def start(self):
        self.status.started()  # Positive H2: resolved
    
    def finish(self):
        self.status.finished()  # Positive H2: resolved

# Negative H2: attr not in __init__
class Handler:
    def setup(self):
        self.client = HTTPClient()  # Not in __init__
    
    def run(self):
        self.client.send()  # Negative H2: unresolved

# Negative H2: unknown class
class UnknownRunner:
    def __init__(self):
        self.handler = SomeUnknownClass()  # Unknown class
    
    def run(self):
        self.handler.process()  # Negative H2: unresolved

# Negative H2: no __init__
class NoInitClass:
    def run(self):
        self.session.load()  # Negative H2: no __init__
EOF
```

### B.2 Extract TRUE Mode

```bash
python3 extract_python.py \
  --repo-root /tmp/h2-verify \
  --repo-name repo://test \
  --revision git:test \
  --emit-unresolved-self-attr true \
  --out "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/true" \
  2>&1 | tee "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/true/run.log"
```

### B.3 Extract FALSE Mode

```bash
python3 extract_python.py \
  --repo-root /tmp/h2-verify \
  --repo-name repo://test \
  --revision git:test \
  --emit-unresolved-self-attr false \
  --out "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/false" \
  2>&1 | tee "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/false/run.log"
```

---

## C) Golden Benchmark Extraction

### C.1 v0.3b Baseline (Reference Only)

```bash
# Reference: golden-v03b/
# No re-extraction needed - use existing
```

### C.2 v0.3c Coverage Mode (Reference Only)

```bash
# Reference: golden-v03c/
# No re-extraction needed - use existing
```

### C.3 v0.4 GA Comparability Mode (FALSE)

```bash
# NOTE: Requires httpie/cli repository at /path/to/httpie
# Adjust --repo-root path as needed

python3 extract_python.py \
  --repo-root /path/to/httpie \
  --repo-name repo://httpie \
  --revision git:HEAD \
  --emit-unresolved-self-attr false \
  --out "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/03-golden/v04ga-comparability" \
  2>&1 | tee "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/03-golden/v04ga-comparability/run.log"
```

---

## D) Metrics Extraction

### D.1 Count Total Edges

```bash
grep -c "to:" /path/to/evidence/EVID-py.callgraph-*.yaml | awk -F: '{sum+=$2} END {print "Total edges:", sum}'
```

### D.2 Count method_call Edges

```bash
grep "kind: method_call" /path/to/evidence/EVID-py.callgraph-*.yaml | wc -l
```

### D.3 Count call Edges

```bash
grep "kind: call" /path/to/evidence/EVID-py.callgraph-*.yaml | wc -l
```

### D.4 Count Unresolved Edges

```bash
grep "to: '?\\." /path/to/evidence/EVID-py.callgraph-*.yaml | wc -l
```

### D.5 Count H2 Unresolved (3-part pattern)

```bash
grep "to: '?.self\\." /path/to/evidence/EVID-py.callgraph-*.yaml | wc -l
```

---

## E) Validation

### E.1 Structural Validation

```bash
python3 validate.py \
  --evidence "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/03-golden/v04ga-comparability/evidence" \
  --schemas ./schemas \
  2>&1 | tee "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/03-golden/validation/validation-v04ga.txt"
```

### E.2 Semantic Validation (if applicable)

```bash
python3 validate.py \
  --evidence "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/03-golden/v04ga-comparability/evidence" \
  --schemas ./schemas \
  --rules ./rules/validator_rules.v0.1.yaml \
  2>&1 | tee -a "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/03-golden/validation/validation-v04ga.txt"
```

---

## F) Comparison Commands

### F.1 Compare TRUE vs FALSE Mini-Fixture

```bash
diff -r \
  "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/true/evidence" \
  "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/false/evidence" \
  > "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/comparisons/true-vs-false.diff" 2>&1
```

### F.2 Extract Edge Counts

```bash
echo "TRUE mode edges:"
grep -c "to:" "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/true/evidence"/EVID-py.callgraph-*.yaml | awk -F: '{sum+=$2} END {print sum}'

echo "FALSE mode edges:"
grep -c "to:" "/home/roberto_schmidt/projects/Deterministic Knowledge System/sprint-v04ga/01-mini-fixture/false/evidence"/EVID-py.callgraph-*.yaml | awk -F: '{sum+=$2} END {print sum}'
```

---

## G) Spot Check Commands

### G.1 Check Specific Edge Present

```bash
grep "to: 'DownloadStatus.started'" /path/to/evidence/EVID-py.callgraph-*.yaml
```

### G.2 Check H2 Unresolved Present (TRUE mode)

```bash
grep "to: '?.self\\." /path/to/evidence/EVID-py.callgraph-*.yaml
```

### G.3 Check H2 Unresolved Absent (FALSE mode)

```bash
grep "to: '?.self\\." /path/to/evidence/EVID-py.callgraph-*.yaml && echo "FAIL: H2 unresolved found" || echo "PASS: No H2 unresolved"
```

---

**Generated:** 2026-02-22T09:27:14Z
