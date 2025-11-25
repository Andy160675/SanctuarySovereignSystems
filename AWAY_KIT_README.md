# Sovereign Away Kit v1
## Air-Gapped Field Deployment Package

**Created**: 2025-11-25
**Version**: 1.0.0
**Classification**: OFFLINE-CAPABLE / AIR-GAP READY

---

## Kit Contents

### Drive Mapping

| Drive | Label | Size | Purpose |
|-------|-------|------|---------|
| **E:** | Elements (SOV_ARCHIVE) | 8TB HDD | Cold storage, evidence archive, full system backup |
| **F:** | KINGSTON (SOV_BOOT) | USB | Boot USB, installer, recovery tools |
| **G:** | SSD2TB (SOV_FIELD) | 2TB SSD | Hot deployment, active sandbox, field operations |

---

## Quick Start

### Option 1: Full Node Setup (New Machine)
```batch
F:\SovereignNode-Setup.bat
```
This will:
- Verify Python 3.10+ installation
- Install offline pip packages from cache
- Create `C:\sovereign-system` directory structure
- Copy core files and evidence store
- Run initial health check

### Option 2: Field Sandbox (Any Machine with Python)
```powershell
G:\RUN-FieldSandbox.ps1
```
This will:
- Start mock services (ports 8001-8005, 8502)
- Launch Trinity backend (port 8600)
- Run smoke test with SVC commit
- Display health dashboard

### Option 3: Archive Recovery
```powershell
# Restore from archive
robocopy E:\SOVEREIGN-ARCHIVE C:\sovereign-system /E /MT:8
```

---

## Directory Structure

```
SOV_BOOT (F:)
├── SovereignNode-Setup.bat      # One-click installer
├── AWAY_KIT_README.md           # This file
├── pip-cache/                   # Offline Python packages
├── installers/
│   ├── python-3.11.9-amd64.exe
│   └── Git-2.43.0-64-bit.exe
└── core-minimal/                # Minimum viable system
    ├── mock_services.py
    ├── trinity/
    └── sov_vc/

SOV_FIELD (G:)
├── RUN-FieldSandbox.ps1         # Quick sandbox launcher
├── sovereign-system/            # Full system copy
│   ├── mock_services.py
│   ├── trinity/
│   ├── boardroom/
│   ├── sov_vc/
│   └── evidence_store/
├── results/                     # Test results accumulator
└── logs/                        # Operation logs

SOV_ARCHIVE (E:)
├── SOVEREIGN-ARCHIVE/           # Full immutable backup
├── evidence-vault/              # Historical evidence bundles
├── golden-masters/              # Verified system snapshots
└── audit-logs/                  # Compliance trail
```

---

## Offline Package Manifest

### Python Dependencies (pip-cache/)
```
fastapi==0.109.0
uvicorn==0.27.0
httpx==0.26.0
pydantic==2.5.3
streamlit==1.31.0
requests==2.31.0
python-multipart==0.0.6
```

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.10+ (3.11 recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Ports**: 8001-8005, 8501, 8502, 8600

---

## Verification Commands

### Check System Health
```powershell
# From any sovereign-system directory
python mock_services.py &
curl http://localhost:8502/health
```

### Verify Evidence Integrity
```powershell
curl -X POST http://localhost:8502/api/core/verify_hash `
  -H "Content-Type: application/json" `
  -d '{"evidence_path": "evidence_store/CASE-TEST-001/mock-event-1.jsonl", "expected_hash": "<HASH>"}'
```

### Run SVC Log
```powershell
python sov_vc/sov.py log
```

---

## Emergency Procedures

### If Services Won't Start
1. Check Python: `python --version`
2. Check ports: `netstat -an | findstr "8502"`
3. Kill orphan processes: `taskkill /F /IM python.exe`

### If Evidence Is Tampered
1. System will detect via hash mismatch
2. Guardian agent will flag and log
3. Restore from E:\SOVEREIGN-ARCHIVE if needed

### If Boot USB Fails
1. Copy F:\core-minimal to any USB
2. Run setup manually from that USB

---

## Contact / Support

This is an offline-first system. All documentation is self-contained.

For the constitutional framework, see:
- `docs/HARMONY_PROTOCOL.md`
- `docs/KID_SAFE_PROTOCOL.md`

For deployment strategy, see:
- `docs/DEPLOYMENT_STRATEGY.md`

---

**Remember**: The sovereign system operates on the principle that AI doesn't need a body - it needs infrastructure. This kit IS that infrastructure, portable and air-gap ready.
