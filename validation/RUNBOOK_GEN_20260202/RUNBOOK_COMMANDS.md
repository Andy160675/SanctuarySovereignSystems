# The Blade of Truth Runbook: Tasks & Commands

This document provides a mapping of VS Code tasks to their corresponding manual commands and scripts.

## How to Run Tasks in VS Code
- Open Command Palette: `Ctrl+Shift+P`
- Type: `Tasks: Run Task`
- Select the desired task from the list.

---

## ðŸ›  Available Tasks

### 1. Phase 5: Start Full Stack
**Purpose:** Launches the core sovereign services (truth-engine, ollama, blade-watcher) via Docker.
- **VS Code Task:** `Phase 5: Start Full Stack`
- **Manual Command:**
  ```powershell
  docker compose up -d
  ```

### 2. Fleet: Full Sync (Remote + Nodes)
**Purpose:** Pulls latest code from Git, stashes local changes if necessary, and synchronizes the entire fleet.
- **VS Code Task:** `Fleet: Full Sync (Remote + Nodes)`
- **Manual Command:**
  ```powershell
  powershell -File scripts/fleet/Sync-SovereignFleet.ps1
  ```
- **Note:** This runs `git pull origin main` and orchestrates updates across PC1-PC5.

### 3. Golden Master: Nightly Generation
**Purpose:** Generates the nightly golden master backup and manifest.
- **VS Code Task:** `Golden Master: Nightly Generation`
- **Manual Command:**
  ```powershell
  powershell -File scripts/nightly-master.ps1
  ```

### 4. UI: Start Development
**Purpose:** Launches the Boardroom Shell Electron UI in development mode with live reload.
- **VS Code Task:** `UI: Start Development`
- **Manual Command:**
  ```powershell
  cd boardroom-shell
  npm run electron-dev
  ```

---

## âš–ï¸ Sovereignty & Governance

### Validate Sovereignty (Sovereignty Suite)
**Purpose:** Run the full suite of sovereignty checks (Network, Dependencies, Crypto, File System, Stress Test, Drift).
- **Manual Command:**
  ```powershell
  pwsh .\scripts\governance\validate_sovereignty.ps1 -All
  ```

### Verify Decision Ledger
**Purpose:** Check the integrity of the tamper-evident decision ledger.
- **Manual Command:**
  ```powershell
  python .\scripts\governance\verify_decision_ledger.py
  ```

---

## ðŸ“‚ Repository Inventory
- **Current Root:** `C:\Users\user\IdeaProjects\sovereign-system`
- **Git Remote:** `https://github.com/PrecisePointway/sovereign-system.git`
- **Branch:** `truth-engine-hardened-v5`

---

## âš ï¸ Important Notes
- **Dirty Workspace:** Your workspace currently has modified files (e.g., `scripts/fleet/orchestrate_fleet.ps1`). The `Sync-SovereignFleet.ps1` script will attempt to `git stash` these before pulling.
- **Docker:** Ensure Docker Desktop is running before starting the full stack.

