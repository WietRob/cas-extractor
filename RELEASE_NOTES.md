# CAS Extractor — Release Notes

---

## v0.6.1 (2026-03-03) — Hygiene Fix

**Type:** Patch  
**Scope:** Resolution Gates

### Summary

Code-Hygiene-Release nach v0.6.0. Keine funktionalen Änderungen am ResolutionEngine-Verhalten.

### Changed

- Dead code in `scripts/check_resolution_gates.py` entfernt
- Unerreichbaren Duplikatblock (57 Zeilen) in `check_provenance_fields()` gelöscht
- Gate-Implementierung auf einen klaren, wartbaren Kontrollfluss reduziert

### Verified

- Regressionstests bleiben grün (21/21)
- Integrationstests bleiben grün
- Alle Gates passieren weiter (6/6)
- Keine API-Änderung
- Keine Re-Tagging- oder Rebase-Maßnahme nötig

### Notes

- Golden Baseline bleibt gültig
- Gate 6 behandelt die bestehende Baseline weiterhin korrekt als Pre-v0.6.0-Baseline ohne Provenance-Felder

---

## v0.6.0 (2026-03-03) — Structured Provenance

**Type:** Minor  
**Scope:** Resolution Engine

### Summary

Structured Provenance für explainable resolution eingeführt. Jede aufgelöste Kante kann jetzt strukturiert erklären, woher die Typinformation kommt.

### Added

- `source_kind` in `ResolutionStep` — Taxonomie des Typ-Source
- `source_symbol` in `ResolutionStep` — Das konkrete Symbol
- `evidence_path` in `ResolutionStep` — Derivation-Chain

### Changed

- Provenance-Population in den Resolvern erweitert:
  - H1 (local_var)
  - H2 (self_attr_init)
  - H2.5 (self_attr_method_local)
  - H2.6/H2.7 (self_attr_propagated)
  - H2.8 (factory_return)
  - H3 (constructor)
  - `static` (import_direct, local_function)
  - `qualified_attr` (import_qualified)
  - `self_dispatch`
  - `cls_dispatch`
  - `super_dispatch`
- YAML-Serialisierung erweitert, sodass Provenance-Felder in `resolution_detail.trace` ausgegeben werden
- Regressionstests um Provenance-Assertions erweitert (`assert_provenance` Helper)
- Gate 6 für Provenance-Coverage eingeführt

### Provenance Taxonomy

| source_kind | Bedeutung |
|-------------|-----------|
| `local_var` | H1: `x = ClassName()` |
| `self_attr_init` | H2: `self.attr = ClassName()` in `__init__` |
| `self_attr_method_local` | H2.5: `self.attr = ClassName()` in gleicher Methode |
| `self_attr_propagated` | H2.6/2.7: via Helper-Chain propagiert |
| `factory_return` | H2.8: `x = factory()` |
| `constructor` | H3: `ClassName().method()` |
| `import_qualified` | qualified_attr: `module.func` |
| `import_direct` | static: `from x import y` |
| `local_function` | static: lokale Modul-Funktion |
| `self_dispatch` | `self.method()` |
| `cls_dispatch` | `cls.method()` |
| `super_dispatch` | `super().method()` |
| `builtin` | Builtin-Funktionen |

### Verified

- Regressionstests grün (21/21)
- Integrationstests grün
- Gates grün (6/6)
- YAML-Ausgabe enthält Provenance-Felder für neue Runs

### Notes

- Die bestehende Golden Baseline unter `sprint-v050-engine/06-golden/v050-product-baseline/` stammt aus der Zeit vor v0.6.0
- Deshalb sind dort noch keine Provenance-Felder serialisiert
- Gate 6 skipped daher auf dieser Baseline (wie vorgesehen)
- Für vollständige Baseline-Abdeckung sollte die Golden Baseline in einem späteren, expliziten Schritt neu erzeugt werden

---

## v0.5.3 (2026-03-02) — Artifact Gates

