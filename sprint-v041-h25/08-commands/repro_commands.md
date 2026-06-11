# CAS Extractor v0.4.1 H2.5 — Reproducible Commands

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

## A) H2.5 Flag Verification

### A.1 Check Help Text (after implementation)

```bash
python3 extract_python.py --help
```

**Expected:** `--enable-h25-self-attr-noninit` visible with help text, default=false

### A.2 Test H2.5 OFF (default)

```bash
python3 extract_python.py \
  --repo-root /tmp/h25-verify \
  --repo-name repo://test \
  --revision git:test \
  --out /tmp/h25-test-off
```

**Expected:** H2.5 patterns stay unresolved

### A.3 Test H2.5 ON

```bash
python3 extract_python.py \
  --repo-root /tmp/h25-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h25-self-attr-noninit true \
  --out /tmp/h25-test-on
```

**Expected:** H2.5 patterns resolved to method_call

### A.4 Test ENV Variable

```bash
CAS_ENABLE_H25_SELF_ATTR_NONINIT=true python3 extract_python.py \
  --repo-root /tmp/h25-verify \
  --repo-name repo://test \
  --revision git:test \
  --out /tmp/h25-test-env
```

**Expected:** Same behavior as A.3

---

## B) Mini-Fixture Tests

### B.1 Create H2.5 Mini-Fixture

```bash
mkdir -p /tmp/h25-verify

cat > /tmp/h25-verify/test_h25.py << 'EOF'
# === H2.5 POSITIVE CASES (intra-method resolution) ===

class HTTPClient:
    def send(self): pass
    def close(self): pass

class WebSocketClient:
    def send(self): pass
    def connect(self): pass

class DownloadStatus:
    def started(self): pass
    def finished(self): pass

# P1: Basic non-__init__ assignment + call in same method
class TestH25Basic:
    def setup(self):
        self.client = HTTPClient()  # H2.5 anchor
        self.client.send()          # H2.5 resolved: HTTPClient.send
    
    def run(self):
        self.client.send()          # Cross-method - unresolved

# P2: Multiple attrs in same method
class TestH25Multiple:
    def configure(self):
        self.client = HTTPClient()       # H2.5 anchor 1
        self.status = DownloadStatus()   # H2.5 anchor 2
        self.client.send()               # H2.5: HTTPClient.send
        self.status.started()            # H2.5: DownloadStatus.started

# P3: Reassignment (last wins) in same method
class TestH25Reassign:
    def reconnect(self):
        self.client = HTTPClient()       # First assignment
        self.client = WebSocketClient()  # Reassignment: wins
        self.client.send()               # H2.5: WebSocketClient.send

# P4: AnnAssign in same method
class TestH25AnnAssign:
    def initialize(self):
        self.client: HTTPClient = HTTPClient()  # H2.5 anchor with annotation
        self.client.send()                      # H2.5: HTTPClient.send

# P5: H2.5 override H2 (reassign in method)
class TestH25OverrideH2:
    def __init__(self):
        self.client = HTTPClient()  # H2 anchor
    
    def reconnect(self):
        self.client = WebSocketClient()  # H2.5 override
        self.client.send()               # H2.5: WebSocketClient.send
    
    def run(self):
        self.client.send()               # H2: HTTPClient.send (no H2.5 in run)

# === H2.5 NEGATIVE CASES (unresolved/skip) ===

# N1: Assignment in method A, call in method B (cross-method)
class TestH25CrossMethod:
    def setup(self):
        self.client = HTTPClient()  # Assignment in setup
    
    def run(self):
        self.client.send()          # Call in run - cross-method, unresolved

# N2: Factory assignment
class TestH25Factory:
    def initialize(self):
        self.client = self._create()  # Factory - can't infer
        self.client.send()            # Unresolved
    
    def _create(self):
        return HTTPClient()

# N3: Unknown class
class TestH25Unknown:
    def setup(self):
        self.handler = SomeUnknownClass()  # Unknown class
        self.handler.process()             # Unresolved

# N4: No assignment before use (same method)
class TestH25NoAssign:
    def run(self):
        self.client.send()  # No prior assignment - unresolved

# N5: Conditional assignment only
class TestH25Conditional:
    def setup(self, use_websocket):
        if use_websocket:
            self.client = WebSocketClient()  # Conditional - not always assigned
        self.client.send()  # May not be assigned - unresolved (conservative)
EOF
echo "H2.5 mini-fixture created at /tmp/h25-verify/test_h25.py"
```

