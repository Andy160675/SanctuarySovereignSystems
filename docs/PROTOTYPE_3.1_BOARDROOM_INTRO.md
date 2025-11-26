# Prototype 3.1 - BoardRoom Introduction

**Version:** 3.1
**Date:** 2025-11-26
**Status:** Active Development

---

## Overview

Prototype 3.1 represents a significant milestone in the Sovereign System: the integration of **Sovereign Version Control (SVC)** directly into the BoardRoom UI. This creates a unified command center for AI governance, evidence management, and immutable audit trails.

## What's New in 3.1

### 1. SVC Tab in BoardRoom UI
A dedicated tab for viewing and managing the Sovereign Version Control system:
- **HEAD commit display** with integrity status badges
- **Run Trinity cases** directly from the UI
- **Commit history browser** with expandable details
- **Evidence metrics** (count, mismatches, risk level)

### 2. Anchor Script (`scripts/anchor-svc-bundle.ps1`)
PowerShell automation for evidence anchoring:
- Creates timestamped ZIP bundles of all SVC commits
- Computes SHA-256 verification hashes
- Generates anchor manifest (JSON) with metadata
- Placeholder for IPFS/Arweave upload

### 3. CI/CD Pipeline (`.github/workflows/svc-archive.yml`)
Automated nightly archival:
- Bundles all SVC commits
- Uploads to IPFS via web3.storage (if token configured)
- Creates GitHub Actions artifacts (90-day retention)
- Generates summary report with verification instructions

### 4. Nudge Email Template (`docs/NUDGE_EMAIL_DRAFT.md`)
Professional template for sharing evidence bundles:
- SHA-256 verification instructions
- IPFS gateway links
- Legal notice boilerplate
- Technical explanation for non-technical recipients

---

## Architecture

```
BoardRoom UI (Streamlit :8501)
    |
    +-- Dashboard ......... System health overview
    +-- Core .............. Agent playground
    +-- Truth ............. Truth engine interface
    +-- Enforce ........... Security & sentinel
    +-- SVC [NEW] ......... Sovereign Version Control
            |
            +-- HEAD Commit Display
            +-- Run Trinity Case
            +-- Commit History
            +-- Integrity Verification

Trinity Backend (:8600)
    |
    +-- /api/trinity/run_case ....... Execute 4-agent pipeline
    +-- /api/trinity/svc/head ....... Get HEAD commit
    +-- /api/trinity/svc/history .... Get all commits

Mock Services (:8001-8005, :8502)
    |
    +-- Investigator, Verifier, Guardian, DollAgent
    +-- Evidence API endpoints
```

---

## Quick Start

### 1. Start Services
```powershell
# Start mock services (if not running)
cd C:\sovereign-system
python -m trinity.mock_services

# Start Trinity backend
python -m trinity.trinity_backend

# Start BoardRoom UI
cd boardroom
streamlit run boardroom_app.py --server.port 8501
```

### 2. Access BoardRoom
Open browser: http://localhost:8501

### 3. Run Trinity Case
1. Navigate to **SVC** tab
2. Enter Case ID and Query
3. Click **Run Trinity Case**
4. View results and new SVC commit

### 4. Create Evidence Bundle
```powershell
.\scripts\anchor-svc-bundle.ps1

# With IPFS upload (placeholder)
.\scripts\anchor-svc-bundle.ps1 -Upload
```

---

## Key Files

| File | Purpose |
|------|---------|
| `boardroom/boardroom_app.py` | Main UI with SVC tab |
| `scripts/anchor-svc-bundle.ps1` | Evidence bundle creator |
| `.github/workflows/svc-archive.yml` | Nightly archival CI |
| `docs/NUDGE_EMAIL_DRAFT.md` | Email template |
| `sov_vc/commits/*.json` | SVC commit files |
| `sov_vc/HEAD` | Current HEAD pointer |

---

## SVC Commit Structure

Each commit contains:
```json
{
  "commit_hash": "sha256...",
  "parent_hash": "sha256... or GENESIS",
  "timestamp": "ISO-8601",
  "case_id": "CASE-XXX",
  "run_id": "uuid",
  "evidence_count": N,
  "evidence_mismatches": N,
  "integrity_status": "INTACT | COMPROMISED",
  "risk_level": "low | medium | high",
  "query": "original query",
  "evidence_files": [...],
  "agent_results": {...}
}
```

---

## Security Model

1. **Tamper Detection** - SHA-256 hashes on all evidence
2. **Chain Integrity** - Hash-linked commit chain
3. **Immutable Anchoring** - IPFS/Arweave for permanent storage
4. **Audit Trail** - Complete history preserved
5. **Third-Party Verification** - Anyone can verify hashes

---

## Next Steps (Prototype 3.2+)

- [ ] GPG signing for commits
- [ ] Arweave integration for permanent storage
- [ ] WebSocket real-time updates in UI
- [ ] Multi-case dashboard view
- [ ] Export to PDF/legal format
- [ ] Witness mode (third-party verification)

---

## Credits

Built on the Sovereign System framework.
Trinity AutoBuild: 4-agent AI pipeline for evidence validation.

*"Trust through verification, sovereignty through transparency."*
