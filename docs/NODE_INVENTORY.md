# Node Inventory & Backup Manifest

**Purpose:** Track software requirements, backup locations, and audit trail for Mobile Command Centre and all sovereign nodes.

---

## Software Requirements

### Core Development

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Core runtime, tests, agents |
| Rust | 1.70+ | ST MICHAEL, Aumann Gate, Row 14-15 |
| Node.js | 18+ | VS Code extensions, tooling |
| Git | 2.40+ | Version control |
| GitHub CLI | 2.0+ | CI interaction, PR management |

### Python Packages (requirements-dev.txt)

```
pytest>=7.0
pytest-cov>=4.0
pytest-json-report>=1.5
mypy>=1.0
ruff>=0.1.0
pre-commit>=3.0
pydantic>=2.0
```

### Rust Crates (Cargo.toml)

Core dependencies for `src/*.rs` modules - see workspace `Cargo.toml`.

### VS Code Extensions

| Extension | Purpose |
|-----------|---------|
| GitHub Copilot | AI assistance with ARCHANGEL-COMMAND prompt |
| Python | Language support |
| rust-analyzer | Rust language server |
| GitLens | Git history visualization |
| Markdown All in One | Doc editing |

---

## Backup Locations

### Critical Directories (MUST be synced)

| Directory | Content | Backup Priority |
|-----------|---------|-----------------|
| `docs/` | Constitutional documents, canon | CRITICAL |
| `scripts/` | Operational scripts | CRITICAL |
| `.github/workflows/` | CI configuration | CRITICAL |
| `src/` | Rust core (ST MICHAEL, Aumann) | CRITICAL |
| `core/` | Python governance logic | CRITICAL |
| `tests/` | Test suites | HIGH |
| `contracts/` | Solidity (if present) | HIGH |
| `evidence/` | Audit evidence bundles | HIGH |

### Backup Strategy

```
Daily:    docs/, scripts/, .github/ → NAS-01:/backups/sovereign/daily/
Weekly:   Full repo snapshot → NAS-01:/backups/sovereign/weekly/
Monthly:  Encrypted archive → External drive
```

### Sync Commands (from laptop)

```bash
# Pull from core PC
rsync -avz pc-core-1:/c/sovereign-system/ ./sovereign-system/ --exclude='.git'

# Push to NAS
rsync -avz ./sovereign-system/docs/ nas-01:/backups/sovereign/docs/

# Full backup
tar -czvf sovereign-$(date +%Y%m%d).tgz sovereign-system/
gpg -c sovereign-$(date +%Y%m%d).tgz
```

---

## Memory Audit Trail

### Key Commits to Remember

| Commit | Date | Significance |
|--------|------|--------------|
| `1cb2f04` | 2025-12-03 | Automation Baseline v0.1.0 |
| `0ebdda5` | 2025-12-03 | Coverage gate added (CI failed - working as designed) |

### Canon Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Automation Canon | CI-as-constitution | `docs/AUTOMATION_CANON.md` |
| ST MICHAEL Automation | Row 14 + Resilience docs | `docs/ST_MICHAEL_AUTOMATION.md` |
| ARCHANGEL-COMMAND | Mobile command prompt | `docs/ARCHANGEL_COMMAND_PROMPT.md` |
| Contributing Guide | Contributor rules | `CONTRIBUTING.md` |

### Tags

| Tag | Commit | Meaning |
|-----|--------|---------|
| `v0.1.0-automation-baseline` | `1cb2f04` | First constitutional baseline |

---

## Node Topology

```
                    ┌─────────────────────┐
                    │   GitHub Remote     │
                    │ (source of truth)   │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │ NODE-MOBILE │     │  PC-CORE-1  │     │   NAS-01    │
   │ ★ COMMAND ★ │◄───►│ (core svcs) │────►│  (backup)   │
   └─────────────┘     └─────────────┘     └─────────────┘
         │                    │
         │    Tailscale       │
         └────────────────────┘
```

### Node Classification

| Node | Hostname | Classification | Role | Access Methods |
|------|----------|----------------|------|----------------|
| **NODE-MOBILE** | Laptop | **Class S (Supreme)** | Main Command Node — full orchestration authority | Hardwired Ethernet / Tailscale SSH / Chrome Remote Desktop |
| PC-CORE-1 | DESKTOP-V20CP12 | Class B | Core services host | RDP / JetBrains Gateway / Tailscale SSH |
| NAS-01 | nas-01 | Class A | Backup and storage archive | Tailscale SSH (restricted to backup user) |

### Access Policy Classes

| Class | Description | Allowed Access |
|-------|-------------|----------------|
| **Class S** | Supreme Command Node | Unrestricted — full authority over all systems |
| **Class A** | Core Sovereign Nodes | Tailscale SSH only — no GUI, minimal attack surface |
| **Class B** | Operational Support | Tailscale SSH + RDP/JetBrains Gateway — GUI access permitted |
| **Class C** | Restricted Nodes | No persistent remote access — supervised only |

---

## Verification Commands

### Check baseline tag exists

```bash
git tag -l "v0.1.0-automation-baseline"
git rev-parse v0.1.0-automation-baseline
```

### Check CI status

```bash
gh run list --repo PrecisePointway/sovereign-system --limit 5
```

### Verify coverage locally

```bash
pytest tests/ --cov=. --cov-report=term-missing --ignore=tests/red_team/ --ignore=tests/fuzz/
```

### Check node connectivity (from laptop)

```bash
ping pc-core-1  # Tailscale hostname
ssh pc-core-1 "cd /c/sovereign-system && git status"
```

---

## Recovery Procedure

If laptop is lost/wiped:

1. Install software (Python, Rust, Git, VS Code Insiders)
2. Clone repo: `git clone https://github.com/PrecisePointway/sovereign-system.git`
3. Install ARCHANGEL-COMMAND prompt from `docs/ARCHANGEL_COMMAND_PROMPT.md`
4. Configure Tailscale and SSH reach-back
5. Run verification commands above

The repo contains everything needed to reconstruct the node.

---

*Last updated: February 2, 2026*
