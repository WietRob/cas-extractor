"""
Artifact Generator — transforms Evidence into Entities, Relations, and Issues.

Schema-compliant output for:
  - cas.entity.v0.1
  - cas.relation.v0.1
  - cas.issue.v0.1
"""
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cas_extractor.utils.ids import entity_id, relation_id, issue_id, reset_counters


# --- Standard library detection ---

_STDLIB_MODULES = frozenset("""
__future__ abc aifc argparse array ast asynchat asyncio asyncore atexit audioop
base64 bdb binascii binhex bisect builtins bz2 calendar cgi cgitb chunk cmath cmd
code codecs codeop collections colorsys compileall concurrent configparser contextlib
contextvars copy copyreg cProfile crypt csv ctypes curses dataclasses datetime dbm
decimal difflib dis distutils doctest email encodings enum errno faulthandler fcntl
filecmp fileinput fnmatch formatter fractions ftplib functools gc getopt getpass gettext
glob grp gzip hashlib heapq hmac html http idlelib imaplib imghdr imp importlib inspect
io ipaddress itertools json keyword lib2to3 linecache locale logging lzma mailbox mailcap
marshal math mimetypes mmap modulefinder multiprocessing netrc nis nntplib numbers
operator optparse os ossaudiodev pathlib pdb pickle pickletools pipes pkgutil platform
plistlib poplib posix posixpath pprint profile pstats pty pwd py_compile pyclbr pydoc
queue quopri random re readline reprlib resource rlcompleter runpy sched secrets select
selectors shelve shlex shutil signal site smtpd smtplib sndhdr socket socketserver
sqlite3 sre_compile sre_constants sre_parse ssl stat statistics string stringprep struct
subprocess sunau symtable sys sysconfig syslog tabnanny tarfile telnetlib tempfile termios
test textwrap threading time timeit tkinter token tokenize tomllib trace traceback
tracemalloc tty turtle turtledemo types typing unicodedata unittest urllib uu uuid venv
warnings wave weakref webbrowser winreg winsound wsgiref xdrlib xml xmlrpc zipapp
zipfile zipimport zlib _thread _io _collections_abc _sitebuiltins typing_extensions
""".split())


_PARAM_PATTERNS = re.compile(
    r"^\s*(:param\s|:type\s|:returns?:|:rtype:|Args:|Returns:|Raises:|Attributes:|Parameters:|Keyword Args:)",
    re.MULTILINE,
)


def _is_param_only_docstring(docstring: str) -> bool:
    lines = [l.strip() for l in docstring.strip().splitlines() if l.strip()]
    if len(lines) <= 1:
        return False
    param_lines = sum(1 for l in lines if _PARAM_PATTERNS.match(l))
    return param_lines / len(lines) > 0.5


def _classify_module(module_name: str, known_internal_prefixes: set[str]) -> str:
    top = module_name.split(".")[0]
    if top in _STDLIB_MODULES:
        return "stdlib"
    if top in known_internal_prefixes:
        return "internal"
    return "third_party"


