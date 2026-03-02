"""
Evidence Writer — serializes extracted data to CAS-compliant YAML artifacts.

Schema: cas.evidence.v0.1
Required fields: schema, id, kind, type, created_at, created_by, source, payload

Payload schemas (from $defs):
  py.symbols:     { symbols: [{qualified, kind, file, ...}] }
  py.importgraph: { imports: [{from, imports: [...]}] }
  py.callgraph:   { nodes: [{symbol, file?}], edges: [{from, to, kind, edge_id, range?}] }
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cas_extractor.models.evidence import (
    CallEntry,
    EvidenceArtifact,
    EvidenceLevel,
    ImportEntry,
    SourceInfo,
    SymbolEntry,
)
from cas_extractor.utils.ids import evidence_id


def write_symbols_evidence(
    symbols: list[SymbolEntry],
    source: SourceInfo,
    out_dir: str,
) -> list[str]:
    """Group symbols by module and write one evidence artifact per module."""
    by_module: dict[str, list[SymbolEntry]] = {}
    for sym in symbols:
        if sym.kind == "module":
            mod = sym.qualified_name
        else:
            parts = sym.qualified_name.rsplit(".", 1)
            mod = parts[0] if len(parts) > 1 else sym.qualified_name
        by_module.setdefault(mod, []).append(sym)

    written = []
    for mod, mod_symbols in sorted(by_module.items()):
        eid = evidence_id("py.symbols", mod)
        # Schema: payload_py_symbols — required: [symbols], additionalProperties: false
        payload = {
            "symbols": [_symbol_to_dict(s) for s in mod_symbols],
        }
        artifact = EvidenceArtifact(
            id=eid,
            type="py.symbols",
            level=EvidenceLevel.E0,
            source=source,
            payload=payload,
        )
        path = _write_artifact(artifact, out_dir)
        written.append(path)
    return written


def write_imports_evidence(
    imports: list[ImportEntry],
    source: SourceInfo,
    out_dir: str,
) -> list[str]:
    """Write import graph evidence, one file per source module.

    Schema: payload_py_importgraph
      required: [imports]
      imports[]: { from: str, imports: [str], symbols?: [{name, alias?, module}] }
    """
    by_module: dict[str, list[ImportEntry]] = {}
    for imp in imports:
        by_module.setdefault(imp.source_module, []).append(imp)

    written = []
    for mod, mod_imports in sorted(by_module.items()):
        eid = evidence_id("py.importgraph", mod)

        # Group imports by target module to match schema structure
        # Schema expects: imports[].{from, imports[], symbols?[]}
        # "from" = source module, "imports" = list of target module names
        by_target: dict[str, list[ImportEntry]] = {}
        for imp in mod_imports:
            # Group by source (the importing module)
            by_target.setdefault(imp.source_module, []).append(imp)

        import_entries = []
        # Each entry: one source module importing N targets
        targets = [imp.target for imp in mod_imports]
        import_entries.append(
            {
                "from": mod,
                "imports": targets,
            }
        )

        payload = {
            "imports": import_entries,
        }
        artifact = EvidenceArtifact(
            id=eid,
            type="py.importgraph",
            level=EvidenceLevel.E0,
            source=source,
            payload=payload,
        )
        path = _write_artifact(artifact, out_dir)
        written.append(path)
    return written


def write_calls_evidence(
    calls: list[CallEntry],
    source: SourceInfo,
    out_dir: str,
) -> list[str]:
    """Write call graph evidence, one file per caller module.

    Schema: payload_py_callgraph
      required: [nodes, edges]
      nodes[]: { symbol: str, file?: str }
      edges[]: { from: str, to: str, kind: enum[call,method_call,super_call,callback], edge_id: int, range?: {...} }
    """
    by_module: dict[str, list[CallEntry]] = {}
    for call in calls:
        parts = call.caller.rsplit(".", 1)
        mod = parts[0] if len(parts) > 1 else call.caller
        by_module.setdefault(mod, []).append(call)

    written = []
    for mod, mod_calls in sorted(by_module.items()):
        eid = evidence_id("py.callgraph", mod)

        # Build nodes: unique symbols involved
        node_set: set[str] = set()
        for c in mod_calls:
            node_set.add(c.caller)
            node_set.add(c.callee)
        nodes = [{"symbol": s} for s in sorted(node_set)]

        # Build edges with schema-compliant fields
        edges = []
        for idx, c in enumerate(mod_calls):
            # Map resolution to kind
            kind = _resolution_to_kind(c.resolution)
            edge = {
                "from": c.caller,
                "to": c.callee,
                "kind": kind,
                "edge_id": idx,
            }
            # Add resolution_source if available (H2.9)
            if c.resolution_source:
                edge["resolution_source"] = c.resolution_source
            # Add resolution_detail if available (v0.5.0 trace)
            if c.resolution_detail:
                edge["resolution_detail"] = c.resolution_detail
            # Add range if anchor available
            if c.anchor:
                edge["range"] = {
                    "start_line": c.anchor.line_start,
                    "start_col": 0,
                    "end_line": c.anchor.line_end,
                    "end_col": 0,
                }
            edges.append(edge)

        # Schema: required [nodes, edges], additionalProperties: false
        payload = {
            "nodes": nodes,
            "edges": edges,
        }
        artifact = EvidenceArtifact(
            id=eid,
            type="py.callgraph",
            level=EvidenceLevel.E1,
            source=source,
            payload=payload,
        )
        path = _write_artifact(artifact, out_dir)
        written.append(path)
    return written


def _resolution_to_kind(resolution: str) -> str:
    """Map internal resolution type to schema-allowed call kind."""
    mapping = {
        "qualified": "call",
        "method": "method_call",
        "super": "super_call",
        "self_dispatch": "method_call",
        "cls_dispatch": "method_call",
        "super_dispatch": "super_call",
        "ctor_dispatch": "method_call",
        "local_var_dispatch": "method_call",
        "self_attr_dispatch": "method_call",
        "callback": "callback",
        "unresolved": "call",
    }
    return mapping.get(resolution, "call")


# --- Serialization helpers ---


def _write_artifact(artifact: EvidenceArtifact, out_dir: str) -> str:
    """Serialize an EvidenceArtifact to schema-compliant YAML."""
    os.makedirs(out_dir, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    data = {
        "schema": "cas.evidence.v0.1",
        "id": artifact.id,
        "kind": "evidence",
        "type": artifact.type,
        "created_at": now,
        "created_by": "extractor:py.v0.1",
        "source": {
            "repo": artifact.source.repo,
            "root": artifact.source.root,
            "revision": artifact.source.revision,
        },
        "payload": artifact.payload,
    }

    filename = f"{artifact.id}.yaml"
    filepath = os.path.join(out_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

    return filepath


def _symbol_to_dict(sym: SymbolEntry) -> dict[str, Any]:
    """Convert SymbolEntry to schema-compliant dict.

    Schema allows: qualified, kind, file, params, returns, decorators, range, fingerprint, base_classes
    """
    d: dict[str, Any] = {
        "qualified": sym.qualified_name,
        "kind": sym.kind,
    }
    # file is required by schema
    if sym.anchor:
        d["file"] = sym.anchor.file
        d["range"] = {
            "start_line": sym.anchor.line_start,
            "start_col": 0,
            "end_line": sym.anchor.line_end,
            "end_col": 0,
        }
        if sym.anchor.fingerprint:
            d["fingerprint"] = sym.anchor.fingerprint
    else:
        d["file"] = ""  # required field

    if sym.decorators:
        d["decorators"] = sym.decorators
    if sym.parameters:
        d["params"] = sym.parameters
    if sym.return_annotation:
        d["returns"] = sym.return_annotation
    if sym.base_classes:
        d["base_classes"] = sym.base_classes
    return d


def _import_to_dict(imp: ImportEntry) -> dict[str, Any]:
    """Legacy helper — no longer used in schema-compliant path."""
    return {
        "source": imp.source_module,
        "target": imp.target,
        "is_from_import": imp.is_from_import,
    }


def _call_to_dict(call: CallEntry) -> dict[str, Any]:
    """Legacy helper — no longer used in schema-compliant path."""
    return {
        "caller": call.caller,
        "callee": call.callee,
        "resolution": call.resolution,
    }
