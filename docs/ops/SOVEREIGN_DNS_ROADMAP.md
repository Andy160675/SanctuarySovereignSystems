# Sovereign DNS Roadmap: NAS Resolver (Phase 2)

**Status:** Proposed / Requirement Identified
**Target Node:** NAS-01 (192.168.4.114)
**Reference:** THE_DIAMOND_DOCTRINE.md, Section 9 (Exit/Transition Criteria)

## 1. Objective
Establish a sovereign DNS resolver on the local NAS to replace dependence on external public resolvers (1.1.1.1, 8.8.8.8) while maintaining controlled internet access.

## 2. Core Requirements
- **Selective Forwarding:** Only forward queries to external resolvers for explicitly approved domains or when local resolution fails.
- **Query Logging:** Record all DNS requests to an immutable ledger for audit (Signal > Noise).
- **Split-Horizon DNS:** Resolve local `.sovereign` or Tailscale names locally.
- **Protocol Enforcement:** Block DNS-over-HTTPS (DoH) and DNS-over-TLS (DoT) at the gateway to ensure visibility of queries.

## 3. Implementation Plan (Future Build)
1. **Containerization:** Deploy `Pi-hole` or `CoreDNS` via Docker on the NAS.
2. **Upstream Config:** Set upstream to trusted resolvers (e.g., Quad9, Unbound).
3. **Integration:** Update `scripts/ops/Set-SovereignDNS.ps1` to point exclusively to .114 without external fallbacks once stability is proven.
4. **Monitoring:** Integrate DNS query logs into the Sovereignty Gate watcher.

## 4. Current State Gap
- NAS at .114 currently pings but fails to resolve external names (Timeout).
- Temporary fix using 1.1.1.1 fallback is active on NODE-MOBILE.
- Doctrine Section 9 requirement: "Sovereign DNS is a hard gate for Phase 2 promotion."
