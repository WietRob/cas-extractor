#!/usr/bin/env python3
"""
Build golden manifest from baseline YAML files.

Generates manifest.json with:
  - edge_count
  - heuristic distribution
  - normalized edge signatures

Usage:
  python build_golden_manifest.py <baseline_dir>        # Generate manifest
  python build_golden_manifest.py <baseline_dir> --check # Compare to existing
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter
import yaml


def normalize_edge_signature(edge: dict) -> tuple:
    return (
        edge.get("from", ""),
        edge.get("to", ""),
        edge.get("kind", ""),
        edge.get("resolution", ""),
    )


def extract_heuristic_from_trace(edge: dict) -> str:
    trace = edge.get("resolution_detail", {}).get("trace", [])
    if trace:
        for step in trace:
            if step.get("heuristic"):
                return step["heuristic"]
    return edge.get("heuristic", "unresolved")


def build_manifest(baseline_dir: Path) -> dict:
    edges = []
    heuristic_counts: Counter[str] = Counter()

    for yaml_file in baseline_dir.glob("EVID-py.*.yaml"):
        if ".callgraph-" in yaml_file.name:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            for edge in data.get("payload", {}).get("edges", []):
                sig = normalize_edge_signature(edge)
                heuristic = extract_heuristic_from_trace(edge)

                edges.append(
                    {
                        "from": sig[0],
                        "to": sig[1],
                        "kind": sig[2],
                        "resolution": sig[3],
                        "heuristic": heuristic,
                    }
                )
                heuristic_counts[heuristic] += 1

    edges.sort(key=lambda e: (e["from"], e["to"], e["heuristic"]))

    return {
        "edge_count": len(edges),
        "heuristics": dict(heuristic_counts),
        "edges": edges,
        "manifest_version": "1.0",
        "generated_by": "build_golden_manifest.py",
    }


def compare_manifests(expected: dict, actual: dict) -> list[str]:
    diffs = []

    if expected["edge_count"] != actual["edge_count"]:
        diffs.append(
            f"edge_count: expected {expected['edge_count']}, got {actual['edge_count']}"
        )

    exp_h = expected.get("heuristics", {})
    act_h = actual.get("heuristics", {})
    if exp_h != act_h:
        diffs.append(f"heuristics: expected {exp_h}, got {act_h}")

    exp_edges = {
        (e["from"], e["to"], e["heuristic"]) for e in expected.get("edges", [])
    }
    act_edges = {(e["from"], e["to"], e["heuristic"]) for e in actual.get("edges", [])}

    missing = exp_edges - act_edges
    extra = act_edges - exp_edges

    if missing:
        diffs.append(f"missing edges: {sorted(missing)[:5]}...")
    if extra:
        diffs.append(f"extra edges: {sorted(extra)[:5]}...")

    return diffs


def main():
    parser = argparse.ArgumentParser(description="Build or check golden manifest")
    parser.add_argument("baseline_dir", type=Path, help="Directory with YAML files")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated manifest to existing (exit 1 on diff)",
    )
    args = parser.parse_args()

    baseline_dir = args.baseline_dir

    if not baseline_dir.is_dir():
        print(f"Error: {baseline_dir} is not a directory")
        sys.exit(1)

    manifest = build_manifest(baseline_dir)

    if args.check:
        manifest_path = baseline_dir / "manifest.json"
        if not manifest_path.exists():
            print(f"Error: {manifest_path} does not exist")
            sys.exit(1)

        with open(manifest_path) as f:
            expected = json.load(f)

        diffs = compare_manifests(expected, manifest)
        if diffs:
            print(f"Manifest mismatch in {baseline_dir}:")
            for d in diffs:
                print(f"  - {d}")
            sys.exit(1)

        print(f"OK: {baseline_dir} manifest matches")
        print(f"  Edge count: {manifest['edge_count']}")
        print(f"  Heuristics: {manifest['heuristics']}")
    else:
        manifest_path = baseline_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"Generated manifest: {manifest_path}")
        print(f"  Edge count: {manifest['edge_count']}")
        print(f"  Heuristics: {manifest['heuristics']}")


if __name__ == "__main__":
    main()