**Type:** Patch  
**Scope:** Resolution Engine

### Summary

Artifact-level Gates und Drift-Detection für den bestehenden ResolutionEngine-Stand gehärtet.

### Changed

- Artifact-level Integrationstests hinzugefügt
- Golden-Manifest-Checks erweitert
- CI-Matrix und Gate-Runner gehärtet

### Verified

- Regressionstests grün
- Integrationstests grün
- Gates grün

---

## v0.4.5 GA (2026-02-23) — H2.9 Enhanced Resolution Metadata

**Release-Typ:** Feature Release  
**Scope:** Python Callgraph Extractor  
**Feature:** H2.9 Enhanced Resolution Metadata

### Was neu ist

v0.4.5 fügt **Auflösungs-Metadaten** zu jedem Call-Edge hinzu:

- **Heuristic tracking:** Welche Heuristik (H1, H2, H2.5, H2.6/2.7, H3) hat den Call aufgelöst
- **Resolution source:** Klartext-Bezeichnung der Auflösungsmethode
- **Backward compatible:** Keine Verhaltensänderung, nur zusätzliches optionales Feld

### CLI Usage

```bash
# H2.9 Metadata aktivieren (für Debugging/Analyse)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-h29-resolution-metadata true \
  --out ./artifacts

# Via Environment Variable
CAS_ENABLE_H29_RESOLUTION_METADATA=true python3 extract_python.py ...

# Default: H2.9 OFF (konservativ)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --out ./artifacts
```

### Output-Beispiel

```yaml
edges:
  - from: module.Class.run
    to: module.HTTPClient.send
    kind: method_call
    resolution_source: H2.5  # ← NEW: Which heuristic resolved
```

### Resolution Source Werte

| Wert | Bedeutung |
|------|-----------|
| H1 | Local variable dispatch (`x = Class(); x.method()`) |
| H2 | Class-level (`self.attr = Class()` in `__init__`) |
| H2.5 | Method-local (`self.attr = Class()` in same method) |
| H2.6/2.7 | Propagated from helper chain |
| H3 | Constructor chain (`ClassName().method()`) |
| self.method | `self.method()` within class |
| cls.method | `cls.method()` in @classmethod |
| super.method | `super().method()` |
| module-level | Static/qualified function call |
| unresolved | Could not resolve |

### Verhalten

| Flag | Output |
|------|--------|
| `--enable-h29-resolution-metadata false` | Keine metadata, wie bisher |
| `--enable-h29-resolution-metadata true` | Jeder Edge hat `resolution_source` Feld |

### Release Gates

| Gate | Status |
|------|--------|
| G1: Flag present, default OFF | ✅ PASS |
| G2: Baseline reproducible | ✅ PASS |
| G3: Metadata added correctly | ✅ PASS |
| G4: All heuristics tracked | ✅ PASS |
| G5: No behavior change | ✅ PASS |
| G6: Smoke test complete | ✅ PASS |
| G7: Backward compatible | ✅ PASS |
| G8: Release pack complete | ✅ PASS |

### Empfohlene Nutzung

| Szenario | H2.9 Modus |
|----------|------------|
| Produktion / Analyse | OFF (default) |
| Debugging / Audit | ON |
| CI/CD Quality Gates | OFF |

### Artefakte

- `sprint-v045-h29/06-release/release_gates_validation.md`
- `sprint-v045-h29/06-release/GO_NO_GO.md`
- `sprint-v045-h29/01-spec/H2.9_SCOPE.md`
- `sprint-v045-h29/01-spec/H2.9_FLAG_CONTRACT.md`

**Baseline:** v0.4.4 GA | Sprint: `sprint-v045-h29/` | **Decision: GO** ✅

---

## v0.4.4 GA (2026-02-23) — H2.8 Factory Return Inference

**Release-Typ:** Feature Release  
**Scope:** Python Callgraph Extractor  
**Feature:** H2.8 Bounded Factory Return Inference

