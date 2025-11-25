# Sovereign System - Multi-PC Air-Gapped LAN Deployment
## SITREP: Live Asset Local Deployment

**Date:** 2025-11-25
**Status:** DEPLOYMENT READY
**Environment:** Air-gapped Local LAN

---

## Network Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AIR-GAPPED LOCAL NETWORK                         │
│                    Subnet: 192.168.50.0/24                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   NODE-01     │          │   NODE-02     │          │   NODE-03     │
│  ORCHESTRATOR │◄────────►│  TRUTH-ENGINE │◄────────►│   AGENTS      │
│ 192.168.50.10 │          │ 192.168.50.20 │          │ 192.168.50.30 │
├───────────────┤          ├───────────────┤          ├───────────────┤
│ - Boardroom   │          │ - txtai       │          │ - Evidence    │
│ - Golden Mstr │          │ - Ollama      │          │ - Property    │
│ - GPG Keys    │          │ - FastAPI     │          │ - Executor    │
│ - Manifest    │          │ - Embeddings  │          │ - Watcher     │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                    │
                         ┌──────────────────┐
                         │   SHARED CORPUS  │
                         │   (SMB/NFS)      │
                         │   Read-Only      │
                         └──────────────────┘
```

---

## Node Assignments

### NODE-01: ORCHESTRATOR (Master)
**IP:** 192.168.50.10
**Role:** Command & Control, Integrity Verification

| Service | Port | Description |
|---------|------|-------------|
| Boardroom Shell | 3000 | UI Dashboard |
| Golden Master | 8080 | Manifest API |
| GPG Verification | - | Key management |

**Containers:**
- `sovereign-boardroom`
- `golden-master-api`

### NODE-02: TRUTH ENGINE
**IP:** 192.168.50.20
**Role:** RAG, Search, LLM Inference

| Service | Port | Description |
|---------|------|-------------|
| Truth Engine | 5050 | FastAPI search |
| Ollama | 11434 | LLM inference |

**Containers:**
- `sovereign-truth`
- `sovereign-ollama`

### NODE-03: AGENT FLEET
**IP:** 192.168.50.30
**Role:** Agent Execution, Processing

| Service | Port | Description |
|---------|------|-------------|
| Executor | - | Agent runner |
| Evidence | - | Evidence validator |
| Property | - | Property analyst |
| Watcher | - | File monitoring |

**Containers:**
- `sovereign-executor`
- `sovereign-evidence`
- `sovereign-property`
- `sovereign-watcher`

---

## Shared Resources

### Corpus Mount (Read-Only)
```
\\192.168.50.10\SOVEREIGN-CORPUS  →  /corpus (ro)
```
- Golden Master manifest
- Document corpus
- Evidence files

### Inter-Node Communication
| From | To | Port | Protocol |
|------|-----|------|----------|
| NODE-01 | NODE-02 | 5050 | HTTP |
| NODE-01 | NODE-03 | 8000 | HTTP |
| NODE-03 | NODE-02 | 5050 | HTTP |
| NODE-03 | NODE-02 | 11434 | HTTP |
| ALL | NODE-01 | 445 | SMB |

---

## Pre-Deployment Checklist

- [ ] All nodes on same subnet (192.168.50.0/24)
- [ ] Static IPs configured
- [ ] Docker installed on all nodes
- [ ] SMB share accessible
- [ ] Firewall rules configured
- [ ] GPG keys distributed
- [ ] USB with deployment package ready

---

## Deployment Order

1. **NODE-01** - Master first (Orchestrator)
2. **NODE-02** - Truth Engine (requires corpus)
3. **NODE-03** - Agents (requires Truth Engine)
