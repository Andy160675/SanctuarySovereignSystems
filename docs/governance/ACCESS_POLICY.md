# Sovereign System Access Policy

**Document ID:** GOV-ACCESS-v1.1
**Effective Date:** 2026-02-02
**Status:** ACTIVE

---

## 1. Overview

This document defines the access control policy for all nodes within the Sovereign Infrastructure. It establishes a tiered classification system to enforce the principle of least privilege while enabling necessary operational flexibility. This policy is machine-parsable and is enforced by the system's governance kernel.

---

## 2. Node Classifications

All nodes within the ecosystem must be assigned one of the following classifications. Access methods are strictly limited based on this class.

### Class A: Core Sovereign Nodes

- **Description:** Nodes that host the most critical infrastructure, including Kubernetes masters, evidence ledgers, and the governance kernel itself.
- **Allowed Access:** **Tailscale SSH only.**
- **Rationale:** Maximum security and minimal attack surface. No GUI, web, or other remote access protocols are permitted under any circumstances.

### Class B: Operational Support Nodes

- **Description:** Helper nodes used for operations, development, or tasks requiring a graphical user interface (e.g., Windows desktops, specific Linux desktop tools).
- **Allowed Access:** Tailscale SSH + **Optional Chrome Remote Desktop**.
- **Rationale:** Provides necessary GUI access for specific, approved use cases while maintaining a secure baseline via the Tailscale mesh. Chrome Remote Desktop must be documented and justified for each node.

### Class C: Restricted Nodes

- **Description:** High-risk devices, including those in shared environments or exposed to non-privileged users (e.g., child-accessible devices, public-facing kiosks).
- **Allowed Access:** **No persistent remote access.** Only supervised, session-based screen sharing is permitted.
- **Rationale:** Protects vulnerable users and environments by prohibiting any form of always-on remote control.

---

## 3. Supreme Authority Designation

### Class S: Main Command Node

- **Description:** A unique designation for the single node granted supreme command authority over the entire sovereign infrastructure. This node acts as the primary point of control for orchestration, deployment, and emergency intervention.
- **Designated Node:** `[MAIN_COMMAND_NODE]`
- **Allowed Access:**
    - **Hardwired Ethernet:** Full, unrestricted access to all network segments and nodes for orchestration rollouts.
    - **Tailscale SSH:** Full command-line access to all nodes in the mesh.
    - **Chrome Remote Desktop:** Permitted for GUI access to itself and any Class B nodes.
- **Operator Contract:**
    - All outbound commands must be logged to WORM (Write-Once, Read-Many) storage for an immutable audit trail.
    - The node must remain inert until explicitly activated by the authenticated operator.
    - Destructive commands (e.g., `docker stack rm`, `kube-delete-namespace`) require a quorum approval from the Trinity agents unless under a declared emergency protocol.

---

## 4. Node Inventory & Classification

This table serves as the canonical record of all registered nodes and their assigned access class. It must be updated whenever a new node is added or an existing node's role changes.

| Node Hostname | Classification | Primary Access | Notes |
|---|---|---|---|
| `[MAIN_COMMAND_NODE]` | **Class S (Supreme)** | Hardwired Ethernet / Tailscale SSH | The designated Main Command Node. |
| `PC-CORE-1` | Class A | Tailscale SSH | Core infrastructure services. |
| `NAS-01` | Class A | Tailscale SSH (restricted to backup user) | Backup and storage archive. |
| `NODE-01` | Class A | LAN Only | Air-gapped orchestrator. |
| `NODE-02` | Class A | LAN Only | Air-gapped truth engine. |
| `NODE-03` | Class A | LAN Only | Air-gapped agent fleet. |

---

## 5. Policy Enforcement

- **CI/CD Pipeline:** The build process will fail if any code attempts to grant access rights that violate this policy.
- **Network ACLs:** Tailscale ACLs and local firewalls must be configured to reflect these rules.
- **Auditing:** The governance kernel will perform continuous audits to detect and alert on any unauthorized access attempts or policy deviations.
