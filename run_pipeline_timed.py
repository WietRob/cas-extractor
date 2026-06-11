#!/usr/bin/env python3
"""
Instrumented Pipeline Runner v2 — CAS Extractor v0.2
Runs each stage separately with timing, artifact counts, and JSON export.

Usage:
    python run_pipeline_timed.py <repo_path> [--output-dir cas_output] [--schemas-dir schemas]

Outputs:
    - Console: Markdown timing table + bottleneck identification
    - pipeline_timing.json: Machine-readable stage data (post this for diagnosis)
"""

import argparse
import sys
import subprocess
import os
import time
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone


def count_artifacts(output_dir: Path) -> dict:
    """Count artifacts by type in the output directory."""
    counts = Counter()
    if not output_dir.exists():
        return dict(counts)
    for yaml_file in output_dir.rglob("*.yaml"):
        name = yaml_file.stem
        if name.startswith("ev-"):
            counts["evidence"] += 1
        elif name.startswith("ent-"):
            counts["entity"] += 1
        elif name.startswith("rel-"):
            counts["relation"] += 1
        elif name.startswith("iss-"):
            counts["issue"] += 1
        else:
            counts["other"] += 1
    counts["total_files"] = sum(counts.values())
    return dict(counts)


def count_files(directory: Path) -> int:
    """Count total YAML files in a directory."""
    if not directory.exists():
        return 0
    return len(list(directory.rglob("*.yaml")))


def run_stage(label: str, cmd: list[str], cwd: str = ".") -> tuple[float, int, str]:
    """Run a subprocess, return (elapsed_seconds, return_code, stderr_tail)."""
    print(f"\n{'='*60}")
    print(f"▶ STAGE: {label}")
    print(f"  CMD: {' '.join(cmd)}")
    print(f"{'='*60}")

    start = time.monotonic()
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    elapsed = time.monotonic() - start

    # Print stdout
    if result.stdout:
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)

    # Capture stderr tail for diagnostics
    stderr_tail = ""
    if result.stderr:
        stderr_tail = result.stderr[-500:]
        if result.returncode != 0:
            print(f"  STDERR (tail): {stderr_tail}")

    status = "✅" if result.returncode == 0 else "❌"
    print(f"\n  {status} {label}: {elapsed:.3f}s (exit={result.returncode})")
    return elapsed, result.returncode, stderr_tail


def main():
    parser = argparse.ArgumentParser(description="Instrumented CAS Pipeline Runner v2")
    parser.add_argument("repo_path", help="Path to the repository to analyze")
    parser.add_argument("--output-dir", default="cas_output", help="Output directory")
    parser.add_argument("--schemas-dir", default="schemas", help="Schemas directory")
    parser.add_argument("--rules-file", default="rules/validator_rules.v0.1.yaml",
                        help="Validator rules file")
    parser.add_argument("--skip-validate", action="store_true",
                        help="Skip validation stages")
    parser.add_argument("--skip-report", action="store_true",
                        help="Skip report generation")
    parser.add_argument("--timing-output", default="pipeline_timing.json",
                        help="Path for JSON timing export")
    args = parser.parse_args()

    repo = os.path.abspath(args.repo_path)
    out = args.output_dir
    schemas = args.schemas_dir
    rules = args.rules_file

    evidence_dir = os.path.join(out, "evidence")
    artifacts_dir = os.path.join(out, "artifacts")

    stages = []  # ordered list of stage results
    wall_start = time.monotonic()

    def record(name, elapsed, rc, counts=None, stderr_tail=""):
        stages.append({
            "name": name,
            "elapsed_s": round(elapsed, 3),
            "exit_code": rc,
            "counts": counts or {},
            "stderr_tail": stderr_tail if rc != 0 else "",
        })

    # ── Stage 1: Extraction ──────────────────────────────────
    elapsed, rc, stderr = run_stage("extraction", [
        sys.executable, "extract_python.py", repo,
        "--output-dir", evidence_dir,
    ])
    ev_counts = count_artifacts(Path(evidence_dir))
    record("extraction", elapsed, rc, ev_counts, stderr)
    print(f"  📦 Evidence: {ev_counts}")

    if rc != 0:
        print("\n⛔ Extraction failed. Aborting.")
        export_and_report(stages, wall_start, args.timing_output, repo)
        sys.exit(1)

    # ── Stage 2: Artifact Generation ─────────────────────────
    elapsed, rc, stderr = run_stage("generate_artifacts", [
        sys.executable, "generate_artifacts.py", evidence_dir,
        "--output-dir", artifacts_dir,
    ])
    art_counts = count_artifacts(Path(artifacts_dir))
    record("generate_artifacts", elapsed, rc, art_counts, stderr)
    print(f"  📦 Artifacts: {art_counts}")

    if rc != 0:
        print("\n⛔ Generation failed. Aborting.")
        export_and_report(stages, wall_start, args.timing_output, repo)
        sys.exit(1)

    # ── Stage 3+4: Validation ────────────────────────────────
    if not args.skip_validate:
        ev_file_count = count_files(Path(evidence_dir))
        art_file_count = count_files(Path(artifacts_dir))

        # Schema validate evidence
        elapsed, rc, stderr = run_stage("schema_validate_evidence", [
            sys.executable, "validate.py", evidence_dir,
            "--schemas-dir", schemas,
            "--mode", "structural",
        ])
        record("schema_validate_evidence", elapsed, rc,
               {"files_validated": ev_file_count}, stderr)

        # Schema validate artifacts
        elapsed, rc, stderr = run_stage("schema_validate_artifacts", [
            sys.executable, "validate.py", artifacts_dir,
            "--schemas-dir", schemas,
            "--mode", "structural",
        ])
        record("schema_validate_artifacts", elapsed, rc,
               {"files_validated": art_file_count}, stderr)

        # Semantic validation
        all_dirs = f"{evidence_dir},{artifacts_dir}"
        total_files = ev_file_count + art_file_count
        elapsed, rc, stderr = run_stage("semantic_validate", [
            sys.executable, "validate.py", all_dirs,
            "--schemas-dir", schemas,
            "--rules-file", rules,
            "--mode", "semantic",
        ])
        record("semantic_validate", elapsed, rc,
               {"files_validated": total_files}, stderr)

    # ── Stage 5: Report ──────────────────────────────────────
    if not args.skip_report:
        elapsed, rc, stderr = run_stage("report", [
            sys.executable, "-c",
            "from pathlib import Path; "
            f"arts = list(Path('{artifacts_dir}').rglob('*.yaml')); "
            f"evs = list(Path('{evidence_dir}').rglob('*.yaml')); "
            f"print(f'Report: {{len(evs)}} evidence, {{len(arts)}} artifacts')",
        ])
        record("report", elapsed, rc, stderr_tail=stderr)

    # ── Final ────────────────────────────────────────────────
    export_and_report(stages, wall_start, args.timing_output, repo)


