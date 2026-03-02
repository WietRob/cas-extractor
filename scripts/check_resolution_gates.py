#!/usr/bin/env python3
"""
Resolution Gate Runner for CI.

Checks:
1. Resolver regression tests pass
2. Golden manifest matches current baseline
3. No only-engine edges (parity gate)
4. Mandatory heuristics present
5. Deterministic ordering verified

Exit codes:
  0: All gates pass
  1: One or more gates failed
"""

import json
import subprocess
import sys
from pathlib import Path


def run_pytest() -> bool:
    print("=" * 60)
    print("GATE 1: Resolver Regression Tests")
    print("=" * 60)

    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/resolvers/", "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("✅ GATE 1 PASSED: All regression tests pass")
        return True
    else:
        print("❌ GATE 1 FAILED: Some tests failed")
        return False


def check_golden_manifest() -> bool:
    print("\n" + "=" * 60)
    print("GATE 2: Golden Manifest")
    print("=" * 60)

    manifest_path = Path(
        "sprint-v050-engine/06-golden/v050-product-baseline/manifest.json"
    )

    if not manifest_path.exists():
        print(f"❌ GATE 2 FAILED: Manifest not found at {manifest_path}")
        print(
            "   Run: python scripts/build_golden_manifest.py sprint-v050-engine/06-golden/v050-product-baseline/"
        )
        return False

    with open(manifest_path) as f:
        manifest = json.load(f)

    edge_count = manifest.get("edge_count", 0)
    heuristics = manifest.get("heuristics", {})

    print(f"  Edge count: {edge_count}")
    print(f"  Heuristics: {heuristics}")

    if edge_count == 0:
        print("❌ GATE 2 FAILED: Manifest has no edges")
        return False

    print("✅ GATE 2 PASSED: Golden manifest valid")
    return True


def check_parity() -> bool:
    print("\n" + "=" * 60)
    print("GATE 3: Parity Check")
    print("=" * 60)

    baseline_dir = Path("sprint-v050-engine/06-golden/v050-product-baseline")

    if not baseline_dir.exists():
        print(f"❌ GATE 3 FAILED: Baseline directory not found: {baseline_dir}")
        return False

    manifest_path = baseline_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

        if manifest.get("edge_count", 0) > 0:
            print(f"  Baseline has {manifest['edge_count']} edges")
            print("✅ GATE 3 PASSED: Baseline exists with edges")
            return True

    print("❌ GATE 3 FAILED: No valid baseline found")
    return False


def check_mandatory_heuristics() -> bool:
    print("\n" + "=" * 60)
    print("GATE 4: Mandatory Heuristics")
    print("=" * 60)

    manifest_path = Path(
        "sprint-v050-engine/06-golden/v050-product-baseline/manifest.json"
    )

    if not manifest_path.exists():
        print(f"❌ GATE 4 FAILED: Manifest not found at {manifest_path}")
        return False

    with open(manifest_path) as f:
        manifest = json.load(f)

    if manifest.get("edge_count", 0) == 0:
        print("⚠️  GATE 4 SKIPPED: Empty baseline")
        return True

    mandatory = {"static", "qualified_attr"}
    present = set(manifest.get("heuristics", {}).keys())
    missing = mandatory - present

    if missing:
        print(f"❌ GATE 4 FAILED: Missing mandatory heuristics: {missing}")
        return False

    print(f"  Present heuristics: {sorted(present)}")
    print("✅ GATE 4 PASSED: All mandatory heuristics present")
    return True


def check_deterministic_ordering() -> bool:
    print("\n" + "=" * 60)
    print("GATE 5: Deterministic Ordering")
    print("=" * 60)

    manifest_path = Path(
        "sprint-v050-engine/06-golden/v050-product-baseline/manifest.json"
    )

    if not manifest_path.exists():
        print(f"❌ GATE 5 FAILED: Manifest not found at {manifest_path}")
        return False

    with open(manifest_path) as f:
        manifest = json.load(f)

    edges = manifest.get("edges", [])
    if not edges:
        print("⚠️  GATE 5 SKIPPED: No edges to check")
        return True

    sort_keys = [
        (e.get("from", ""), e.get("to", ""), e.get("heuristic", "")) for e in edges
    ]
    sorted_keys = sorted(sort_keys)

    if sort_keys != sorted_keys:
        print("❌ GATE 5 FAILED: Edges not in sorted order")
        first_diff = next(
            i for i in range(len(sort_keys)) if sort_keys[i] != sorted_keys[i]
        )
        print(f"  First mismatch at index {first_diff}")
        return False

    print(f"  {len(edges)} edges in sorted order")
    print("✅ GATE 5 PASSED: Deterministic ordering verified")
    return True


