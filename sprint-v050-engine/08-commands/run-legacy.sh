#!/bin/bash
# Run legacy (engine=false) mode for parity comparison
# Usage: ./run-legacy.sh [repo-root] [output-dir]

REPO_ROOT="${1:-.}"
OUTPUT_DIR="${2:-./sprint-v050-engine/03-evidence-runs/legacy}"

echo "Running legacy mode..."
python3 extract_python.py \
    --repo-root "$REPO_ROOT" \
    --repo-name repo://main \
    --revision git:HEAD \
    --out "$OUTPUT_DIR"

echo "Legacy run complete. Output: $OUTPUT_DIR"
