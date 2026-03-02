#!/bin/bash
# Run engine (engine=true) mode for parity comparison
# Usage: ./run-engine.sh [repo-root] [output-dir]

REPO_ROOT="${1:-.}"
OUTPUT_DIR="${2:-./sprint-v050-engine/03-evidence-runs/engine}"

echo "Running engine mode..."
python3 extract_python.py \
    --repo-root "$REPO_ROOT" \
    --repo-name repo://main \
    --revision git:HEAD \
    --enable-v050-resolution-engine true \
    --out "$OUTPUT_DIR"

echo "Engine run complete. Output: $OUTPUT_DIR"