def export_and_report(stages, wall_start, timing_output, repo):
    wall_total = round(time.monotonic() - wall_start, 3)

    # ── JSON Export ──────────────────────────────────────────
    timing_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "wall_total_s": wall_total,
        "stages": stages,
    }

    # Add diagnosis hints
    if stages:
        slowest = max(stages, key=lambda s: s["elapsed_s"])
        timing_data["bottleneck"] = {
            "stage": slowest["name"],
            "elapsed_s": slowest["elapsed_s"],
            "pct_of_total": round(slowest["elapsed_s"] / wall_total * 100, 1)
                           if wall_total > 0 else 0,
        }

        # Add per-file rate for validation stages
        for s in stages:
            if "files_validated" in s["counts"] and s["counts"]["files_validated"] > 0:
                s["rate_ms_per_file"] = round(
                    s["elapsed_s"] * 1000 / s["counts"]["files_validated"], 1
                )

    Path(timing_output).write_text(json.dumps(timing_data, indent=2), encoding="utf-8")
    print(f"\n💾 Timing data exported to: {timing_output}")

    # ── Console Report ───────────────────────────────────────
    print(f"\n\n{'='*60}")
    print(f"📊 PIPELINE TIMING REPORT")
    print(f"{'='*60}")
    print(f"\n| Stage | Time (s) | % | Exit | Key Counts |")
    print(f"|-------|----------|---|------|------------|")

    for s in stages:
        elapsed = s["elapsed_s"]
        pct = round(elapsed / wall_total * 100, 1) if wall_total > 0 else 0
        rc = s["exit_code"]
        counts = s["counts"]

        # Pick most relevant counts to display
        display_parts = []
        for key in ["evidence", "entity", "relation", "issue", "total_files",
                     "files_validated"]:
            if key in counts:
                display_parts.append(f"{key}={counts[key]}")
        if "rate_ms_per_file" in s:
            display_parts.append(f"{s['rate_ms_per_file']}ms/file")
        counts_str = ", ".join(display_parts) or "—"

        status = "✅" if rc == 0 else "❌"
        print(f"| {s['name']} | {elapsed:.3f} | {pct}% | {status} | {counts_str} |")

    print(f"\n**Wall total: {wall_total:.3f}s**")

    # Bottleneck + diagnosis
    if stages:
        slowest = max(stages, key=lambda s: s["elapsed_s"])
        print(f"\n🔍 **Bottleneck: {slowest['name']}** "
              f"({slowest['elapsed_s']:.3f}s, "
              f"{round(slowest['elapsed_s']/wall_total*100, 1)}% of total)")

        # Diagnosis hints
        name = slowest["name"]
        print(f"\n💡 Diagnosis hints for '{name}':")
        if "schema_validate" in name:
            rate = slowest.get("rate_ms_per_file", 0)
            if rate > 50:
                print(f"   → {rate}ms/file is slow. Likely re-compiling schemas per file.")
                print(f"   → Fix: Cache compiled validators. Consider fastjsonschema.")
            else:
                print(f"   → {rate}ms/file is reasonable. Volume issue, not per-file.")
        elif name == "semantic_validate":
            print(f"   → Likely O(n²) cross-artifact lookups.")
            print(f"   → Fix: Build id→artifact index once, then run rules against index.")
        elif name == "generate_artifacts":
            print(f"   → Likely many small YAML writes or re-parsing evidence.")
            print(f"   → Fix: Batch writes, parse evidence once into memory.")
        elif name == "extraction":
            print(f"   → Extraction is the bottleneck — unusual for v0.2.")
            print(f"   → Check call resolver for O(n²) symbol lookups.")


if __name__ == "__main__":
    main()
