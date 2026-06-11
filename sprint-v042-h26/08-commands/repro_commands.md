# CAS Extractor v0.4.2 H2.6 — Reproducible Commands

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

## A) H2.6 Flag Verification

### A.1 Check Help Text (after implementation)

```bash
python3 extract_python.py --help
```

**Expected:** `--enable-h26-self-attr-intermethod` visible with help text, default=false

### A.2 Test H2.6 OFF (default)

```bash
python3 extract_python.py \
  --repo-root /tmp/h26-verify \
  --repo-name repo://test \
  --revision git:test \
  --out /tmp/h26-test-off
```

**Expected:** H2.6 patterns stay unresolved (use H2/H2.5 only)

### A.3 Test H2.6 ON

```bash
python3 extract_python.py \
  --repo-root /tmp/h26-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h26-self-attr-intermethod true \
  --out /tmp/h26-test-on
```

**Expected:** H2.6 patterns resolved to method_call via inter-method propagation

### A.4 Test H2.6 ON with Custom Depth

```bash
python3 extract_python.py \
  --repo-root /tmp/h26-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h26-self-attr-intermethod true \
  --h26-max-helper-depth 3 \
  --out /tmp/h26-test-depth3
```

**Expected:** Propagation depth extended to 3 levels

### A.5 Test ENV Variable

```bash
CAS_ENABLE_H26_SELF_ATTR_INTERMETHOD=true python3 extract_python.py \
  --repo-root /tmp/h26-verify \
  --repo-name repo://test \
  --revision git:test \
  --out /tmp/h26-test-env
```

**Expected:** Same behavior as A.3

---

## B) Mini-Fixture Tests

### B.1 Create H2.6 Mini-Fixture

```bash
mkdir -p /tmp/h26-verify

cat > /tmp/h26-verify/test_h26.py << 'EOF'
# === H2.6 POSITIVE CASES (inter-method propagation) ===

class HTTPClient:
    def send(self): pass
    def close(self): pass

class WebSocketClient:
    def send(self): pass
    def connect(self): pass

class DataParser:
    def parse(self): pass
    def validate(self): pass

# P1: Basic inter-method - setup assigns, run uses
class TestH26Basic:
    def setup(self):
        self.client = HTTPClient()  # H2.6 anchor in helper
    
    def run(self):
        self.setup()                 # H2.6: detect call to setup
        self.client.send()           # H2.6: resolve to HTTPClient.send

# P2: Multiple attrs from helper
class TestH26Multiple:
    def configure(self):
        self.client = HTTPClient()
        self.parser = DataParser()
    
    def process(self):
        self.configure()
        self.client.send()           # H2.6: HTTPClient.send
        self.parser.parse()          # H2.6: DataParser.parse

# P3: Chain of helpers (depth 2)
class TestH26Chain:
    def init_client(self):
        self.client = HTTPClient()
    
    def setup(self):
        self.init_client()           # H2.6: depth 1
    
    def run(self):
        self.setup()                 # H2.6: depth 2
        self.client.send()           # H2.6: HTTPClient.send (if depth >= 2)

# P4: Helper with AnnAssign
class TestH26AnnAssign:
    def initialize(self):
        self.client: HTTPClient = HTTPClient()
    
    def execute(self):
        self.initialize()
        self.client.send()           # H2.6: HTTPClient.send

# P5: Override H2 via helper
class TestH26OverrideH2:
    def __init__(self):
        self.client = HTTPClient()  # H2 anchor
    
    def reconnect(self):
        self.client = WebSocketClient()  # H2.5 in helper
    
    def run(self):
        self.reconnect()
        self.client.send()           # H2.6: WebSocketClient.send (H2.5 wins over H2)

# P6: H2.5 in caller + H2.6 from helper merge
class TestH26Merge:
    def setup_parser(self):
        self.parser = DataParser()
    
    def process(self):
        self.client = HTTPClient()   # H2.5 in caller
        self.setup_parser()          # H2.6 from helper
        self.client.send()           # H2.5: HTTPClient.send
        self.parser.parse()          # H2.6: DataParser.parse

# === H2.6 NEGATIVE CASES (unresolved/skip) ===

# N1: Factory in helper
class TestH26Factory:
    def create_client(self):
        self.client = self._factory()  # Factory - can't infer
        self.client.send()              # Unresolved
    
    def _factory(self):
        return HTTPClient()

# N2: Unknown class in helper
class TestH26Unknown:
    def setup(self):
        self.handler = SomeUnknownClass()  # Unknown class
    
    def run(self):
        self.setup()
        self.handler.process()             # Unresolved

# N3: Cross-class (out of scope)
class HelperClass:
    def setup(self):
        self.client = HTTPClient()

class CallerClass:
    def __init__(self, helper):
        self.helper = helper
    
    def run(self):
        self.helper.setup()            # Cross-class - out of scope
        # No self.client here

# N4: Cycle detection
class TestH26Cycle:
    def method_a(self):
        self.method_b()
        self.client.send()
    
    def method_b(self):
        self.method_a()  # Cycle!
        self.client = HTTPClient()

# N5: Conflict (same attr, different types)
class TestH26Conflict:
    def setup_http(self):
        self.client = HTTPClient()
    
    def setup_ws(self):
        self.client = WebSocketClient()
    
    def run(self):
        self.setup_http()
        self.setup_ws()                # Conflict: client = HTTPClient vs WebSocketClient
        self.client.send()             # Unresolved (conflict)

# N6: Depth exceeded
class TestH26DepthExceeded:
    def level1(self):
        self.client = HTTPClient()
    
    def level2(self):
        self.level1()
    
    def level3(self):
        self.level2()
    
    def run(self):
        self.level3()                  # Depth 3 > default max 2
        self.client.send()             # Unresolved (if depth cap = 2)

# N7: Conditional in helper (conservative)
class TestH26Conditional:
    def setup(self, use_websocket):
        if use_websocket:
            self.client = WebSocketClient()  # Conditional - may not assign
        # No else branch - client may be undefined
    
    def run(self):
        self.setup(True)
        self.client.send()             # Unresolved (conservative)

# N8: No helper call
class TestH26NoHelper:
    def setup(self):
        self.client = HTTPClient()
    
    def run(self):
        # No self.setup() call!
        self.client.send()             # Unresolved (no H2.5, no H2.6 propagation)
EOF
echo "H2.6 mini-fixture created at /tmp/h26-verify/test_h26.py"
```

