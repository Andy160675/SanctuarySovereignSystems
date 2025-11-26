# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| V3.x    | :white_check_mark: |
| < V3    | :x:                |

## Reporting a Vulnerability

We take security seriously. The Sovereign System is designed for institutional-grade governance, which means security issues are treated with the highest priority.

### How to Report

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead:

1. Email security concerns to the maintainers directly
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Any suggested mitigations

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 24-72 hours
  - High: 1-2 weeks
  - Medium: 2-4 weeks
  - Low: Next release cycle

### Scope

Security issues we're interested in:

- Hash chain integrity bypasses
- Governance gate circumvention
- Unauthorized anchor modification
- External witness spoofing
- Authentication/authorization flaws
- Data exfiltration vectors

### Out of Scope

- Issues in dependencies (report upstream)
- Theoretical attacks without proof-of-concept
- Social engineering vectors
- Physical access attacks

## Security Architecture

The Sovereign System implements multiple security layers:

### Hash Chain Integrity
- SHA-256 payload hashing
- Chain hash continuity verification
- Cross-platform normalization

### Governance Gates
- Evidence gate (Recorder + Archivist)
- Ethics gate (Ethicist review triggers)
- Legal gate (Jurist escalation)
- Security gate (Guardian controls)
- Consensus gate (7/13 supermajority)

### External Witness
- RFC3161 timestamping (when enabled)
- IPFS/Arweave anchoring (when enabled)
- Sidecar pattern (witness data separate from commits)

### Audit Trail
- All actions produce artifacts
- Automation dispatch is logged and anchored
- No silent side effects

## Responsible Disclosure

We follow responsible disclosure practices:

1. Reporter notifies maintainers privately
2. We confirm and assess the issue
3. We develop and test a fix
4. We coordinate disclosure timing with reporter
5. We release fix and publish advisory
6. Reporter may be credited (with permission)

Thank you for helping keep Sovereign System secure.

---

*"The organism protects itself by being transparent about how it protects itself."*