def generate_from_evidence(
    evidence_dir: str,
    out_entities: str,
    out_relations: str,
    out_issues: str,
) -> dict[str, Any]:
    """Read evidence YAML files and generate schema-compliant artifacts."""
    os.makedirs(out_entities, exist_ok=True)
    os.makedirs(out_relations, exist_ok=True)
    os.makedirs(out_issues, exist_ok=True)

    # Reset sequential ID counters
    reset_counters()

    now = datetime.now(timezone.utc).isoformat()

    evidence_files = sorted(Path(evidence_dir).glob("*.yaml"))
    evidence_data = []
    for ef in evidence_files:
        with open(ef, "r") as f:
            evidence_data.append(yaml.safe_load(f))

    # Collect all symbols, imports, calls
    all_symbols = []
    all_imports = []
    all_calls_resolved = []
    all_calls_unresolved = []

    for ev in evidence_data:
        ev_type = ev.get("type", "")
        payload = ev.get("payload", {})
        source = ev.get("source", {})

        if ev_type == "py.symbols":
            for sym in payload.get("symbols", []):
                sym["_source"] = source
                sym["_evidence_id"] = ev["id"]
                all_symbols.append(sym)

        elif ev_type == "py.importgraph":
            # Schema: payload.imports[].{from, imports[]}
            # Flatten to internal format: {source, target, _evidence_id}
            for imp_entry in payload.get("imports", []):
                src_mod = imp_entry.get("from", "")
                for tgt in imp_entry.get("imports", []):
                    all_imports.append({
                        "source": src_mod,
                        "target": tgt,
                        "_evidence_id": ev["id"],
                    })

        elif ev_type == "py.callgraph":
            # Schema: payload.edges[].{from, to, kind, edge_id}
            # Map to internal format: {caller, callee, resolution, _evidence_id}
            for edge in payload.get("edges", []):
                call_data = {
                    "caller": edge.get("from", ""),
                    "callee": edge.get("to", ""),
                    "resolution": edge.get("kind", "call"),
                    "_evidence_id": ev["id"],
                }
                all_calls_resolved.append(call_data)
            # No separate unresolved array in new schema — all edges are in one list

    # Determine internal module prefixes
    known_internal_prefixes = set()
    for sym in all_symbols:
        if sym["kind"] == "module":
            top = sym.get("qualified", sym.get("qualified_name", "")).split(".")[0]
            known_internal_prefixes.add(top)

    # Resolution type breakdown
    resolution_counts: dict[str, int] = {}
    for call in all_calls_resolved:
        rt = call.get("resolution", "unknown")
        resolution_counts[rt] = resolution_counts.get(rt, 0) + 1
    # all_calls_unresolved is now empty (schema puts all edges in one array)
    for call in all_calls_unresolved:
        resolution_counts["unresolved"] = resolution_counts.get("unresolved", 0) + 1

    counts = {
        "entities": 0, "relations": 0, "issues": 0,
        "issues_by_type": {},
        "claims_by_level": {},
        "claims_filtered": 0,
        "calls_resolved": len(all_calls_resolved),
        "calls_unresolved": len(all_calls_unresolved),
        "resolution_types": resolution_counts,
        "imports_internal": 0,
        "imports_external": 0,
        "orphan_external": 0,
        "orphan_internal": 0,
    }

    claim_counter = 0

    # --- Generate Entities ---
    known_entity_ids = set()
    symbol_by_qname: dict[str, dict] = {}

    for sym in all_symbols:
        qname = sym.get("qualified", sym.get("qualified_name", ""))
        sym_kind = sym["kind"]
        eid = entity_id(sym_kind, qname)
        known_entity_ids.add(eid)
        symbol_by_qname[qname] = sym

        # Map symbol kind to entity type enum
        type_map = {
            "function": "py.function",
            "method": "py.function",
            "class": "py.class",
            "module": "py.module",
        }
        etype = type_map.get(sym_kind, "py.function")

        # Build source block from evidence source
        ev_source = sym.get("_source", {})
        source_block = {
            "repo": ev_source.get("repo", "repo://unknown"),
            "root": ev_source.get("root", "/"),
            "revision": ev_source.get("revision", "unknown"),
        }
        # Add file if available
        sym_file = sym.get("file")
        if sym_file:
            source_block["file"] = sym_file

        # Build anchors
        anchors = []
        anchors.append({
            "type": "symbol",
            "value": qname,
        })
        fp = sym.get("fingerprint")
        if fp:
            anchors.append({
                "type": "fingerprint",
                "value": fp,
                "algo": "sha256",
            })

        # Build evidence_ref for this entity
        evid_ref = sym["_evidence_id"]

        entity = {
            "schema": "cas.entity.v0.1",
            "id": eid,
            "kind": "entity",
            "type": etype,
            "name": qname.split(".")[-1],
            "status": "draft",
            "created_at": now,
            "created_by": "extractor:py.v0.1",
            "source": source_block,
            "anchors": anchors,
            "claims": [],
            "relations": [],
        }

        # Namespace
        if "." in qname:
            entity["namespace"] = qname.rsplit(".", 1)[0]

        # Conservative claim: purpose from docstring
        if sym.get("docstring"):
            docstring = sym["docstring"]
            sym_name = qname.split(".")[-1]

            if sym_name == "__init__" or _is_param_only_docstring(docstring):
                counts["claims_filtered"] += 1
            else:
                claim_counter += 1
                claim_id = f"CLM-{claim_counter:03d}"
                entity["claims"].append({
                    "id": claim_id,
                    "kind": "purpose",
                    "statement": docstring.split("\n")[0].strip(),
                    "confidence": {
                        "level": "E2",
                        "direction": "provisional",
                    },
                    "evidence": [evid_ref],
                })
                counts["claims_by_level"]["E2"] = counts["claims_by_level"].get("E2", 0) + 1

        _write_yaml(entity, os.path.join(out_entities, f"{eid}.yaml"))
        counts["entities"] += 1

    # --- Generate Relations ---

    # Contains relations
    for sym in all_symbols:
        sym_kind = sym["kind"]
        qname = sym.get("qualified", sym.get("qualified_name", ""))
        if sym_kind in ("function", "method", "class"):
            parts = qname.rsplit(".", 1)
            if len(parts) > 1:
                parent_qname = parts[0]
                parent_sym = symbol_by_qname.get(parent_qname)
                if parent_sym and parent_sym["kind"] == "class":
                    parent_eid = entity_id("class", parent_qname)
                else:
                    parent_eid = entity_id("module", parent_qname)
                child_eid = entity_id(sym_kind, qname)

                rid = relation_id("contains", parent_eid, child_eid)
                relation = {
                    "schema": "cas.relation.v0.1",
                    "id": rid,
                    "kind": "relation",
                    "type": "contains",
                    "from": parent_eid,
                    "to": child_eid,
                    "confidence": {"level": "E0", "direction": "confirmed"},
                    "evidence": [sym["_evidence_id"]],
                    "created_at": now,
                    "created_by": "extractor:py.v0.1",
                }
                _write_yaml(relation, os.path.join(out_relations, f"{rid}.yaml"))
                counts["relations"] += 1

    # Import relations
    seen_import_rels = set()
    for imp in all_imports:
        target_top = imp["target"].split(".")[0]
        classification = _classify_module(imp["target"], known_internal_prefixes)

        if classification == "internal":
            counts["imports_internal"] += 1
        else:
            counts["imports_external"] += 1

        src_eid = entity_id("module", imp["source"])
        tgt_eid = entity_id("module", target_top)

        # Dedup key (not the sequential ID)
        dedup_key = f"imports-{src_eid}-{tgt_eid}"
        if dedup_key not in seen_import_rels:
            seen_import_rels.add(dedup_key)
            rid = relation_id("imports", src_eid, tgt_eid)
            relation = {
                "schema": "cas.relation.v0.1",
                "id": rid,
                "kind": "relation",
                "type": "imports",
                "from": src_eid,
                "to": tgt_eid,
                "confidence": {"level": "E0", "direction": "confirmed"},
                "evidence": [imp["_evidence_id"]],
                "created_at": now,
                "created_by": "extractor:py.v0.1",
            }
            _write_yaml(relation, os.path.join(out_relations, f"{rid}.yaml"))
            counts["relations"] += 1

    # Call relations
    seen_call_rels = set()
    for call in all_calls_resolved:
        caller_eid = entity_id("function", call["caller"])
        callee_eid = entity_id("function", call["callee"])
        dedup_key = f"calls-{caller_eid}-{callee_eid}"
        if dedup_key not in seen_call_rels:
            seen_call_rels.add(dedup_key)
            rid = relation_id("calls", caller_eid, callee_eid)
            relation = {
                "schema": "cas.relation.v0.1",
                "id": rid,
                "kind": "relation",
                "type": "calls",
                "from": caller_eid,
                "to": callee_eid,
                "confidence": {"level": "E1", "direction": "confirmed"},
                "evidence": [call["_evidence_id"]],
                "created_at": now,
                "created_by": "extractor:py.v0.1",
            }
            _write_yaml(relation, os.path.join(out_relations, f"{rid}.yaml"))
            counts["relations"] += 1

    # --- Generate Issues ---
    # Issue types in schema enum: ambiguous, unproven, conflict, orphan, schema_error

    # Unresolved calls → type: "ambiguous"
    seen_issues = set()
    for call in all_calls_unresolved:
        caller_eid = entity_id("function", call["caller"])
        dedup_key = f"ambiguous-{caller_eid}-{call['callee']}"
        if dedup_key not in seen_issues:
            seen_issues.add(dedup_key)
            iid = issue_id("ambiguous", caller_eid)
            issue = {
                "schema": "cas.issue.v0.1",
                "id": iid,
                "kind": "issue",
                "type": "ambiguous",
                "applies_to": [caller_eid],
                "summary": f"Unresolved call to \'{call['callee']}\' from \'{call['caller']}\'",
                "severity": "info",
                "created_by": "extractor:py.v0.1",
                "created_at": now,
                "evidence": [call["_evidence_id"]],
            }
            _write_yaml(issue, os.path.join(out_issues, f"{iid}.yaml"))
            counts["issues"] += 1
            counts["issues_by_type"]["ambiguous"] = counts["issues_by_type"].get("ambiguous", 0) + 1

    # Orphan targets
    for imp in all_imports:
        target_top = imp["target"].split(".")[0]
        tgt_eid = entity_id("module", target_top)

        if tgt_eid not in known_entity_ids:
            classification = _classify_module(imp["target"], known_internal_prefixes)

            if classification in ("stdlib", "third_party"):
                severity = "info"
                counts["orphan_external"] += 1
            else:
                severity = "warn"
                counts["orphan_internal"] += 1

            dedup_key = f"orphan-{tgt_eid}"
            if dedup_key not in seen_issues:
                seen_issues.add(dedup_key)
                iid = issue_id("orphan", tgt_eid)
                issue = {
                    "schema": "cas.issue.v0.1",
                    "id": iid,
                    "kind": "issue",
                    "type": "orphan",
                    "applies_to": [tgt_eid],
                    "summary": f"Import target \'{target_top}\' is {classification} (not in extracted entities)",
                    "severity": severity,
                    "created_by": "extractor:py.v0.1",
                    "created_at": now,
                    "evidence": [imp["_evidence_id"]],
                }
                _write_yaml(issue, os.path.join(out_issues, f"{iid}.yaml"))
                counts["issues"] += 1
                counts["issues_by_type"]["orphan"] = counts["issues_by_type"].get("orphan", 0) + 1

    return counts


def _write_yaml(data: dict, filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
