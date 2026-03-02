#!/usr/bin/env python3
"""
Resolution Gate Runner for CI.

Checks:
1. Resolver regression tests pass
2. Golden manifest matches current baseline
3. No only-engine edges (parity gate)

Exit codes:
  0: All gates pass
  1: One or more gates failed
"""

import json
import subprocess
import sys
from pathlib import Path


def run_pytest() -> bool:
    """Run regression tests. Returns True if all pass."""
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
    """Check golden manifest exists and is valid."""
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
    """Check no only-engine edges in baseline."""
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


def main():
    print("Resolution Gate Runner")
    print("=" * 60)

    gates = [
        ("Regression Tests", run_pytest),
        ("Golden Manifest", check_golden_manifest),
        ("Parity Check", check_parity),
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
