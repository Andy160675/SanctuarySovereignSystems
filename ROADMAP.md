# Season 3 Roadmap: Extension Governance
**Date:** 2026-02-08
**Baseline:** v1.0.0-kernel74 (STABLE LOCKED)

## 1. Overview
This roadmap defines the governance framework and delivery sequence for Season 3 extensions (`S3-EXT-001..006`). All extensions must pass the Season 2 Compliance Gate and cannot modify core invariants.

## 2. Governance Framework (The "Extension Boundary")
- **Immutability**: Season 2 Kernel Invariants are immutable by extensions.
- **Authority Matching**: Extensions must declare their required Authority Level (Operator, Innovator, or Steward) in their manifest.
- **Subtractive Verification**: Compliance Gate (Phase 9) verifies that the extension manifest does not request forbidden capabilities.
- **Audit Integration**: Extension activation and core signals are hash-chained in the Audit Ledger.

## 3. Extension IDs and Delivery Sequence

### Phase 3.1: Observation & Connectivity
- **S3-EXT-001: Signal Observer**
  - **Level**: Innovator
  - **Function**: Passive telemetry of the signal bus for observability.
  - **Constraint**: Read-only; cannot inject signals.
- **S3-EXT-002: External Webhook Adapter**
  - **Level**: Operator
  - **Function**: Inbound bridge for external events (GitHub, Slack, Custom Webhooks).
  - **Constraint**: Signals must pass full Legality Gate (P3) before routing.

### Phase 3.2: Multi-Party Authority
- **S3-EXT-003: Quorum Consensus Handler**
  - **Level**: Steward
  - **Function**: Implements m-of-n approval for Steward-level signals.
  - **Constraint**: Cannot override the Halt Doctrine.
- **S3-EXT-004: Treasury & Asset Vault**
  - **Level**: Steward
  - **Function**: Cryptographic custody of digital assets tied to kernel signals.
  - **Constraint**: Asset release strictly bound to Steward-level routed signals.

### Phase 3.3: Scaling & Resilience
- **S3-EXT-005: Pathology Detector (Integrated)**
  - **Level**: Innovator
  - **Function**: Active monitoring of kernel health and signal pathology.
  - **Implementation**: `tools/sovereign_stack/engine/pathology/pathology_detector.py`
  - **Constraint**: Advisory signals only; cannot bypass authority ladder.
- **S3-EXT-006: Sovereign Sync (Integrated)**
  - **Level**: Operator
  - **Function**: Constitutional commit and push operations ("G.I.y").
  - **Implementation**: `tools/sovereign_stack/ops/sovereign_sync.py`
  - **Constraint**: Every push must be a typed signal recorded in the audit ledger.

## 4. SovereignStack Deployment Tooling
The `tools/sovereign_stack/` directory contains the production-grade implementation of the Sovereign Kernel and supporting infrastructure.
- **Kernel Orchestrator**: `sovereign_kernel.py`
- **Sync Tools**: `ops/sovereign_sync.py`
- **Pathology Monitoring**: `engine/pathology/pathology_detector.py`

### Deployment Flow
1. Initialize Kernel: `from tools.sovereign_stack.sovereign_kernel import SovereignKernel`
2. Register Handlers per Authority Level.
3. Process signals through the full constitutional pipeline.
4. Execute "G.I.y" sync operations for audited repository updates.

## 5. Compliance Gate Checklists
Each extension must provide:
1. `manifest.json` declaring permissions.
2. `compliance_proof.py` (optional formal proof of non-interference).
3. Integration tests covering the Authority Ladder escalation.

---
*Season 3 activated by governance. Baseline locked.*
