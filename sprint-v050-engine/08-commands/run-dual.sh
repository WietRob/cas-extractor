#!/bin/bash
# Run dual mode (both legacy and engine) for parity comparison
# Usage: ./run-dual.sh [repo-root] [output-dir]

REPO_ROOT="${1:-.}"
OUTPUT_DIR="${2:-./sprint-v050-engine/03-evidence-runs}"

LEGACY_DIR="$OUTPUT_DIR/legacy"
ENGINE_DIR="$OUTPUT_DIR/engine"

echo "=== Dual Run Mode ==="

echo "[1/2] Running legacy mode..."
python3 extract_python.py \
    --repo-root "$REPO_ROOT" \
    --repo-name repo://main \
    --revision git:HEAD \
    --out "$LEGACY_DIR"

echo "[2/2] Running engine mode..."
python3 extract_python.py \
    --repo-root "$REPO_ROOT" \
    --repo-name repo://main \
    --revision git:HEAD \
    --enable-v050-resolution-engine true \
    --out "$ENGINE_DIR"

echo ""
echo "=== Dual Run Complete ==="
echo "Legacy output: $LEGACY_DIR"
echo "Engine output: $ENGINE_DIR"
echo ""
echo "To compare results, run:"
echo "  python3 sprint-v050-engine/08-commands/compare_results.py $LEGACY_DIR $ENGINE_DIR"
