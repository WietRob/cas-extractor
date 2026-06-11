#!/usr/bin/env python3
"""
generate_artifacts.py — CAS Artifact Generator CLI

Usage:
    python generate_artifacts.py \
        --evidence-dir ./artifacts/evidence \
        --out-entities ./artifacts/entities/py \
        --out-relations ./artifacts/relations \
        --out-issues ./artifacts/issues
"""
import argparse
from cas_extractor.generators.artifact_generator import generate_from_evidence


def main():
    parser = argparse.ArgumentParser(
        description="CAS Artifact Generator — Evidence → Entities/Relations/Issues"
    )
    parser.add_argument("--evidence-dir", required=True, help="Directory with evidence YAML files")
    parser.add_argument("--out-entities", required=True, help="Output directory for entity artifacts")
    parser.add_argument("--out-relations", default="./artifacts/relations", help="Output directory for relation artifacts")
    parser.add_argument("--out-issues", required=True, help="Output directory for issue artifacts")
    args = parser.parse_args()

    print(f"[generate] Reading evidence from {args.evidence_dir} ...")
    counts = generate_from_evidence(
        evidence_dir=args.evidence_dir,
        out_entities=args.out_entities,
        out_relations=args.out_relations,
        out_issues=args.out_issues,
    )

    print(f"[generate] Results:")
    print(f"  → {counts['entities']} entities")
    print(f"  → {counts['relations']} relations")
    print(f"  → {counts['issues']} issues")
    print("[generate] Done.")


if __name__ == "__main__":
    main()
