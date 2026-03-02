#!/usr/bin/env python3
"""
extract_python.py — CAS Python Evidence Extractor CLI

Usage:
    python extract_python.py \
        --repo-root . \
        --repo-name repo://main \
        --revision git:abcd1234 \
        --out ./artifacts/evidence/

Outputs:
    EVID-py-symbols-*.yaml
    EVID-py-importgraph-*.yaml
    EVID-py-callgraph-*.yaml
"""

import argparse
import os
import sys
from datetime import datetime, timezone

from cas_extractor.extractors.python_symbols import extract_symbols
from cas_extractor.extractors.python_imports import extract_imports
from cas_extractor.extractors.python_calls import extract_calls
from cas_extractor.models.evidence import SourceInfo
from cas_extractor.writers.evidence_writer import (
    write_symbols_evidence,
    write_imports_evidence,
    write_calls_evidence,
)


def _parse_bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes", "on")


def _parse_int(value: str) -> int:
    return int(value)


def main():
    parser = argparse.ArgumentParser(description="CAS Python Evidence Extractor")
    parser.add_argument("--repo-root", required=True, help="Path to repository root")
    parser.add_argument(
        "--repo-name", required=True, help="Repo identifier (e.g. repo://main)"
    )
    parser.add_argument(
        "--revision", required=True, help="Revision identifier (e.g. git:abcd1234)"
    )
    parser.add_argument(
        "--out", required=True, help="Output directory for evidence artifacts"
    )
    parser.add_argument(
        "--skip-calls", action="store_true", help="Skip callgraph extraction"
    )
    parser.add_argument(
        "--emit-unresolved-self-attr",
        type=_parse_bool,
        default=_parse_bool(os.environ.get("CAS_EMIT_UNRESOLVED_SELF_ATTR", "true")),
        help="Emit unresolved self.attr.method() calls (default: true). "
        "Set CAS_EMIT_UNRESOLVED_SELF_ATTR env var or use --emit-unresolved-self-attr false",
    )
    parser.add_argument(
        "--enable-h25-self-attr-noninit",
        type=_parse_bool,
        default=_parse_bool(
            os.environ.get("CAS_ENABLE_H25_SELF_ATTR_NONINIT", "false")
        ),
        help="Enable H2.5: resolve self.attr.method() where self.attr = Class() in non-__init__ methods (default: false). "
        "Set CAS_ENABLE_H25_SELF_ATTR_NONINIT env var or use --enable-h25-self-attr-noninit true",
    )
    parser.add_argument(
        "--enable-h26-self-attr-intermethod",
        type=_parse_bool,
        default=_parse_bool(
            os.environ.get("CAS_ENABLE_H26_SELF_ATTR_INTERMETHOD", "false")
        ),
        help="Enable H2.6: resolve self.attr.method() where self.attr is assigned in a helper method called via self.helper() (default: false). "
        "Set CAS_ENABLE_H26_SELF_ATTR_INTERMETHOD env var or use --enable-h26-self-attr-intermethod true",
    )
    parser.add_argument(
        "--h26-max-helper-depth",
        type=_parse_int,
        default=_parse_int(os.environ.get("CAS_H26_MAX_HELPER_DEPTH", "2")),
        help="Maximum propagation depth for H2.6 inter-method analysis (default: 2). "
        "Only effective when --enable-h26-self-attr-intermethod is true. "
        "Set CAS_H26_MAX_HELPER_DEPTH env var or use --h26-max-helper-depth N",
    )
    parser.add_argument(
        "--enable-h27-self-attr-transitive",
        type=_parse_bool,
        default=_parse_bool(
            os.environ.get("CAS_ENABLE_H27_SELF_ATTR_TRANSITIVE", "false")
        ),
        help="Enable H2.7: resolve self.attr.method() where self.attr is assigned in a multi-hop helper chain (default: false). "
        "Set CAS_ENABLE_H27_SELF_ATTR_TRANSITIVE env var or use --enable-h27-self-attr-transitive true",
    )
    parser.add_argument(
        "--h27-max-chain-depth",
        type=_parse_int,
        default=_parse_int(os.environ.get("CAS_H27_MAX_CHAIN_DEPTH", "2")),
        help="Maximum helper chain depth for H2.7 transitive analysis (default: 2). "
        "Only effective when --enable-h27-self-attr-transitive is true. "
        "Set CAS_H27_MAX_CHAIN_DEPTH env var or use --h27-max-chain-depth N",
    )
    parser.add_argument(
        "--enable-h28-factory-return",
        type=_parse_bool,
        default=_parse_bool(os.environ.get("CAS_ENABLE_H28_FACTORY_RETURN", "false")),
        help="Enable H2.8: infer return types from factory functions that directly return ClassName() (default: false). "
        "Set CAS_ENABLE_H28_FACTORY_RETURN env var or use --enable-h28-factory-return true",
    )
    parser.add_argument(
        "--h28-max-factory-depth",
        type=_parse_int,
        default=_parse_int(os.environ.get("CAS_H28_MAX_FACTORY_DEPTH", "1")),
        help="Maximum factory chain depth for H2.8 inference (default: 1). "
        "Only effective when --enable-h28-factory-return is true. "
        "Set CAS_H28_MAX_FACTORY_DEPTH env var or use --h28-max-factory-depth N",
    )
    parser.add_argument(
        "--enable-h29-resolution-metadata",
        type=_parse_bool,
        default=_parse_bool(
            os.environ.get("CAS_ENABLE_H29_RESOLUTION_METADATA", "false")
        ),
        help="Enable H2.9: add resolution metadata to self.attr.method() calls "
        "showing which heuristic resolved the call and source location (default: false). "
        "Set CAS_ENABLE_H29_RESOLUTION_METADATA env var or use --enable-h29-resolution-metadata true",
    )
    parser.add_argument(
        "--enable-v050-resolution-engine",
        type=_parse_bool,
        default=_parse_bool(
            os.environ.get("CAS_ENABLE_V050_RESOLUTION_ENGINE", "false")
        ),
        help="Enable v0.5.0: use ResolutionEngine instead of legacy resolver (default: false). "
        "Set CAS_ENABLE_V050_RESOLUTION_ENGINE env var or use --enable-v050-resolution-engine true",
    )
    parser.add_argument(
        "--v050-emit-resolution-trace",
        type=_parse_bool,
        default=_parse_bool(os.environ.get("CAS_V050_EMIT_RESOLUTION_TRACE", "false")),
        help="Enable v0.5.0: emit resolution trace for debugging (default: false). "
        "Only effective when --enable-v050-resolution-engine is true. "
        "Set CAS_V050_EMIT_RESOLUTION_TRACE env var or use --v050-emit-resolution-trace true",
    )
    args = parser.parse_args()

    source = SourceInfo(
        repo=args.repo_name,
        root=args.repo_root,
        revision=args.revision,
        collected_at=datetime.now(timezone.utc).isoformat(),
    )

    print(f"[extract] Scanning {args.repo_root} ...")

    # 1. Symbols (E0)
    print("[extract] Extracting symbols ...")
    symbols = list(extract_symbols(args.repo_root))
    print(f"  → {len(symbols)} symbols found")
    files = write_symbols_evidence(symbols, source, args.out)
    print(f"  → {len(files)} evidence files written")

    # 2. Imports (E0)
    print("[extract] Extracting import graph ...")
    imports = list(extract_imports(args.repo_root))
    print(f"  → {len(imports)} import edges found")
    files = write_imports_evidence(imports, source, args.out)
    print(f"  → {len(files)} evidence files written")

    # 3. Calls (E1) — optional
    if not args.skip_calls:
        print("[extract] Extracting call graph (conservative) ...")
        calls = list(
            extract_calls(
                args.repo_root,
                emit_unresolved_self_attr=args.emit_unresolved_self_attr,
                enable_h25_self_attr_noninit=args.enable_h25_self_attr_noninit,
                enable_h26_self_attr_intermethod=args.enable_h26_self_attr_intermethod,
                h26_max_helper_depth=args.h26_max_helper_depth,
                enable_h27_self_attr_transitive=args.enable_h27_self_attr_transitive,
                h27_max_chain_depth=args.h27_max_chain_depth,
                enable_h28_factory_return=args.enable_h28_factory_return,
                h28_max_factory_depth=args.h28_max_factory_depth,
                enable_h29_resolution_metadata=args.enable_h29_resolution_metadata,
                enable_v050_resolution_engine=args.enable_v050_resolution_engine,
                v050_emit_resolution_trace=args.v050_emit_resolution_trace,
            )
        )
        print(f"  → {len(calls)} call edges found")
        files = write_calls_evidence(calls, source, args.out)
        print(f"  → {len(files)} evidence files written")
    else:
        print("[extract] Skipping callgraph (--skip-calls)")

    print("[extract] Done.")


if __name__ == "__main__":
    main()