### Was neu ist

v0.4.4 erweitert die H1/H2-Resolution um **Factory Return Inference**:

- **Factory detection:** Erkennt Funktionen mit direktem `return ClassName()` Pattern
- **Type inference:** `x = factory(); x.method()` → `ClassName.method` aufgelöst
- **Self-attr support:** `self.attr = factory()` → Typ für `self.attr.method()` inferiert
- **Bounded depth:** Aktuell auf depth=1 beschränkt (nur direkte Factory-Returns)
- **Conservative:** Nur single direct return, keine conditional returns, keine Variablen

### CLI Usage

```bash
# H2.8 aktivieren (optional, für maximale Coverage)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-h28-factory-return true \
  --out ./artifacts

# Via Environment Variable
CAS_ENABLE_H28_FACTORY_RETURN=true python3 extract_python.py ...

# Default: H2.8 OFF (konservativ)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --out ./artifacts
```

### Verhalten

| Pattern | H2.8 OFF | H2.8 ON |
|---------|----------|---------|
| `x = factory(); x.method()` | ❌ unresolved | ✅ method_call |
| `self.attr = factory()` in `__init__` | ❌ unresolved | ✅ method_call |
| `self.attr = factory()` in method | ❌ unresolved | ✅ method_call (via H2.5/H2.6/H2.7) |
| Conditional return factory | N/A | ❌ unresolved (conservative) |
| Indirect return (variable) | N/A | ❌ unresolved (conservative) |

### Beispiel

```python
def create_client():
    return HTTPClient()  # Factory function

class Example:
    def run(self):
        self.client = create_client()  # H2.8: infer HTTPClient
        self.client.send()             # H2.8 ON: HTTPClient.send
                                      # H2.8 OFF: unresolved
```

### Mini-Fixture Ergebnisse

| Kategorie | Fälle | Status |
|-----------|-------|--------|
| H2.8 Positive | 7/7 | ✅ PASS |
| H2.8 Negative | 8/8 | ✅ PASS |
| False Positives | 0 | ✅ |
| Regressions H1/H2/H2.5/H2.6/H2.7/H3 | 0 | ✅ |

### Release Gates

| Gate | Status |
|------|--------|
| G1: Flag present, default OFF | ✅ PASS |
| G2: Mini-fixture OFF reproducible | ✅ PASS |
| G3: Mini-fixture ON resolves positives | ✅ PASS |
| G4: 0 false positives | ✅ PASS |
| G5: No regressions | ✅ PASS |
| G6: Factory detection bounded | ✅ PASS |
| G7: Smoke test complete | ✅ PASS |
| G8: Release pack complete | ✅ PASS |

### Empfohlene Nutzung

| Szenario | H2.8 Modus |
|----------|------------|
| Produktion / Analyse | OFF (default) |
| Maximale Coverage | ON |
| Historischer Metrikvergleich | OFF |
| CI/CD Quality Gates | OFF |

### Artefakte

- `sprint-v044-h28/06-release/release_gates_validation.md`
- `sprint-v044-h28/06-release/GO_NO_GO.md`
- `sprint-v044-h28/01-spec/H2.8_SCOPE.md`
- `sprint-v044-h28/01-spec/H2.8_FLAG_CONTRACT.md`

**Baseline:** v0.4.3 GA | Sprint: `sprint-v044-h28/` | **Decision: GO** ✅

---

## v0.4.3 GA (2026-02-23) — H2.7 Bounded Multi-Hop Self-Attr Propagation

**Release-Typ:** Feature Release  
**Scope:** Python Callgraph Extractor  
**Feature:** H2.7 Bounded Multi-Hop Transitive Self-Attr Propagation

### Was neu ist

v0.4.3 erweitert die H2.6-Resolution um **Multi-Hop-Propagation** über Helper-Ketten:

