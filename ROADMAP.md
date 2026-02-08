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
- **S3-EXT-005: Federated Mesh Connector**
  - **Level**: Innovator
  - **Function**: P2P discovery and signal exchange between independent Sovereign Nodes.
  - **Constraint**: Remote signals treated as untrusted (unverified) until local validation.
- **S3-EXT-006: Adversarial Stress Tester**
  - **Level**: Operator
  - **Function**: Automated fuzzer for testing Legality Gate resilience.
  - **Constraint**: Operates in a contained "simulation" domain.

## 4. Compliance Gate Checklists
Each extension must provide:
1. `manifest.json` declaring permissions.
2. `compliance_proof.py` (optional formal proof of non-interference).
3. Integration tests covering the Authority Ladder escalation.

---
*Season 3 activated by governance. Baseline locked.*
