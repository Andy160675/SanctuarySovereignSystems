# Sovereign Network Binding Table (v1.1 Reconciliation)

This table binds logical Pentad roles to physical network endpoints.

| Pentad Role | Physical IP | Hostname | Tailscale IP | Status |
| :--- | :--- | :--- | :--- | :--- |
| **PC-A (Constitutional)** | 192.168.4.137 | MIND | 100.102.37.106 | ✅ Reconciled |
| **PC-B (Orchestration)** | 192.168.4.124 | HEART | 100.96.222.82 | ✅ Reconciled |
| **PC-C (Verification)** | 192.168.4.136 | EYES | 100.94.217.82 | ✅ Reconciled |
| **PC-D (Analytics)** | 192.168.4.117 | backdrop3 | 100.102.223.88 | ✅ Reconciled |
| **PC-E (Safety)** | ? | pc5 | 100.88.25.122 | ⏳ Pending |
| **NAS (Memory Spine)** | 192.168.4.78 | DXP4800PLUS | - | ✅ Reconciled |
| **Gateway** | 192.168.4.1 | UNKNOWN | - | ✅ Reconciled |

## Note on Conflicts
- The user's 'Network Map v1.1' identifies **192.168.4.78** as **NAS Primary**.
- **192.168.4.117** is **PC4**.
- **192.168.4.124** is **PC3 Relay**.
- **192.168.4.137** was identified as **DESKTOP-V20CP12** in the scan.

*Last Updated: 2026-02-05*
