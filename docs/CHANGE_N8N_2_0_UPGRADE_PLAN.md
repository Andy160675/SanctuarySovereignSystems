# Change Request: n8n 2.0 Upgrade Plan
## Sovereign System Change Control

---

### Summary

| Field | Value |
|-------|-------|
| **Change ID** | CHG-2025-001 |
| **Subsystem** | n8n Orchestration Layer |
| **Current Version** | 1.x (to be confirmed) |
| **Target Version** | 2.0.x |
| **Status** | PENDING (awaiting stable release) |
| **Risk Level** | MEDIUM |

---

### Timeline (from n8n announcement)

| Milestone | Date | Notes |
|-----------|------|-------|
| 2.0.0 beta | 8 Dec 2025 | Early access, breaking changes active |
| 2.0.x stable | 15 Dec 2025 | Production-ready |
| 1.x support ends | ~15 Mar 2026 | 3 months post-2.0 stable (bug/security only) |

---

### Breaking Changes Reference

**Official Documentation:** `https://docs.n8n.io/2-0-breaking-changes/`

Key areas affected:
- Security enforcement changes
- Storage backend modifications
- Configuration schema changes
- Environment variable changes

---

### Pre-Upgrade Checklist

- [ ] Document current n8n version
- [ ] Export all workflows as JSON
- [ ] Run **Migration Report** (Settings → Migration Report, admin only)
- [ ] Screenshot/export Migration Report findings
- [ ] Hash + store report as evidence in SVC
- [ ] Review breaking changes doc against our workflows
- [ ] Test upgrade on isolated instance first

---

### Evidence Bundle Requirements

When upgrading, create evidence bundle:

```
evidence/n8n-upgrade-2025/
├── pre-upgrade/
│   ├── version.txt           # Current version
│   ├── workflows/*.json      # All exported workflows
│   ├── migration-report.json # Migration Report output
│   └── migration-report.png  # Screenshot
├── breaking-changes-review.md
└── post-upgrade/
    ├── version.txt           # New version
    ├── test-results.json     # Smoke test results
    └── verification.json     # Hash verification
```

---

### Sovereign Integration Notes

n8n's role in the Sovereign System:
- **Commodity orchestration layer** for workflow automation
- Agent flows that need visual editing / rapid prototyping
- Non-critical scheduling and notification pipelines

**NOT for:**
- Constitutional rule enforcement (stays in Guardian)
- Evidence hashing/verification (stays in Core)
- Truth Engine operations (sovereign RAG)
- SVC commits (sovereign version control)

The principle: **n8n choreographs, Sovereign verifies.**

---

### Rollback Plan

1. Stop n8n 2.0 containers
2. Restore 1.x container image
3. Import pre-upgrade workflow JSONs
4. Verify functionality
5. Document incident in SVC

---

### Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| System Owner | | | |
| Security Review | | | |
| Ops Lead | | | |

---

*This change request is tracked under Sovereign System governance.*
*Hash and store this document when upgrade is executed.*