- **Multi-hop chains:** Wenn `run() → prepare() → init()` und `init()` weist `self.attr = ClassName()` zu, propagiere den Typ zur aufrufenden Methode
- **Bounded depth:** Max. Helper-Ketten-Tiefe konfigurierbar (default: 2)
- **Depth control:** depth=2 für zwei-hop, depth=3 für drei-hop Ketten
- **Cycle detection:** Zyklen werden erkannt und übersprungen
- **Conflict handling:** Gleicher attr mit unterschiedlichen Typen → unresolved (konservativ)

### CLI Usage

```bash
# H2.7 aktivieren (optional, für maximale Coverage)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-h27-self-attr-transitive true \
  --out ./artifacts

# Mit angepasster Tiefe
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-h27-self-attr-transitive true \
  --h27-max-chain-depth 3 \
  --out ./artifacts

# Via Environment Variable
CAS_ENABLE_H27_SELF_ATTR_TRANSITIVE=true python3 extract_python.py ...
CAS_H27_MAX_CHAIN_DEPTH=3 python3 extract_python.py ...

# Default: H2.7 OFF (konservativ)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --out ./artifacts
```

### Verhalten

| Pattern | H2.7 OFF | H2.7 ON |
|---------|----------|---------|
| Single-hop: `run() -> helper() -> attr = Class` | ✅ method_call (H2.6) | ✅ method_call (H2.7) |
| Two-hop: `run() -> h1() -> h2() -> attr = Class` | ❌ unresolved | ✅ method_call (depth >= 2) |
| Three-hop chain | ❌ unresolved | ✅ method_call (depth >= 3) |
| Cycle detected | N/A | ✅ blocked (no infinite loop) |
| Conflict (same attr, diff types) | N/A | ❌ unresolved (conservative) |

### Beispiel

```python
class Example:
    def init_client(self):
        self.client = HTTPClient()  # Assignment at depth 2
    
    def prepare(self):
        self.init_client()           # Depth 1 from run
    
    def run(self):
        self.prepare()               # Entry point
        self.client.send()           # H2.7 ON: HTTPClient.send
                                     # H2.7 OFF: unresolved
```

### Mini-Fixture Ergebnisse

| Kategorie | Fälle | Status |
|-----------|-------|--------|
| H2.7 Positive | 7/7 | ✅ PASS |
| H2.7 Negative | 10/10 | ✅ PASS |
| False Positives | 0 | ✅ |
| Regressions H1/H2/H2.5/H2.6/H3 | 0 | ✅ |

### Release Gates

| Gate | Status |
|------|--------|
| G1: Flag present, default OFF | ✅ PASS |
| G2: Mini-fixture OFF reproducible | ✅ PASS |
| G3: Mini-fixture ON resolves positives | ✅ PASS |
| G4: 0 false positives | ✅ PASS |
| G5: No regressions | ✅ PASS |
| G6: Cycle detection + bounded depth | ✅ PASS |
| G7: Golden benchmark complete | ✅ PASS |
| G8: Release pack complete | ✅ PASS |

### Empfohlene Nutzung

| Szenario | H2.7 Modus |
|----------|------------|
| Produktion / Analyse | OFF (default) |
| Maximale Coverage | ON |
| Historischer Metrikvergleich | OFF |
| CI/CD Quality Gates | OFF |

### Artefakte

- `sprint-v043-h27/06-release/release_gates_validation.md`
- `sprint-v043-h27/06-release/GO_NO_GO.md`
- `sprint-v043-h27/01-spec/H2.7_SCOPE.md`
- `sprint-v043-h27/01-spec/H2.7_FLAG_CONTRACT.md`

**Baseline:** v0.4.2 GA | Sprint: `sprint-v043-h27/` | **Decision: GO** ✅

---

## v0.4.2 GA (2026-02-22) — H2.6 Class-Local Inter-Method Self-Attr Propagation

**Release-Typ:** Feature Release  
**Scope:** Python Callgraph Extractor  
**Feature:** H2.6 Class-Local Inter-Method Self-Attr Propagation

