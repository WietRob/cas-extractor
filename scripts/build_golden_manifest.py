#!/usr/bin/env python3
"""
Build golden manifest from baseline YAML files.

Generates manifest.json with:
  - edge_count
  - heuristic distribution
  - normalized edge signatures
"""

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
        if yaml_file.name.endswith(".callgraph.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            for edge in data.get("payload", {}).get("edges", []):
                sig = normalize_edge_signature(edge)
                heuristic = extract_heuristic_from_trace(edge)

                edges.append({
                    "from": sig[0],
                    "to": sig[1],
                    "kind": sig[2],
                    "resolution": sig[3],
                    "heuristic": heuristic,
                })
                heuristic_counts[heuristic] += 1

    return {
        "edge_count": len(edges),
        "heuristics": dict(heuristic_counts),
        "edges": edges,
        "manifest_version": "1.0",
        "generated_by": "build_golden_manifest.py",
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_golden_manifest.py <baseline_dir>")
        sys.exit(1)

    
    baseline_dir = Path(sys.argv[1])

    if not baseline_dir.is_dir():
        print(f"Error: {baseline_dir} is not a directory")
        sys.exit(1)
    
    manifest = build_manifest(baseline_dir)
    
    manifest_path = baseline_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Generated manifest: {manifest_path}")
    print(f"  Edge count: {manifest['edge_count']}")
    print(f"  Heuristics: {manifest['heuristics']}")


if __name__ == "__main__":
    main()
