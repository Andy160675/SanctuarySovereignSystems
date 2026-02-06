# CSS-ARCH-DOC-001 — Sovereign Systems Architecture
**Version:** 1.0.0
**Date:** 2026-02-06
**Status:** Pending Steven Review

## 1. Executive Summary
This document defines the technical architecture for the Sovereign System, focusing on local-first infrastructure, secure mesh networking, and deterministic governance.

## 2. Infrastructure
### 2.1 Storage & Compute
- **Primary NAS:** UGREEN DXP4800 Plus (UGOS Pro, Debian 12)
- **IP:** 192.168.4.114:9999
- **Service State:** Docker service requires manual restart via UI after admin password reset.

### 2.2 Networking
- **Mesh:** Tailscale (connecting Node-0 UK and Node-1 Tenerife).
- **DNS:** Primary via NAS, fallback to 1.1.1.1.
- **10GbE:** Tuned with jumbo frames and optimized buffers.

### 2.3 Cloud Strategy
- **Provider:** Tresorit Business (Swiss-based, zero-knowledge, E2E).
- **Prohibition:** Google Drive is strictly forbidden for sovereign data.

## 3. Deployment Topology
- **Node-0 (UK):** Primary Command Node.
- **Node-1 (Tenerife):** Operational Node.
- **Pi-hole:** To be deployed via UGOS Docker UI for local DNS filtering.

## 4. Integrity
- SHA-256 + GPG manifest integrity for all architectural artifacts.
