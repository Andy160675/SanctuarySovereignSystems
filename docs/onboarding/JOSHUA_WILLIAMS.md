# Joshua Williams Onboarding Playbook

## Overview
This document outlines the staged onboarding process for Joshua Williams to the Sovereign System. Access is granted on a least-privilege basis, expanding as training milestones are achieved.

## Security Requirements
- **Separate Account**: Joshua must use a dedicated GitHub account (not a shared one).
- **2FA**: Two-Factor Authentication (TOTP or Security Key) is MANDATORY.
- **PAT Usage**: All personal access tokens must be encrypted using `Sovereign-PAT-Encrypt.ps1` if used for automation.

## Access Matrix

| Phase | Scope | Repositories | Permissions |
| :--- | :--- | :--- | :--- |
| **1: Initial** | Training & Docs | `sovereign-protocol-docs`, `AGI-Safety-Testing-Standard` | Read-only |
| **2: Junior** | Operations | `sovereign-ops-dashboard`, `meeting-packs` | Triage / Read-write |
| **3: Specialist** | Core Dev | `sovereign-monorepo` (specific branches) | Write (via PR) |
| **4: Full** | Governance | `trinity-os`, `aegis-core-v1` | Maintainer |

## Step-by-Step Checklist

### 1. Account Setup
- [ ] Create GitHub account (e.g., `JoshuaW-Sovereign`).
- [ ] Enable 2FA in GitHub settings.
- [ ] Set up SSH keys for Git operations.

### 2. Initial Access
- [ ] Add as collaborator to Phase 1 repositories.
- [ ] Review `CONSTITUTION.md` and `OPERATOR_CONTRACT.md`.
- [ ] Complete "Initial Safety Briefing" (refer to `AGI-Safety-Testing-Standard`).

### 3. Tooling Installation
- [ ] Install VS Code + Sovereign Workspace.
- [ ] Install Node.js (for MCP tools).
- [ ] Run `.\Install-SovereignTools.ps1` (if available).

### 4. Verification
- [ ] Successfully clone a Phase 1 repo.
- [ ] Successfully load MCP `Context7` server in VS Code.
- [ ] Verify 2FA status with the security team.

## Handover Notes
- Joshua is currently in **Phase 1**.
- Primary point of contact: Sovereign Authority.
