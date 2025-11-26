# SOVEREIGN SYSTEM - V3 FROZEN / V4 ACTIVE
# ==========================================
#
# 26 November 2025
#
# Constitutional Status: V3 RATIFIED AND FROZEN
# Evolution Layer: V4 ACTIVE (safety-bounded)
#
# ---

## Current Architecture

```
sovereign-system/
├── src/boardroom/              # Core Governance Layer (V3 Frozen)
│   ├── governance.py           # Hard Gates (evidence, ethics, legal, security, consensus)
│   ├── anchoring.py            # Hash Chain (cross-platform verified)
│   ├── roles.py                # Boardroom 13 Constitutional Roles
│   ├── automation.py           # Post-commit dispatch (5 handlers)
│   ├── external_anchor.py      # RFC3161/IPFS/Arweave witness adapter
│   └── chain_governed_verify.py # V4: Governed maintenance operations
├── streamlit_app/              # Governance Cockpit
│   └── Home.py                 # Live dashboard with "Verify Now (Governed)"
├── DATA/                       # Runtime artifacts (not committed)
│   ├── _anchor_chain.json      # Cryptographic audit spine
│   ├── _commits/               # Governance decision artifacts
│   ├── _chain_verifications/   # Verification reports
│   └── _automation_log.json    # Dispatch history
├── tests/                      # Test suite (V4 safety net)
├── prompts/                    # Constitutional genome
│   └── boardroom_master.txt    # Immutable behavioural DNA
└── docs/                       # Documentation
```

## System Status

### V3 Core (FROZEN)

| Component | Status | Description |
|-----------|--------|-------------|
| Boardroom 13 | ✅ Active | 13 constitutional roles |
| Governance Gate | ✅ Active | 5 hard gates enforced |
| Hash Chain | ✅ Valid (7/7) | Cross-platform verified |
| External Witness | ✅ Configured | RFC3161/IPFS adapter (dry-run) |
| Automation Dispatch | ✅ Active | 5 action handlers |

### V4 Evolution (ACTIVE)

| Feature | Status | Description |
|---------|--------|-------------|
| Governed Verification | ✅ Live | VERIFY_CHAIN_NOW as governed action |
| Test Suite | ✅ Protected | Anchoring, verification, automation |
| Open Source Prep | ✅ Ready | LICENSE, CONTRIBUTING, SECURITY |

### Deployment

| Endpoint | Status |
|----------|--------|
| Streamlit Cloud | ✅ Live |
| Local Demo | ✅ `./DEMO.bat` |

## Institutional Triad

```
LAW (V3 Constitution) + MEMORY (Hash Chain) + PROOF (Test Suite)
```

All three are now aligned and machine-verifiable.

## Operational Posture

**Mode:** Operate → Observe → Respond

No build pressure until real human friction occurs:
- Human misunderstands the cockpit
- Human hesitates at a governance step
- Human asks for proof unavailable in one click
- Human tries to use governance as workflow rather than audit

## Quick Start

```powershell
# Windows
.\DEMO.bat

# PowerShell
.\DEMO.ps1

# Unix
./demo.sh
```

Then open: http://localhost:8501

## Chain Health

```bash
python -c "from src.boardroom.anchoring import verify_chain_integrity; print(verify_chain_integrity())"
```

Expected: `{'valid': True, 'total_anchors': 7, 'verified_anchors': 7, 'errors': []}`

## Constitutional Properties

1. **Sovereign Truth**: Internal memory cannot be quietly rewritten
2. **External Non-Repudiation**: Third parties can verify existence timestamps
3. **Hard Gate Enforcement**: No action without evidence, ethics, legal, security, consensus
4. **Full Traceability**: Every decision has a chain position
5. **Forensic Readiness**: Any decision can be exported as a sealed bundle

## Evolution History

| Version | Date | Status |
|---------|------|--------|
| Phase 4 | 2025-11-19 | Docker deployment, Truth Engine |
| Phase 5 | 2025-11-20 | Boardroom 13, Governance Gate |
| V3 | 2025-11-26 | Constitutional freeze |
| V4 | 2025-11-26 | Governed maintenance, test suite |

---

*"The organism remembers what it did, can prove it didn't rewrite history,
and a third party can confirm when that memory existed."*

— Sovereign System V3
26 November 2025