### Was neu ist

v0.4.2 erweitert die H2/H2.5-Resolution um **Inter-Method-Propagation** innerhalb einer Klasse:

- **Class-local propagation:** Wenn `self.helper()` aufgerufen wird und `helper` ein `self.attr = ClassName()` enthält, propagiere den Typ zur aufrufenden Methode
- **Bounded depth:** Max. Helper-Tiefe konfigurierbar (default: 2)
- **Cycle detection:** Zyklen werden erkannt und übersprungen
- **Conflict handling:** Gleicher attr mit unterschiedlichen Typen → unresolved (konservativ)

### CLI Usage

```bash
# H2.6 aktivieren (optional, für maximale Coverage)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-h26-self-attr-intermethod true \
  --out ./artifacts

# Mit angepasster Tiefe
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-h26-self-attr-intermethod true \
  --h26-max-helper-depth 3 \
  --out ./artifacts

# Via Environment Variable
CAS_ENABLE_H26_SELF_ATTR_INTERMETHOD=true python3 extract_python.py ...
CAS_H26_MAX_HELPER_DEPTH=3 python3 extract_python.py ...

# Default: H2.6 OFF (konservativ)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --out ./artifacts
```

### Verhalten

| Pattern | H2.6 OFF | H2.6 ON |
|---------|----------|---------|
| `self.attr = Class()` in `__init__`, call in any method | ✅ method_call (H2) | ✅ method_call (H2) |
| `self.attr = Class()` in non-`__init__`, call in same method | ✅ method_call (H2.5) | ✅ method_call (H2.5) |
| `self.attr = Class()` in helper, call after `self.helper()` | ❌ unresolved | ✅ method_call (H2.6) |
| Cycle detected | N/A | ✅ blocked (no infinite loop) |
| Conflict (same attr, diff types from helpers) | N/A | ❌ unresolved (conservative) |

### Resolution Priority

1. **H2.5 method-local** (intra-method assignment)
2. **H2.6 propagated** (from called helpers)
3. **H2 class-level** (`__init__` assignment)

### Beispiel

```python
class Example:
    def setup(self):
        self.client = HTTPClient()  # H2.6 anchor in helper
    
    def run(self):
        self.setup()                 # H2.6: detect self.setup() call
        self.client.send()           # H2.6 ON: HTTPClient.send
                                     # H2.6 OFF: unresolved
```

### Mini-Fixture Ergebnisse

| Kategorie | Fälle | Status |
|-----------|-------|--------|
| H2.6 Positive | 6/6 | ✅ PASS |
| H2.6 Negative | 8/8 | ✅ PASS |
| False Positives | 0 | ✅ |
| Regressions H1/H2/H2.5/H3 | 0 | ✅ |

### Release Gates

| Gate | Status |
|------|--------|
| G1: Implementation Completeness | ✅ PASS |
| G2: Test Coverage | ✅ PASS |
| G3: Zero False Positives | ✅ PASS |
| G4: Zero Regressions | ✅ PASS |
| G5: Feature Flag Correct | ✅ PASS |
| G6: Documentation Complete | ✅ PASS |
| G7: Evidence Pack Complete | ✅ PASS |
| G8: Reproducibility | ✅ PASS |

### Empfohlene Nutzung

| Szenario | H2.6 Modus |
|----------|------------|
| Produktion / Analyse | OFF (default) |
| Maximale Coverage | ON |
| Historischer Metrikvergleich | OFF |
| CI/CD Quality Gates | OFF |

### Artefakte

- `sprint-v042-h26/09-release/release_gates_validation.md`
- `sprint-v042-h26/09-release/GO_NO_GO.md`
- `sprint-v042-h26/07-quality/mini_fixture_results.md`
- `sprint-v042-h26/01-spec/H2.6_SCOPE.md`
- `sprint-v042-h26/01-spec/H2.6_FLAG_CONTRACT.md`

