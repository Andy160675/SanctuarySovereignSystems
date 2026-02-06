---
DOCUMENT_ID: SOV-SOP-001
AUTHORITY: Ops Command
REVISION: 1.1
LAST_AUDIT: 2026-02-06
STATUS: AUDITED
---
# SOVEREIGN STANDARD OPERATING PROCEDURES (SOP) - DAILY RHYTHM

## CROSS-VALIDATION DOCTRINE (Core Invariant)
Reliability comes from forcing independent components to agree â€” and treating disagreement as a first-class signal.

### 1. Operational Rules
*   **Independence**: Components must not share hidden assumptions, tooling, or data paths.
*   **Disagreement = Signal**: Never average or suppress divergence. Log it, escalate it, investigate it.
*   **Graceful Degradation**: Loss of a component reduces authority, not safety.
*   **Explicit Accountability**: A human remains the final decision authority. Always attributable.

### 2. Escalation States
*   **Green**: All nodes agree. **Action: Execute.**
*   **Yellow**: Partial disagreement. **Action: Hold + Review.**
*   **Red**: No agreement/Majority disagreement. **Action: Halt + Investigate.**

## 08:00 UTC - INGESTION
1.  **Physical Transfer**: Connect "Air Gap" USB or download via secure channel.
2.  **Sanitization**: Scan files for malware/macros before placing in Inbox.
3.  **Placement**:
    *   Invoices/Contracts -> `Evidence/Inbox`
    *   Property Listings -> `Property/Leads`

## 08:30 UTC - EXECUTION
1.  **Launch**: Run `./launch.sh` (if not running).
2.  **Cross-Validate**: Run task "Ops: Verify Evidence Agreement (Cross-Node)".
    *   **GREEN**: Proceed to Ingest/Analyze.
    *   **YELLOW/RED**: HALT. Human investigation required per Cross-Validation Doctrine.
3.  **Execute**:
    *   `docker-compose run --rm executor python src/agents/evidence_validator.py`
    *   `docker-compose run --rm executor python src/agents/property_analyst.py`

## 09:00 UTC - ADJUDICATION
1.  **Review Console**: Run `python scripts/review_property.py`.
2.  **Decisions**:
    *   **APPROVE**: Only if data is complete, accurate, and conservative.
    *   **REJECT**: Any hallucination, missing risk flag, or over-valuation.
3.  **Evidence Check**: Spot check 1-2 files in `Evidence/Analysis/_verified` to ensure redaction held.

## 17:00 UTC - CLOSE OF BUSINESS
1.  **Audit**: Run `./scripts/sovereign.sh audit` (if available) or check `Governance/Logs/audit_chain.jsonl`.
2.  **Backup**: Run `sovereign-backup.ps1` to mirror state to encrypted drives.
3.  **Shutdown**: `docker-compose down` (if strictly offline overnight).

## WEEKLY MAINTENANCE (FRIDAY)
1.  **Update Code**: `git pull origin main` (if updates available).
2.  **Prune Docker**: `docker system prune -f` to clear old layers.
3.  **Rotate Keys**: If using API keys, rotate them.

