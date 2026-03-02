# v0.5.0 Baseline Provenance

## Baseline Information

| Field | Value |
|-------|-------|
| **Date** | 2026-02-24 |
| **Commit** | git:HEAD (current working tree) |
| **Python Version** | $(python3 --version) |
| **CLI Version** | v0.4.5 GA |

## Baseline Run Command

```bash
python3 extract_python.py \
  --repo-root . \
  --repo-name repo://main \
  --revision git:HEAD \
  --out ./sprint-v050-engine/00-meta/baseline
```

## Baseline Results

| Metric | Value |
|--------|-------|
| Symbols | 205 |
| Evidence files (symbols) | 53 |
| Import edges | 162 |
| Evidence files (imports) | 24 |
| Call edges | 731 |
| Evidence files (calls) | 37 |

## Baseline Flags Used

Current baseline is captured with default flags (all H2.x features OFF by default):

- `--emit-unresolved-self-attr true` (default)
- `--enable-h25-self-attr-noninit false` (default)
- `--enable-h26-self-attr-intermethod false` (default)
- `--enable-h27-self-attr-transitive false` (default)
- `--enable-h28-factory-return false` (default)
- `--enable-h29-resolution-metadata false` (default)
- `--enable-v050-resolution-engine false` (NEW - default)

## Purpose

This baseline serves as the reference for:
1. Verifying no regressions in legacy mode
2. Comparing legacy vs engine outputs
3. Ensuring parity between old and new implementations

## Reproducibility

To reproduce this baseline:

```bash
cd /home/roberto_schmidt/projects/Deterministic\ Knowledge\ System
python3 extract_python.py --repo-root . --repo-name repo://main --revision git:HEAD --out ./sprint-v050-engine/00-meta/baseline
```