**Baseline:** v0.4.1 GA | Sprint: `sprint-v042-h26/` | **Decision: GO** ✅

---

## v0.4.1 GA (2026-02-22) — H2.5 Intra-Method Non-`__init__` Self-Attr Resolution

**Release-Typ:** Feature Release  
**Scope:** Python Callgraph Extractor  
**Feature:** H2.5 Intra-Method Non-`__init__` Self-Attr Resolution

### Was neu ist

v0.4.1 erweitert die H2-Resolution um `self.attr = ClassName(...)` Zuweisungen **außerhalb von `__init__`**:

- **Intra-Method Write-Before-Use:** Wenn `self.attr = ClassName()` und `self.attr.method()` in **derselben Methode** stehen, wird der Call aufgelöst
- **Feature Flag:** `--enable-h25-self-attr-noninit true|false` (Default: `false`)
- **Priority:** H2.5 (method-local) > H2 (class-level `__init__`)

### CLI Usage

```bash
# H2.5 aktivieren (optional, für maximale Coverage)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --enable-h25-self-attr-noninit true \
  --out ./artifacts

# Via Environment Variable
CAS_ENABLE_H25_SELF_ATTR_NONINIT=true python3 extract_python.py ...

# Default: H2.5 OFF (konservativ)
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --out ./artifacts
```

### Verhalten

| Pattern | H2.5 OFF | H2.5 ON |
|---------|----------|---------|
| `self.attr = Class()` in `__init__`, call in any method | ✅ method_call (H2) | ✅ method_call (H2) |
| `self.attr = Class()` in non-`__init__`, call in **same** method | ❌ unresolved | ✅ method_call (H2.5) |
| `self.attr = Class()` in non-`__init__`, call in **different** method | ❌ unresolved | ❌ unresolved |
| Reassignment in method | H2 value | H2.5 value (last wins) |

### Scope

| IN Scope | OUT of Scope |
|----------|--------------|
| ✅ Intra-Method (write-before-use) | ❌ Cross-Method Propagation |
| ✅ `Assign` + `AnnAssign` | ❌ Factory Return Inference |
| ✅ Last-assignment-wins | ❌ CFG/Branch/Path-Sensitivity |

### Beispiel

```python
class Example:
    def __init__(self):
        self.client = HTTPClient()  # H2 anchor
    
    def reconnect(self):
        self.client = WebSocketClient()  # H2.5 anchor (overrides H2)
        self.client.send()  # H2.5 ON: WebSocketClient.send
                             # H2.5 OFF: HTTPClient.send (from __init__)
    
    def run(self):
        self.client.send()  # H2.5 ON/OFF: HTTPClient.send (no H2.5 in run)
```

### Mini-Fixture Ergebnisse

| Kategorie | Fälle | Status |
|-----------|-------|--------|
| H2.5 Positive | 6/6 | ✅ PASS |
| H2.5 Negative | 5/5 | ✅ PASS |
| False Positives | 0 | ✅ |
| Regressions H1/H2/H3 | 0 | ✅ |

### Release Gates

| Gate | Status |
|------|--------|
| G1: Implementation Completeness | ✅ PASS |
| G2: Test Coverage | ✅ PASS |
| G3: Zero False Positives | ✅ PASS |
| G4: Zero Regressions | ✅ PASS |
| G5: Feature Flag Correct | ✅ PASS |
| G6: Documentation Complete | ✅ PASS |
| G7: Evidence Pack Complete | ✅ PASS |
| G8: Reproducibility | ✅ PASS |

### Empfohlene Nutzung

| Szenario | H2.5 Modus |
|----------|------------|
| Produktion / Analyse | OFF (default) |
| Maximale Coverage | ON |
| Historischer Metrikvergleich | OFF |
| CI/CD Quality Gates | OFF |

### Artefakte