### B.2 Extract H2.5 OFF

```bash
python3 extract_python.py \
  --repo-root /tmp/h25-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h25-self-attr-noninit false \
  --emit-unresolved-self-attr true \
  --out "sprint-v041-h25/04-mini-fixture/off" \
  2>&1 | tee "sprint-v041-h25/04-mini-fixture/results_off.md"
```

### B.3 Extract H2.5 ON

```bash
python3 extract_python.py \
  --repo-root /tmp/h25-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h25-self-attr-noninit true \
  --emit-unresolved-self-attr true \
  --out "sprint-v041-h25/04-mini-fixture/on" \
  2>&1 | tee "sprint-v041-h25/04-mini-fixture/results_on.md"
```

---

## C) Smoke Tests

### C.1 Smoke H2.5 OFF

```bash
python3 extract_python.py \
  --repo-root cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:test \
  --enable-h25-self-attr-noninit false \
  --out sprint-v041-h25/05-smoke/off \
  2>&1 | tee sprint-v041-h25/05-smoke/smoke_off.md
```

### C.2 Smoke H2.5 ON

```bash
python3 extract_python.py \
  --repo-root cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:test \
  --enable-h25-self-attr-noninit true \
  --out sprint-v041-h25/05-smoke/on \
  2>&1 | tee sprint-v041-h25/05-smoke/smoke_on.md
```

---

## D) Golden Benchmark

### D.1 v0.4.0 Reference (existing)

```bash
# Use existing golden-v04rc/ for baseline
# Metrics already captured in sprint-v041-h25/00-meta/BASELINE_PROVENANCE.md
```

### D.2 v0.4.1 H2.5 OFF (should match v0.4.0)

```bash
# NOTE: Requires httpie/cli repository
python3 extract_python.py \
  --repo-root /path/to/httpie \
  --repo-name repo://httpie \
  --revision git:HEAD \
  --emit-unresolved-self-attr false \
  --enable-h25-self-attr-noninit false \
  --out sprint-v041-h25/06-golden/v041-h25-off \
  2>&1 | tee sprint-v041-h25/06-golden/v041_h25_off_extraction.log
```

### D.3 v0.4.1 H2.5 ON

```bash
python3 extract_python.py \
  --repo-root /path/to/httpie \
  --repo-name repo://httpie \
  --revision git:HEAD \
  --emit-unresolved-self-attr false \
  --enable-h25-self-attr-noninit true \
  --out sprint-v041-h25/06-golden/v041-h25-on \
  2>&1 | tee sprint-v041-h25/06-golden/v041_h25_on_extraction.log
```

---

## E) Metrics Commands

### E.1 Count Total Edges

```bash
grep -h "to:" sprint-v041-h25/06-golden/*/EVID-py.callgraph-*.yaml | wc -l
```

### E.2 Count method_call Edges

```bash
grep "kind: method_call" sprint-v041-h25/06-golden/*/EVID-py.callgraph-*.yaml | wc -l
```

### E.3 Count H2.5 Resolved (new resolution type)

```bash
# After implementation, grep for self_attr_dispatch or new H2.5 marker
grep "self_attr_dispatch" sprint-v041-h25/06-golden/*/EVID-py.callgraph-*.yaml | wc -l
```

---

## F) Comparison Commands

### F.1 Compare OFF vs ON

```bash
echo "=== H2.5 OFF edges ==="
grep -h "to:" sprint-v041-h25/04-mini-fixture/off/EVID-py.callgraph-*.yaml | wc -l

echo "=== H2.5 ON edges ==="
grep -h "to:" sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-*.yaml | wc -l

echo "=== Delta ==="
# Calculate difference
```

### F.2 Check Positive H2.5 Cases

```bash
# P1: HTTPClient.send in setup method
grep "to: test_h25.HTTPClient.send" sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-*.yaml

# P3: WebSocketClient.send (reassign wins)
grep "to: test_h25.WebSocketClient.send" sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-*.yaml
```

### F.3 Check Negative H2.5 Cases

```bash
# N1: Cross-method should be unresolved
grep "to: '?.self.client.send'" sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-*.yaml
```

---

**Generated:** 2026-02-22T10:47:00Z
