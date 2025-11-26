# Sovereign System V3 - Demo Guide

## One-Click Launch

### Windows
Double-click `DEMO.bat` or run:
```powershell
.\DEMO.ps1
```

### Mac/Linux
```bash
chmod +x demo.sh
./demo.sh
```

## What You'll See

The **Governance & Evidence Board** opens at http://localhost:8501

### Home Page
- Global chain health indicator (VALID/INVALID/EMPTY)
- "Verify Now" button for on-demand chain verification
- System architecture overview
- Quick stats (decisions, chain length, exports)

### Governance View
- Recent governance decisions with outcomes
- Gate status (evidence, ethics, legal, security, consensus)
- Merkle roots and external anchor receipts
- Full JSON inspection for each decision

### Chain Health View
- Chain integrity verification
- Anchor-by-anchor inspection
- Error detection and reporting

### Export View
- One-click evidence bundle generation
- Download sealed ZIP bundles
- View existing exports

## What This Demonstrates

1. **Sovereign Memory** - Hash-chained audit trail that can't be quietly rewritten
2. **Governance Gate** - Decisions only commit after passing hard gates
3. **External Witness** - Third-party attestation capability (dry-run mode)
4. **Forensic Export** - Court-ready evidence bundles
5. **Institutional Transparency** - Everything visible, verifiable, provable

## V3 Status

- **Tag:** v3.0.0-complete
- **Status:** Frozen / Ratified
- **Lineage:** V4 open for future evolution

## Requirements

- Python 3.10+
- Streamlit (auto-installed if missing)
- Git (for cloning)

## Quick Clone & Run

```bash
git clone https://github.com/PrecisePointway/sovereign-system.git
cd sovereign-system
git checkout v3.0.0-complete

# Windows
DEMO.bat

# Mac/Linux
./demo.sh
```