- `sprint-v041-h25/09-release/v0.4.1-h25-report.md`
- `sprint-v041-h25/09-release/GO_NO_GO.md`
- `sprint-v041-h25/09-release/release_gates_validation.md`
- `sprint-v041-h25/09-release/merge_tag_readiness.md`
- `sprint-v041-h25/04-mini-fixture/` (Test-Evidence)

**Baseline:** v0.4.0 GA | Sprint: `sprint-v041-h25/` | **Decision: GO** ✅

---

## v0.4 GA (2026-02-22) — H2.1 Feature-Flag for Comparability Mode

**Release-Typ:** Feature Release  
**Scope:** Python Callgraph Extractor  
**Feature:** H2.1 Feature-Flag `--emit-unresolved-self-attr` for Coverage vs Comparability Mode

### Was neu ist

v0.4 führt ein Feature-Flag ein, das steuert, ob unaufgelöste `self.attr.method()` Pattern emittiert werden:

- **Coverage Mode** (`--emit-unresolved-self-attr true`, default): Maximale Callgraph-Vollständigkeit
- **Comparability Mode** (`--emit-unresolved-self-attr false`): Historische Metrikvergleichbarkeit

### CLI Usage

```bash
# Coverage Mode (default)
python3 extract_python.py --repo-root . --repo-name repo://main --revision git:HEAD --out ./artifacts

# Comparability Mode (for metric comparisons)
python3 extract_python.py --repo-root . --repo-name repo://main --revision git:HEAD --out ./artifacts --emit-unresolved-self-attr false

# Via Environment Variable
CAS_EMIT_UNRESOLVED_SELF_ATTR=false python3 extract_python.py ...
```

### Verhalten

| Pattern | Coverage Mode (true) | Comparability Mode (false) |
|---------|---------------------|---------------------------|
| Resolved H2 dispatch | ✅ method_call | ✅ method_call (identisch) |
| Unresolved H2 3-part (`?.self.<attr>.<method>`) | ✅ Edge emittiert | ❌ Edge geskippt |
| Unresolved H2 2-part (`?.self.<method>`) | ✅ Edge emittiert | ✅ Edge emittiert |

### Golden-Test (httpie) — Kernergebnis

| Metric | v0.3b | v0.3c (TRUE) | v0.4 GA (FALSE) |
|--------|-------|--------------|-----------------|
| Total call edges | 2810 | 2899 | 2814 |
| method_call | 204 | 208 | **208** |
| Unresolved (?.*) | 919 | 1004 | **919** |
| H2 3-part unresolved | N/A | 85 | **0** |

### Interpretation

- **H2 Quality Gain preserved**: +4 method_call in beiden Modi
- **Comparability restored**: v0.4 GA (FALSE) ≈ v0.3b + H2 quality gain
- **No regression**: H1/H3 dispatches unchanged

### Verifiziertes Verhalten

| Check | Ergebnis |
|-------|----------|
| 6 Release Gates | 6/6 PASS |
| 25 Spot Checks | 25/25 PASS |
| False Positives | 0 |
| Regression H1/H3 | 0 |

### Empfohlene Nutzung

| Szenario | Modus | Flag |
|----------|-------|------|
| Produktion / Analyse | Coverage | `true` (default) |
| Historischer Metrikvergleich | Comparability | `false` |
| CI/CD Quality Gates | Comparability | `false` |

### Artefakte

- `sprint-v04ga/05-release/v0.4-ga-report.md`
- `sprint-v04ga/05-release/GO_NO_GO.md`
- `sprint-v04ga/03-golden/metrics/benchmark_matrix.md`
- `golden-v04rc/`

**Baseline:** httpie/cli @ git:HEAD | Sprint: `sprint-v04ga/`

---

## v0.3c (2026-02-21) — H2 Instance-Attribute-Dispatch

**Release-Typ:** Minor Feature Release  
**Scope:** Python Callgraph Extractor  
**Feature:** H2 Instance-Attribute-Dispatch (`self.attr = Class(); self.attr.method()`)

