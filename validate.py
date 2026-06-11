#!/usr/bin/env python3
"""
validate.py — CAS Artifact Validator CLI

Usage:
    python validate.py \
        --schemas ./schemas \
        --rules ./rules/validator_rules.v0.1.yaml \
        --artifacts ./artifacts

Two-stage validation:
  Stage 1: Structural (JSON Schema)
  Stage 2: Semantic (validator_rules.v0.1.yaml, R1–R6)
"""
import argparse
import sys

from cas_extractor.validators.schema_validate import validate_structural
from cas_extractor.validators.semantic_validate import validate_semantic


def main():
    parser = argparse.ArgumentParser(
        description="CAS Artifact Validator — Structural + Semantic"
    )
    parser.add_argument("--schemas", required=True, help="Directory with JSON Schema files")
    parser.add_argument("--rules", required=True, help="Path to validator_rules YAML")
    parser.add_argument("--artifacts", required=True, help="Directory tree with YAML artifacts")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    print("=" * 60)
    print("CAS Validator v0.1")
    print("=" * 60)

    # Stage 1: Structural
    print("\n--- Stage 1: Structural (JSON Schema) ---")
    struct_result = validate_structural(args.schemas, args.artifacts)
    print(struct_result.summary())

    if struct_result.errors:
        print("\nErrors:")
        for err in struct_result.errors:
            path_str = " → ".join(str(p) for p in err.get("path", []))
            print(f"  ✗ {err['file']}")
            if path_str:
                print(f"    at: {path_str}")
            print(f"    {err['message']}")

    if struct_result.warnings:
        print("\nWarnings:")
        for warn in struct_result.warnings:
            print(f"  ⚠ {warn['file']}: {warn['message']}")

    # Stage 2: Semantic
    print("\n--- Stage 2: Semantic (Rules R1–R6) ---")
    sem_result = validate_semantic(args.rules, args.artifacts)
    print(sem_result.summary())

    if sem_result.violations:
        print("\nViolations:")
        for v in sem_result.violations:
            severity = v.get("severity", "error")
            marker = "⚠" if severity == "warning" else "✗"
            print(f"  {marker} [{v['rule']}] {v['artifact']}")
            print(f"    {v['message']}")

    # Exit code
    print("\n" + "=" * 60)
    has_errors = not struct_result.is_valid
    has_semantic_errors = not sem_result.is_valid

    if args.strict:
        has_errors = has_errors or bool(struct_result.warnings)

    if has_errors or has_semantic_errors:
        print("RESULT: FAIL")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
