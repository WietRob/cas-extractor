=== T12: POSITIVE H2.5 CASES ===

P1: TestH25Basic.setup - HTTPClient.send:
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-b48a1974.yaml-    to: test_h25.HTTPClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-b48a1974.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-b48a1974.yaml-    to: test_h25.HTTPClient.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-b48a1974.yaml-    kind: method_call

P2: TestH25Multiple.configure - HTTPClient.send + DownloadStatus.started:
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    to: test_h25.HTTPClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    to: test_h25.DownloadStatus
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    to: test_h25.HTTPClient.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    kind: method_call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    to: test_h25.DownloadStatus.started
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-1283cddf.yaml-    kind: method_call

P3: TestH25Reassign.reconnect - WebSocketClient.send (last wins):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-3b4ee18f.yaml-    to: test_h25.HTTPClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-3b4ee18f.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-3b4ee18f.yaml-    to: test_h25.WebSocketClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-3b4ee18f.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-3b4ee18f.yaml-    to: test_h25.WebSocketClient.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-3b4ee18f.yaml-    kind: method_call

P4: TestH25AnnAssign.initialize - HTTPClient.send:
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-2ce406f9.yaml-    to: test_h25.HTTPClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-2ce406f9.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-2ce406f9.yaml-    to: test_h25.HTTPClient.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-2ce406f9.yaml-    kind: method_call

P5: TestH25OverrideH2.reconnect - WebSocketClient.send (H2.5 wins over H2):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-48f8373f.yaml-    to: test_h25.WebSocketClient
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-48f8373f.yaml-    kind: call
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-48f8373f.yaml-    to: test_h25.WebSocketClient.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-48f8373f.yaml-    kind: method_call

P5b: TestH25OverrideH2.run - HTTPClient.send (H2 from __init__):
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-48f8373f.yaml-    to: test_h25.HTTPClient.send
sprint-v041-h25/04-mini-fixture/on/EVID-py.callgraph-48f8373f.yaml-    kind: method_call
