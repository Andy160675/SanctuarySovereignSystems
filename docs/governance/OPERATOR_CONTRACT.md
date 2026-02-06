_# Operator Contract for Main Command Node

**Document ID:** GOV-OPERATOR-v1.0
**Applies to:** `[MAIN_COMMAND_NODE]` (Class S)
**Effective Date:** 2026-02-02

---

## 1. Principle of Command

This document codifies the binding operational contract for the designated **Main Command Node**. As the central point of control for the Sovereign Infrastructure, this node and its operator are granted supreme authority, balanced by a strict set of inalienable responsibilities. Adherence to this contract is mandatory and is monitored by the governance kernel.

---

## 2. Grant of Authority

The Main Command Node is authorized to perform the following actions:

- **Full System Orchestration:** Initiate, modify, and terminate any and all services across both the remote mesh and the air-gapped LAN.
- **Deployment Authority:** Execute deployment scripts (`deploy.sh`), manage container lifecycles (`docker stack`, `kubectl apply`), and promote builds to production.
- **Emergency Intervention:** Halt, isolate, or decommission any node or service in response to a verified security incident or critical failure.
- **Constitutional Access:** Read and write to all governance documents, including `ACCESS_POLICY.md`, subject to the standard commit and review process.

---

## 3. Mandatory Obligations

This authority is contingent upon the fulfillment of the following obligations:

### 3.1. Immutable Audit Trail

- **Requirement:** All commands that alter the state of the system **must** be logged to a secure, WORM (Write-Once, Read-Many) storage layer before execution.
- **Implementation:** The node's shell must be configured to pipe all commands and their outputs to a remote syslog server or an immutable log service. The integrity of this log is paramount.

### 3.2. Inert-by-Default Activation

- **Requirement:** The command node must remain in an inert, listen-only state until explicitly activated by the authenticated human operator.
- **Implementation:** Activation requires a multi-factor authentication sequence, such as a password-protected SSH key combined with a time-based one-time password (TOTP) or a physical security key (e.g., YubiKey).

### 3.3. Quorum for Destructive Actions

- **Requirement:** Actions classified as "destructive" require a consensus approval from the Trinity agents before execution, except under a declared state of emergency.
- **Definition of Destructive:** Any action that results in the non-recoverable deletion of data or the permanent termination of a core service. Examples include:
    - `docker stack rm`
    - `kubectl delete namespace`
    - `rm -rf /data/production`
- **Implementation:** The command-line interface will be wrapped by a script that submits a proposal to the governance kernel and waits for a signed approval from the Trinity before proceeding.

### 3.4. Mode-Aware Policy Enforcement

- **Requirement:** The node must be aware of its current connectivity mode (Hardwired, Remote, WiFi) and apply the corresponding security policies automatically.
- **Implementation:** A mode-detection script will run on startup and on network changes, adjusting firewall rules and routing tables to match the context-specific policies defined in `ACCESS_POLICY.md`.

---

## 4. Emergency Protocols

- **Declaration:** A state of emergency can be declared by the human operator via a cryptographically signed message. This declaration bypasses the quorum requirement for destructive actions.
- **Justification:** The declaration must be accompanied by a detailed justification, which is logged to the immutable audit trail.
- **Revocation:** The state of emergency is automatically revoked after a predefined period (e.g., 1 hour) unless explicitly extended.

---

## 5. Acknowledgment

By activating and operating this node, the human operator acknowledges and agrees to be bound by the terms of this contract. Violations will be logged, will trigger an immediate system-wide alert, and may result in the automatic revocation of command authority.
