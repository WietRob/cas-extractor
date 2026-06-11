=== T13: NEGATIVE H2.5 CASES ===

N1: TestH25CrossMethod - cross-method (unresolved):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-960ee513.yaml-    to: test_h25.HTTPClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-960ee513.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-960ee513.yaml-    to: ?.self.client.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-960ee513.yaml-    kind: call

N2: TestH25Factory - factory (unresolved):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-450155ea.yaml:    to: test_h25.TestH25Factory._create
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-450155ea.yaml-    kind: method_call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-450155ea.yaml-    to: ?.self.client.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-450155ea.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-450155ea.yaml-    to: test_h25.HTTPClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-450155ea.yaml-    kind: call

N3: TestH25Unknown - unknown class (unresolved):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-9c8327d6.yaml-    to: ?.SomeUnknownClass
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-9c8327d6.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-9c8327d6.yaml-    to: ?.self.handler.process
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-9c8327d6.yaml-    kind: call

N4: TestH25NoAssign - no assignment (unresolved):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-c5464983.yaml-    to: ?.self.client.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-c5464983.yaml-    kind: call

N5: TestH25Conditional - conditional (unresolved):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-d2e9643e.yaml-    to: test_h25.WebSocketClient.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-d2e9643e.yaml-    kind: method_call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-d2e9643e.yaml-    to: test_h25.WebSocketClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-d2e9643e.yaml-    kind: call
