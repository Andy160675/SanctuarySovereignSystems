# Runtime Entrypoints (Canonical)

## Canonical production entrypoint
- truth-engine/app.py
  - Status: FIREWALLED (export-only)
  - Commit: 6b1039dd6f62cbb5931bf18a8deaadae8f264944

## Secondary / complete harness (non-production unless explicitly deployed)
- truth-engine-complete/app.py
  - Status: FIREWALLED (export-only; txtai optional)
  - Commit: 56cf466ee4d2f6f637fea2bb35436815248debdb

## Non-canonical mirrors
- core/truth-engine/*
- core/truth-engine-complete/*

These core/* paths are treated as mirrors/legacy unless they appear in deployment manifests
or launch scripts. Current launch-surface sweep found only editor-metadata references.
