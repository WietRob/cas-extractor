#!/usr/bin/env python3
import sys
import yaml
from pathlib import Path
from collections import Counter


def load_edges(out_dir):
    edges = []
    out_path = Path(out_dir)
    for yaml_file in out_path.rglob("*.yaml"):
        if "callgraph" in yaml_file.name:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                payload = data.get("payload", {})
                edges.extend(payload.get("edges", []))
    return edges


def normalize_edge(e):
    return (e.get("from"), e.get("to"), e.get("kind"), e.get("resolution"))


def classify_diff(legacy_counter, engine_counter):
    exact = []
    count_mismatch = []

    legacy_keys = set(legacy_counter.keys())
    engine_keys = set(engine_counter.keys())
    common_keys = legacy_keys & engine_keys

    for key in common_keys:
        l_count = legacy_counter[key]
        e_count = engine_counter[key]
        if l_count == e_count:
            exact.append((key, l_count))
        else:
            count_mismatch.append((key, l_count, e_count))

    only_legacy = [(k, legacy_counter[k]) for k in sorted(legacy_keys - engine_keys)]
    only_engine = [(k, engine_counter[k]) for k in sorted(engine_keys - legacy_keys)]

    return {
        "exact": exact,
        "count_mismatch": count_mismatch,
        "only_legacy": only_legacy,
        "only_engine": only_engine,
    }


def print_diff_report(diff):
    print("\n" + "=" * 60)
    print("PARITY DIFF REPORT")
    print("=" * 60)

    exact_count = sum(c for _, c in diff["exact"])
    print(
        f"\n[EXACT] {len(diff['exact'])} unique edges, {exact_count} total edges match exactly"
    )

    if diff["count_mismatch"]:
        print(
            f"\n[COUNT MISMATCH] {len(diff['count_mismatch'])} edges with different counts:"
        )
        for key, l_count, e_count in sorted(diff["count_mismatch"])[:15]:
            print(
                f"  {key}: legacy={l_count}, engine={e_count}, delta={e_count - l_count:+d}"
            )
        if len(diff["count_mismatch"]) > 15:
            print(f"  ... and {len(diff['count_mismatch']) - 15} more")

    l_only_count = sum(c for _, c in diff["only_legacy"])
    e_only_count = sum(c for _, c in diff["only_engine"])

    if diff["only_legacy"]:
        print(
            f"\n[ONLY LEGACY] {len(diff['only_legacy'])} unique edges, {l_only_count} total edges:"
        )
        for key, count in sorted(diff["only_legacy"])[:15]:
            print(f"  {count}x {key}")
        if len(diff["only_legacy"]) > 15:
            print(f"  ... and {len(diff['only_legacy']) - 15} more unique edges")

    if diff["only_engine"]:
        print(
            f"\n[ONLY ENGINE] {len(diff['only_engine'])} unique edges, {e_only_count} total edges:"
        )
        for key, count in sorted(diff["only_engine"])[:15]:
            print(f"  {count}x {key}")
        if len(diff["only_engine"]) > 15:
            print(f"  ... and {len(diff['only_engine']) - 15} more unique edges")

    print("\n" + "=" * 60)


def compare(legacy_dir, engine_dir):
    legacy_edges = load_edges(legacy_dir)
    engine_edges = load_edges(engine_dir)

    legacy_normalized = [normalize_edge(e) for e in legacy_edges]
    engine_normalized = [normalize_edge(e) for e in engine_edges]

    legacy_counter = Counter(legacy_normalized)
    engine_counter = Counter(engine_normalized)

    print(f"Legacy edges (total): {len(legacy_edges)}")
    print(f"Engine edges (total): {len(engine_edges)}")
    print(f"Delta: {len(engine_edges) - len(legacy_edges):+d}")

    diff = classify_diff(legacy_counter, engine_counter)

    print_diff_report(diff)

    exact_count = sum(c for _, c in diff["exact"])
    mismatch_count = abs(sum(e - l for _, l, e in diff["count_mismatch"]))
    l_only_count = sum(c for _, c in diff["only_legacy"])
    e_only_count = sum(c for _, c in diff["only_engine"])

    total_diff = mismatch_count + l_only_count + e_only_count

    if total_diff == 0:
        print("\n✅ PARITY: Exact match!")
        return True
    else:
        print(f"\n❌ PARITY FAIL: {total_diff} edges differ")
        print(f"   - count mismatch: {mismatch_count}")
        print(f"   - only legacy: {l_only_count}")
        print(f"   - only engine: {e_only_count}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: compare_results.py <legacy_dir> <engine_dir>")
        sys.exit(1)

    parity = compare(sys.argv[1], sys.argv[2])
    sys.exit(0 if parity else 1)