### B.2 Extract H2.6 OFF

```bash
python3 extract_python.py \
  --repo-root /tmp/h26-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h26-self-attr-intermethod false \
  --emit-unresolved-self-attr true \
  --out "sprint-v042-h26/04-mini-fixture/off" \
  2>&1 | tee "sprint-v042-h26/04-mini-fixture/off/extraction.log"
```

### B.3 Extract H2.6 ON (default depth 2)

```bash
python3 extract_python.py \
  --repo-root /tmp/h26-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h26-self-attr-intermethod true \
  --h26-max-helper-depth 2 \
  --emit-unresolved-self-attr true \
  --out "sprint-v042-h26/04-mini-fixture/on" \
  2>&1 | tee "sprint-v042-h26/04-mini-fixture/on/extraction.log"
```

### B.4 Extract H2.6 ON (depth 3)

```bash
python3 extract_python.py \
  --repo-root /tmp/h26-verify \
  --repo-name repo://test \
  --revision git:test \
  --enable-h26-self-attr-intermethod true \
  --h26-max-helper-depth 3 \
  --emit-unresolved-self-attr true \
  --out "sprint-v042-h26/04-mini-fixture/on-depth3" \
  2>&1 | tee "sprint-v042-h26/04-mini-fixture/on-depth3/extraction.log"
```

---

## C) Smoke Tests

### C.1 Smoke H2.6 OFF

```bash
python3 extract_python.py \
  --repo-root cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:test \
  --enable-h26-self-attr-intermethod false \
  --out sprint-v042-h26/05-smoke/off \
  2>&1 | tee sprint-v042-h26/05-smoke/smoke_off.md
```

### C.2 Smoke H2.6 ON

```bash
python3 extract_python.py \
  --repo-root cas_extractor \
  --repo-name repo://cas_extractor \
  --revision git:test \
  --enable-h26-self-attr-intermethod true \
  --h26-max-helper-depth 2 \
  --out sprint-v042-h26/05-smoke/on \
  2>&1 | tee sprint-v042-h26/05-smoke/smoke_on.md
```

---

## D) Comparison Commands

### D.1 Compare OFF vs ON

```bash
echo "=== H2.6 OFF edges ==="
grep -h "to:" sprint-v042-h26/04-mini-fixture/off/EVID-py.callgraph-*.yaml | wc -l

echo "=== H2.6 ON edges ==="
grep -h "to:" sprint-v042-h26/04-mini-fixture/on/EVID-py.callgraph-*.yaml | wc -l

echo "=== Delta ==="
# Calculate difference
```

### D.2 Check Positive H2.6 Cases

```bash
# P1: HTTPClient.send via setup()
grep "to: test_h26.HTTPClient.send" sprint-v042-h26/04-mini-fixture/on/EVID-py.callgraph-*.yaml

# P3: Chain depth 2
grep -A5 "run.*test_h26" sprint-v042-h26/04-mini-fixture/on/EVID-py.callgraph-*.yaml
```

### D.3 Check Negative H2.6 Cases

```bash
# N1: Factory - should be unresolved
grep "to: '?.self.client.send'" sprint-v042-h26/04-mini-fixture/on/EVID-py.callgraph-*.yaml

# N4: Cycle - should not cause infinite loop (test passes if command returns)
echo "Cycle test passed if this command returns"
```

---

## E) Metrics Commands

### E.1 Count Total Edges

```bash
grep -h "to:" sprint-v042-h26/04-mini-fixture/*/EVID-py.callgraph-*.yaml | wc -l
```

### E.2 Count method_call Edges

```bash
grep "kind: method_call" sprint-v042-h26/04-mini-fixture/on/EVID-py.callgraph-*.yaml | wc -l
```

### E.3 Count H2.6 Specific Resolutions

```bash
# After implementation, grep for self_attr_dispatch which includes H2.6
grep "self_attr_dispatch" sprint-v042-h26/04-mini-fixture/on/EVID-py.callgraph-*.yaml | wc -l
```

---

**Generated:** 2026-02-22