### Was neu ist

v0.3c erweitert die Call-Resolution um das Pattern:

- **Zuweisung in `__init__`:** `self.attr = ClassName(...)`
- **Nutzung in Methoden:** `self.attr.method()`

Wenn `self.attr` in `__init__` eindeutig auf eine bekannte Klasse zurückgeführt werden kann, wird der Aufruf als `method_call` aufgelöst.

### Beispiel

**Vor v0.3c:** `self.status.started()` wurde häufig übersprungen (kein Edge).  
**Ab v0.3c:** Auflösung zu `DownloadStatus.started` (method_call), falls `self.status = DownloadStatus(...)` in `__init__` erkannt wird.

### Verifiziertes Verhalten

**Mini-Fixture H2:** 10/10 PASS

| Kategorie | Fälle | Status |
|-----------|-------|--------|
| Positive | Basic, Multiple Attrs, Reassignment, Annotated | ✅ |
| Negative | NotInInit, Factory, UnknownClass, NoInit | ✅ (bleiben unresolved) |

### Golden-Test (httpie) — Kernergebnis

**Wichtig:** v0.3c verbessert Resolution und erhöht die Sichtbarkeit des Callgraphs.

| Metric | v0.3b | v0.3c | Delta |
|--------|-------|-------|-------|
| Total call edges | 2810 | 2899 | **+89** |
| method_call | 204 | 208 | **+4** |
| Unresolved (?.*) | 919 | 1004 | **+85** |

### Interpretation (audit-relevant)

Der Anstieg der unresolved Calls ist **keine Regression**, sondern ein **Coverage-Effekt**:

- **+4** neue korrekt aufgelöste Dispatches
- **+85** neu sichtbare, bislang übersprungene `self.attr.method()` Aufrufe

**Within previously visible edge population: keine strukturelle Regression.**

### Validierung

| Check | Ergebnis |
|-------|----------|
| Structural Validation | 100% PASS |
| Semantic Validator | ausgeführt, erwartete Violations dokumentiert |
| Spot Checks | 25/25 verifiziert, 0 False Positives |

### Kompatibilität / Risiko

| Aspekt | Bewertung |
|--------|-----------|
| Breaking Change | Nein (keine Schema-Änderung) |
| Behavioral Change | Ja (mehr Edges durch Coverage) |
| Historischer Metrikvergleich | Beeinflusst (Counts steigen) |

### Artefakte

- `v0.3c-report.md`
- `golden-v03c/`
- `validation-v03c.txt`
- `/tmp/h2-verify/` (Mini-Fixture)

**Baseline:** httpie/cli @ git:HEAD | Validation: `validation-v03c.txt`

---

## v0.3b (2026-02-21) — H1 Local Variable Dispatch

**Feature:** H1 Local Variable Dispatch (`x = ClassName(); x.method()`)

- **Unresolved:** 970 → 919 (**-51, -5.3%**)
- **method_call:** 0 → 204 (**+204**)
- **super_call:** 0 → 8 (**+8**)
- **Dispatch rate:** 0% → 7.5%

### Details

Siehe `v0.3b-final-report.md`

**Baseline:** httpie/cli @ git:HEAD | Validation: `validation-v03b.txt`

---

## v0.3a (2026-02-21) — H3 Constructor Chain

**Feature:** H3 Constructor Chain Resolution (`ClassName().method()`)

- **method_call:** +153 (primär v0.2 self/cls dispatch)
- **super_call:** +8
- **Dispatch rate:** 5.7%

### Details

Siehe `v0.3a-report.md`

---

## v0.2 (2026-02-21) — Self/Cls/Super Dispatch

**Features:**

- `self.method()` → `CurrentClass.method`
- `cls.method()` → `CurrentClass.method` (@classmethod)
- `super().method()` → `BaseClass.method`

### Details

Siehe `golden-test-report-v02.md`