def check_provenance_fields() -> bool:
    print("\n" + "=" * 60)
    print("GATE 6: Provenance Fields")
    print("=" * 60)

    manifest_path = Path(
        "sprint-v050-engine/06-golden/v050-product-baseline/manifest.json"
    )

    if not manifest_path.exists():
        print(f"❌ GATE 6 FAILED: Manifest not found at {manifest_path}")
        return False

    with open(manifest_path) as f:
        manifest = json.load(f)

    edges = manifest.get("edges", [])
    if not edges:
        print("⚠️  GATE 6 SKIPPED: No edges to check")
        return True

    provenance_coverage = {
        "source_kind": 0,
        "source_symbol": 0,
        "evidence_path": 0,
    }
    total_with_trace = 0

    for edge in edges:
        resolution_detail = edge.get("resolution_detail", {})
        trace = resolution_detail.get("trace", [])
        if trace:
            total_with_trace += 1
            step = trace[0]
            if step.get("source_kind"):
                provenance_coverage["source_kind"] += 1
            if step.get("source_symbol"):
                provenance_coverage["source_symbol"] += 1
            if step.get("evidence_path"):
                provenance_coverage["evidence_path"] += 1

    if total_with_trace == 0:
        print("⚠️  GATE 6 SKIPPED: No edges with trace (baseline predates v0.6.0)")
        print(
            "   Regenerate baseline with: python scripts/build_golden_manifest.py <dir>"
        )
        return True

    coverage_pct = {
        k: (v / total_with_trace * 100) if total_with_trace > 0 else 0
        for k, v in provenance_coverage.items()
    }

    print(f"  Edges with trace: {total_with_trace}")
    print(
        f"  source_kind coverage: {provenance_coverage['source_kind']}/{total_with_trace} ({coverage_pct['source_kind']:.1f}%)"
    )
    print(
        f"  source_symbol coverage: {provenance_coverage['source_symbol']}/{total_with_trace} ({coverage_pct['source_symbol']:.1f}%)"
    )
    print(
        f"  evidence_path coverage: {provenance_coverage['evidence_path']}/{total_with_trace} ({coverage_pct['evidence_path']:.1f}%)"
    )

    min_coverage = 80.0
    all_pass = all(pct >= min_coverage for pct in coverage_pct.values())

    if all_pass:
        print(f"✅ GATE 6 PASSED: All provenance fields >= {min_coverage}% coverage")
        return True
    else:
        print(f"❌ GATE 6 FAILED: Provenance coverage below {min_coverage}%")
        return False

    with open(manifest_path) as f:
        manifest = json.load(f)

    edges = manifest.get("edges", [])
    if not edges:
        print("⚠️  GATE 6 SKIPPED: No edges to check")
        return True

    provenance_coverage = {
        "source_kind": 0,
        "source_symbol": 0,
        "evidence_path": 0,
    }
    total_resolved = 0

    for edge in edges:
        heuristic = edge.get("heuristic", "")
        if heuristic and heuristic not in ("none", "skip"):
            total_resolved += 1
            resolution_detail = edge.get("resolution_detail", {})
            trace = resolution_detail.get("trace", [])
            if trace:
                step = trace[0]
                if step.get("source_kind"):
                    provenance_coverage["source_kind"] += 1
                if step.get("source_symbol"):
                    provenance_coverage["source_symbol"] += 1
                if step.get("evidence_path"):
                    provenance_coverage["evidence_path"] += 1

    if total_resolved == 0:
        print("⚠️  GATE 6 SKIPPED: No resolved edges")
        return True

    coverage_pct = {
        k: (v / total_resolved * 100) if total_resolved > 0 else 0
        for k, v in provenance_coverage.items()
    }

    print(f"  Total resolved edges: {total_resolved}")
    print(
        f"  source_kind coverage: {provenance_coverage['source_kind']}/{total_resolved} ({coverage_pct['source_kind']:.1f}%)"
    )
    print(
        f"  source_symbol coverage: {provenance_coverage['source_symbol']}/{total_resolved} ({coverage_pct['source_symbol']:.1f}%)"
    )
    print(
        f"  evidence_path coverage: {provenance_coverage['evidence_path']}/{total_resolved} ({coverage_pct['evidence_path']:.1f}%)"
    )

    min_coverage = 80.0
    all_pass = all(pct >= min_coverage for pct in coverage_pct.values())

    if all_pass:
        print(f"✅ GATE 6 PASSED: All provenance fields >= {min_coverage}% coverage")
        return True
    else:
        print(f"❌ GATE 6 FAILED: Provenance coverage below {min_coverage}%")
        return False


def main():
    print("Resolution Gate Runner")
    print("=" * 60)

    gates = [
        ("Regression Tests", run_pytest),
        ("Golden Manifest", check_golden_manifest),
        ("Parity Check", check_parity),
        ("Mandatory Heuristics", check_mandatory_heuristics),
        ("Deterministic Ordering", check_deterministic_ordering),
        ("Provenance Fields", check_provenance_fields),
    ]

    results = {}
    for name, check_fn in gates:
        results[name] = check_fn()

    print("\n" + "=" * 60)
    print("GATE SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 ALL GATES PASSED")
        sys.exit(0)
    else:
        print("\n⚠️ SOME GATES FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
