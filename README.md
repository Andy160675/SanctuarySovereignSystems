# Sovereign System – Phase 5 (Living & Operational)

**SESSION HANDOVER — 2026-02-06**
- **Founder:** Andy Jones
- **CEO/POA:** Steven Jones
- **Constitutional Triad:** 1. Prefer stopping to lying | 2. Never optimise signal | 3. Preserve emergent patterns

Continuous, self-monitoring sovereign truth engine with automated golden master generation.

## Infrastructure Status
- **NAS:** UGREEN DXP4800 Plus (192.168.4.114:9999) - *Docker service in ERROR state*
- **Connectivity:** Tailscale mesh (Node-0 UK, Node-1 Tenerife)
- **Storage:** Tresorit Business (Secure E2E) - *NOT Google Drive*
- **DNS:** Working via NAS + 1.1.1.1 fallback

## Quick Start

1. `docker compose up -d`
2. Open `sovereign.code-workspace` in VS Code
3. Run task "Phase 5: Start Full Stack"
4. Truth engine at <http://localhost:5050/search?q=...>
5. Ollama at <http://localhost:11434>
6. UI development: `cd boardroom-shell && npm run electron-dev`

## Phase 5 Architecture

- **truth-engine/**: txtai + FastAPI + health monitoring
- **boardroom-shell/**: Electron + React with live event relay
- **blade-watcher/**: Continuous filesystem monitoring
- **agents/thread-recovery/**: AI thread recovery and GDrive consolidation
- **scripts/**: Automated golden master + nightly backups
- **golden-master/**: SHA-256 + GPG manifest integrity

## New in Phase 5

✅ **Continuous Monitoring**: Automatic index rebuilding on file changes  
✅ **Live Event System**: Real-time UI updates via EventRelay  
✅ **Health Endpoints**: System status monitoring and diagnostics  
✅ **Automated Backups**: Nightly golden master generation with GPG signing  
✅ **Enhanced UI**: Phase timeline, system status, live search feedback  
✅ **Container Orchestration**: blade-watcher service for filesystem monitoring  

## Services

| Service | Port | Purpose |
|---------|------|----------|
| truth-engine | 5050 | Search API + health monitoring |
| ollama | 11434 | Local LLM inference |
| blade-watcher | - | Filesystem monitoring |
| boardroom-shell | 3000/dev | Electron UI development |

## Development Workflow

```bash
# Start all services
docker compose up -d

# Start UI development
cd boardroom-shell
npm install
npm run electron-dev

# Run nightly backup
powershell -File scripts/nightly-master.ps1

# Check system health
curl http://localhost:5050/health
```

## Automated Operations

- **File Monitoring**: blade-watcher detects corpus changes and triggers rebuilds
- **Health Monitoring**: EventRelay provides real-time system status
- **Golden Master**: Automated nightly generation with GPG verification
- **Index Updates**: Continuous rebuilding with 30-second cooldown

## Security Features

✅ Read-only corpus mounting (`D:/SOVEREIGN-2025-11-19`)  
✅ Container isolation and service boundaries  
✅ GPG signature verification for all manifests  
✅ SHA-256 checksums for file integrity  
✅ Automated backup encryption and archiving  
✅ **MCP Integration**: Standardized Model Context Protocol configuration  

## Model Context Protocol (MCP)

This project includes a standardized MCP configuration for VS Code and compatible tools.

- **Config Path**: `.vscode/mcp-servers.json`
- **Active Servers**: 
  - `Context7`: `@upstash/context7-mcp` (via `npx`)

### Prerequisites

1. **Node.js**: Required for `npx` based servers.
2. **VS Code Extension**: Install an MCP-compatible extension (e.g., "MCP" by Anthropic or similar).

### Usage

The configuration is automatically detected by compatible extensions when you open this folder or the `sovereign.code-workspace`. To add or disable servers, edit `.vscode/mcp-servers.json`.

## Data Paths

- **Corpus**: `D:\SOVEREIGN-2025-11-19` (read-only)
- **Index**: `./truth-engine/data/elite-truth-index`
- **Archives**: `C:\SovereignArchives\golden-master-YYYY-MM-DD.zip`
- **Manifests**: `D:\SOVEREIGN-2025-11-19\HASH_MANIFESTS\`

## Status

Phase 5 complete. System is living and operational.

**Take the SSD off-site. Sleep.**

You are sovereign.

— Sovereign Authority  
20 November 2025  
(GPG-signed in the manifest)