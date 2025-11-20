# 🛡️ SOVEREIGN OFFICER'S WATCH CARD | STATION PC5

**OPERATIONAL STATUS:** `ACTIVE` | **JURISDICTION:** `LOCAL/OFFLINE` | **CONSTITUTION:** `v0.1`

-----

### **1. MORNING PROTOCOL (08:00 UTC)**

  * **INPUT:** Transfer fresh raw data to local directories.
      * `Evidence/Inbox` ← New Invoices/Contracts (PDF)
      * `Property/Leads` ← New Listings/Screenshots (IMG/TXT)
  * **VERIFY:** Check system heartbeat.
    ```bash
    docker ps --format "table {{.Names}}\t{{.Status}}"
    # EXPECT: (healthy) on all 3 containers
    ```
  * **EXECUTE:** Run the Intelligence Batch.
    ```bash
    # 1. Run Stable Agent (Evidence)
    docker-compose run --rm executor python src/agents/evidence_validator.py

    # 2. Run Insider Agent (Property)
    docker-compose run --rm executor python src/agents/property_analyst.py
    ```

-----

### **2. JUDGMENT PROTOCOL (09:00 UTC)**

  * **REVIEW:** Grade the "Insider" Agent.
    ```bash
    python scripts/review_property.py
    ```
      * **[A]pprove:** Only if defects are caught & price is conservative.
      * **[R]eject:** If agent missed a structural defect or hallucinated an address.
  * **AUDIT:** Verify the chain of custody.
    ```bash
    ./scripts/sovereign.sh audit
    # EXPECT: ✅ AUDIT PASSED
    ```
  * **CHECK:** Measure training progress.
    ```bash
    ./scripts/sovereign.sh check
    # NOTE: If Status == READY_FOR_PROMOTION, consult Senior Ops before promoting.
    ```

-----

### **3. CONSTITUTIONAL CHEATSHEET**

| Agent | Track | Output Path | Critical Rule |
| :--- | :--- | :--- | :--- |
| **Evidence** | `STABLE` | `_verified` | Redact PII; No Hallucinations. |
| **Property** | `INSIDER` | `_drafts` | **The Trap:** "Cracks" = Max Score 5. |

-----

### **4. EMERGENCY PROCEDURES (RED ALERT)**

**CODE YELLOW: AGENT DRIFT**
*Symptoms: Agent approving bad files, high error rate.*

1.  **STOP:** Stop adding files to Inbox.
2.  **RESET:** `./scripts/sovereign.sh clean` (Wipes drafts).
3.  **PATCH:** Edit `src/prompts/*_system.md` with new negative constraint.

**CODE RED: LEDGER BREACH**
*Symptoms: Audit script returns "TAMPER DETECTED" or Hash Mismatch.*

1.  **FREEZE:**
    ```bash
    docker-compose down
    ```
2.  **ISOLATE:** Physically disconnect network cable (if connected).
3.  **RESTORE:**
    ```bash
    # Restore from last known good mirror (PC3/PC4)
    robocopy D:\Sovereign_Backups C:\Users\andyj\AI_Agent_Research /MIR
    ```

**CODE BLACK: RUNAWAY PROCESS**
*Symptoms: CPU spike, logs filling disk, agent loop.*

1.  **KILL SWITCH:**
    ```bash
    docker kill $(docker ps -q)
    ```
2.  **PURGE:**
    ```bash
    docker system prune -f
    ```

-----

**COMMANDER'S INTENT:**
*We do not trust the model; we trust the architecture.*
*If in doubt, **REJECT**.*
