# Sovereign System Documentation Audit

This directory contains the results of the retroactive closed-loop audit of the Sovereign System's doctrine and evolution.

## Audit Principles
1. **Independence**: Audit tools operate independently of production code.
2. **Disagreement = Signal**: Evidence gaps are recorded as signals, not hidden.
3. **Traceability**: Every claim must be linked to a physical artefact.

## Deliverables
- `SCOPE.md`: Boundaries of the audit.
- `EVIDENCE_INDEX.md`: Master list of verified artefacts.
- `TIMELINE.md`: Reconstructed evolution of the system.
- `TRACE_MATRIX.md`: Mapping of claims to evidence.
- `AUDIT_GAPS.md`: Identified missing provenance.
- `HASH_MANIFEST.json`: Cryptographic fingerprints of all audited files.

## Audit Pipeline
The audit is performed by a suite of specialized scripts in `scripts/audit/`:
- `Forensic-Scanner.ps1`: Generates the hash manifest.
- `Timeline-Builder.ps1`: Reconstructs history from logs.
- `Claim-Tracer.ps1`: Maps doctrine to artefacts.
- `Skeptic-Auditor.ps1`: Identifies gaps.
- `Invoke-AuditPipeline.ps1`: Orchestrates the full process.

## Hardening (Phase 1 Implemented)
The audit framework now includes additional integrity layers:
1. **Merkle Sealing**: Bundles are sealed with a SHA-256 Merkle root using `audit/scripts/seal_bundle.py`.
2. **Pipeline Versioning**: Tracked in `audit/.pipeline_version`.
3. **Immutable Snapshots**: Historical audit results are preserved in `audit/snapshots/`.
4. **VS Code Integration**: Standardized tasks for verified pipeline execution.
