# Main Command Node: Responsibilities & Authority

**Document ID:** GOV-MCN-v1.0  
**Classification:** Class S (Supreme)  
**Effective Date:** 2026-02-02  
**Status:** ACTIVE

---

## 1. Purpose

This document defines the responsibilities, authority boundaries, and operational obligations of the **Main Command Node (NODE-MOBILE)**. As the designated Class S node within the Sovereign Infrastructure, it serves as the central point of command and control for all system operations.

The Main Command Node is the only node authorized to exercise supreme command authority across the entire sovereign mesh. This authority is granted under strict governance constraints to ensure accountability, auditability, and alignment with constitutional principles.

---

## 2. Designation

| Attribute | Value |
|-----------|-------|
| **Node Identifier** | NODE-MOBILE |
| **Classification** | Class S (Supreme) |
| **Role** | Main Command Node |
| **Authority Scope** | Full orchestration authority over all sovereign systems |
| **Connectivity Modes** | Hardwired Ethernet, Tailscale SSH, Chrome Remote Desktop |

---

## 3. Core Responsibilities

### 3.1 System Orchestration

The Main Command Node is responsible for coordinating all operational activities across the sovereign infrastructure. This includes:

- **Service Lifecycle Management:** Starting, stopping, and restarting containerized services across all nodes.
- **Deployment Execution:** Running deployment scripts (`deploy.sh`), managing Docker stacks, and applying Kubernetes manifests.
- **Configuration Propagation:** Distributing configuration changes to subordinate nodes via secure channels.
- **Fleet Synchronization:** Ensuring all nodes maintain consistent state with the canonical source of truth (GitHub).

### 3.2 Monitoring & Health Oversight

The Main Command Node must maintain continuous awareness of system health:

- **Node Connectivity:** Verify all nodes in the mesh are reachable via Tailscale.
- **Service Status:** Monitor container health and service availability across the fleet.
- **Resource Utilization:** Track CPU, memory, and storage metrics to prevent resource exhaustion.
- **Anomaly Detection:** Identify and escalate unusual patterns that may indicate security incidents or system degradation.

### 3.3 Backup & Recovery Coordination

The Main Command Node oversees the backup strategy and serves as the primary recovery coordinator:

- **Backup Verification:** Confirm daily, weekly, and monthly backups complete successfully.
- **Integrity Checks:** Validate backup archives against known-good checksums.
- **Recovery Execution:** In the event of node failure, coordinate restoration from backups.
- **Disaster Recovery Testing:** Periodically test recovery procedures to ensure they remain functional.

### 3.4 Security Enforcement

The Main Command Node enforces security policies across the infrastructure:

- **Access Control:** Ensure all nodes comply with their assigned access class (A/B/C).
- **Credential Management:** Rotate SSH keys, API tokens, and other credentials on schedule.
- **Firewall Verification:** Confirm firewall rules align with the ACCESS_POLICY.md specification.
- **Incident Response:** Serve as the command center for security incident investigation and remediation.

### 3.5 Governance Compliance

The Main Command Node must operate within the constitutional framework:

- **Audit Trail Maintenance:** Log all commands to WORM storage for immutable audit.
- **Quorum Coordination:** Submit destructive actions to Trinity agents for approval.
- **Policy Enforcement:** Reject any operation that violates constitutional principles.
- **Documentation Updates:** Keep governance documents current and accurate.

---

## 4. Authority Boundaries

### 4.1 Granted Authority

The Main Command Node is authorized to:

| Action | Scope | Constraints |
|--------|-------|-------------|
| **Execute deployments** | All nodes | Must be logged to audit trail |
| **Modify service configurations** | All nodes | Changes must be committed to Git |
| **Access all nodes via SSH** | Full mesh | Via Tailscale only |
| **Issue emergency halt commands** | All nodes | Requires justification in audit log |
| **Read all governance documents** | Full repository | No restrictions |
| **Write governance documents** | Full repository | Subject to commit review |

### 4.2 Prohibited Actions

The Main Command Node is **NOT** authorized to:

| Prohibited Action | Rationale |
|-------------------|-----------|
| **Bypass audit logging** | Violates CP-001 (Immutable Audit Trail) |
| **Execute destructive commands without quorum** | Violates CP-002 (Human Oversight) |
| **Modify constitutional invariants unilaterally** | Violates CP-003 (Constitutional Supremacy) |
| **Operate in silent failure mode** | Violates CP-005 (Graceful Degradation) |
| **Grant Class S authority to other nodes** | Single command node doctrine |

### 4.3 Emergency Override

In a declared state of emergency, the Main Command Node may temporarily bypass quorum requirements for destructive actions. This override is subject to:

- **Declaration:** A cryptographically signed emergency declaration must be logged.
- **Justification:** The declaration must include a detailed justification.
- **Time Limit:** The override expires after 1 hour unless explicitly extended.
- **Post-Incident Review:** All emergency actions must be reviewed within 24 hours.

---

## 5. Operational Obligations

### 5.1 Inert-by-Default

The Main Command Node must remain in an inert, listen-only state until explicitly activated by the authenticated human operator. Activation requires:

- Password-protected SSH key authentication
- Time-based one-time password (TOTP) or physical security key
- Successful Tailscale mesh connection

### 5.2 Mode-Aware Operation

The Main Command Node must detect its connectivity mode and apply appropriate policies:

| Mode | Detection | Policy |
|------|-----------|--------|
| **Hardwired** | Ethernet interface UP | Full LAN access for orchestration |
| **WiFi** | Trusted SSID detected | Local access with standard restrictions |
| **Remote** | Tailscale only | Restricted to mesh traffic only |

### 5.3 Continuous Audit

All commands executed from the Main Command Node must be logged to an immutable audit trail. The log must capture:

- Timestamp (UTC)
- Command executed
- Target node(s)
- Operator identity
- Command output/result
- Hash chain link to previous entry

### 5.4 Regular Verification

The Main Command Node operator must perform regular verification checks:

| Check | Frequency | Command |
|-------|-----------|---------|
| Mesh connectivity | Daily | `tailscale status` |
| Service health | Daily | `docker ps` on each node |
| Backup status | Weekly | Verify NAS sync logs |
| Governance compliance | Weekly | `gh run list` for CI status |
| Full system audit | Monthly | Run all verification commands |

---

## 6. Succession & Recovery

### 6.1 Single Command Node Doctrine

Only one node may hold Class S designation at any time. If the Main Command Node is lost or compromised:

1. **Revoke Authority:** Remove the compromised node from Tailscale ACLs immediately.
2. **Designate Successor:** A new node may be elevated to Class S via constitutional amendment.
3. **Restore from Backup:** The successor node must be provisioned from the canonical repository.
4. **Verify Chain Integrity:** Confirm the evidence chain remains unbroken.

### 6.2 Recovery Procedure

If NODE-MOBILE is lost or wiped, follow the recovery procedure in `docs/NODE_INVENTORY.md`:

1. Install required software (Python, Rust, Git, VS Code)
2. Clone repository from GitHub
3. Configure Tailscale and SSH reach-back
4. Run verification commands
5. Update NODE_INVENTORY.md with new hostname if changed

---

## 7. Accountability

The human operator of the Main Command Node accepts full accountability for:

- All commands executed from the node
- Compliance with constitutional principles
- Maintenance of the audit trail
- Security of credentials and access tokens
- Timely response to security incidents

Violations of this document will be logged, will trigger system-wide alerts, and may result in automatic revocation of command authority.

---

## 8. References

| Document | Purpose |
|----------|---------|
| `docs/NODE_INVENTORY.md` | Node topology and classification |
| `ACCESS_POLICY.md` | Access control policy |
| `OPERATOR_CONTRACT.md` | Binding operator obligations |
| `AUTONOMY_LIMITS.md` | Autonomy model and forbidden actions |
| `Governance/governance_config.yaml` | Constitutional principles |

---

*This document is part of the Sovereign System governance framework and is subject to constitutional review.*
