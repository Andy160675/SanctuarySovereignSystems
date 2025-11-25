# DAY 1 – SOVEREIGN AGENT DEPLOYMENT CHECKLIST

_Date: __________________ | Operator: ___________________

Purpose:
Prove, in one sitting, that the Sovereign Agent stack runs in **Insider (safe)** mode end-to-end with:

- Correct directory isolation
- Router obeying TRACK=insider
- VS Code extension showing drafts
- Audit log + readiness script working

---

## 0. PREP – MACHINE & REPO STATE

- [ ] Git working and clean (no uncommitted critical changes)
- [ ] Docker installed and running
- [ ] Python 3.10+ available (`python --version`)
- [ ] Node + npm installed for VS Code extension
- [ ] Repo opened in VS Code at repo root

Sanity check:

- [ ] You can see `docker-compose-unified.yml` in the repo
- [ ] You can see `agent_router.py` in `src/` or `src/utils/`
- [ ] You can see `calculate_readiness.py` and `sovereign.sh` in the repo root
- [ ] You can see the VS Code extension scaffold (`package.json`, `src/extension.ts`, etc.)

---

## 1. DIRECTORY SCHEMA – CREATE THE WALLS

From the repo root, create the minimum directories:

```bash
mkdir -p Evidence/Inbox
mkdir -p Evidence/Analysis/_drafts
mkdir -p Evidence/Analysis/_verified

mkdir -p Property/Leads
mkdir -p Property/Scored/_drafts
mkdir -p Property/Scored/_production

mkdir -p Governance/Logs
```

Verify:

- Evidence/Inbox exists
- Evidence/Analysis/_drafts exists
- Evidence/Analysis/_verified exists
- Property/Leads and Property/Scored/_drafts exist
- Governance/Logs exists

These MUST match what agent_router.py and Docker volumes expect.

## 2. ENVIRONMENT – FORCE INSIDER MODE

Create or update .env in the repo root:

```ini
TRACK=insider
WRITE_MODE=draft

EVIDENCE_TRACK=insider
PROPERTY_TRACK=insider
```

Checks:

- .env file exists at repo root
- TRACK=insider (default should never be stable)
- No stable anywhere in .env for Day 1

## 3. DOCKER – BRING UP INSIDER AGENTS ONLY

Open docker-compose-unified.yml and verify:

- agent-evidence-insider service exists and mounts:
  - ./Evidence:/data/evidence:ro
  - ./Evidence/Analysis/_drafts:/data/output
- agent-property-insider service exists and mounts:
  - ./Property/Leads:/data/leads:ro
  - ./Property/Scored/_drafts:/data/output
- vscode-bridge service exists and exposes port 5173

Then run:

```bash
docker-compose -f docker-compose-unified.yml up -d
```

Confirm:

- docker ps shows evidence-insider
- docker ps shows property-insider
- No stable containers running yet

## 4. ROUTER – VERIFY IT OBEYS TRACK=INSIDER

Check agent_router.py:

- Uses TRACK = os.getenv("TRACK", "insider")
- For agent_type='evidence':
  - Base root: /data/evidence
  - Insider → Analysis/_drafts
  - Stable → Analysis/_verified
- For agent_type='property':
  - Base root: /data/property
  - Insider → Scored/_drafts
  - Stable → Scored/_production

Run a one-shot test inside the evidence container:

```bash
docker exec -it evidence-insider python -c "from agent_router import SovereignRouter; r=SovereignRouter('evidence'); print(r.track, r.get_execution_mode()); r.save_result('test_doc.json', {'ping':'pong'})"
```

Expected:

- Output shows insider SANDBOX
- A file appears at Evidence/Analysis/_drafts/test_doc.json
- No file appears in _verified

If any write lands in _verified in Insider mode, stop – router is misconfigured.

## 5. VS CODE EXTENSION – HUMAN GATE ONLINE

In VS Code:

- package.json defines:
  - viewsContainers.activitybar with id sovereign-governance
  - View sovereign-evidence-view
  - Commands sovereign.approveDraft and sovereign.rejectDraft
- src/extension.ts (or out/extension.js after build) includes:
  - SovereignDraftsProvider
  - handleDecision('APPROVE' | 'REJECT', fileData)
  - Writes to Governance/Logs/audit-insider.jsonl

Install deps & run extension host:

```bash
npm install
npm run compile # or equivalent
```

Then press F5 (Launch Extension) in VS Code.

Checks inside the Extension host window:

- New activity bar icon: “Sovereign Boardroom”
- Clicking it shows “Insider Drafts (Pending Review)”
- You see test_doc.json in the list (or create a couple more by running the agent)

## 6. HUMAN REVIEW – CREATE REAL AUDIT EVENTS

Inside the Sovereign panel:

- Click Promote ✅ on at least a few drafts
- Click Reject ❌ on at least one draft

Then check the filesystem:

- Approved files moved from Evidence/Analysis/_drafts → _verified
- Rejected files moved from _drafts → _rejected (if configured)
- Governance/Logs/audit-insider.jsonl exists and contains JSONL entries

Quick content check:

```bash
head Governance/Logs/audit-insider.jsonl
```

You should see lines with:

- decision: "APPROVE" / "REJECT"
- filename: matching the draft
- timestamp: ISO string

## 7. READINESS SCRIPT – MEASURE, DON’T GUESS

Run the CHECK phase script from repo root:

```bash
python calculate_readiness.py
```

Expected:

- Script prints “Analyzing Insider Audit Logs…”
- It writes readiness_report.json in repo root
- You see entries for at least evidence-validator with:
  - status: CALIBRATING or READY_FOR_PROMOTION
  - metrics.accuracy field
  - metrics.samples_collected number

Day 1 goal is NOT to be ready for promotion. Day 1 goal is:

- Readiness report exists and is correct
- Accuracy < threshold is accepted as truth, not a failure

## 8. CLI WRAPPER – PROMOTION COMMAND (DRY RUN)

Make sovereign.sh executable:

```bash
chmod +x sovereign.sh
```

Run a dry check:

```bash
./sovereign.sh check
./sovereign.sh promote evidence-validator
```

Expected:

- check runs and prints the same numbers as calculate_readiness.py
- promote refuses if status != READY_FOR_PROMOTION
- .env is unchanged on Day 1 (still TRACK=insider)

If promote tries to switch to stable before the threshold is met, treat that as a bug.

## 9. EVIDENCE SNAPSHOT – LOCK THE PROOF

Before you close for the day:

- Commit all new files:
  - agent_router.py
  - calculate_readiness.py
  - sovereign.sh
  - VS Code extension files
  - DAY1_CHECKLIST.md (this file)
- Run tests / simple script checks if you have them
- Capture a screenshot of:
  - VS Code “Insider Drafts” pane with a promoted item
  - Terminal showing calculate_readiness.py output

Optional but recommended:

- Tag the commit: git tag sovereign-day1-insider

## 10. DAY 1 EXIT CRITERIA

You can tick “Day 1 Complete” only if ALL of these are true:

- Agents can run in Docker in Insider mode without touching production directories
- Router writes to _drafts only when TRACK=insider
- VS Code shows drafts and allows Approve/Reject
- Audit log is generated in Governance/Logs/audit-insider.jsonl
- calculate_readiness.py produces readiness_report.json
- sovereign.sh promote refuses to promote when below threshold

If any of these fail, you are still in pre-Day-1. Fix, repeat, and only then claim Day 1.

Operator Note:

This checklist is not theatre. It’s the minimum proof that “agents + governance + human gate” exist as real, testable code on a single node.

You can drop that in the repo as `DAY1_CHECKLIST.md` or `README-SOVEREIGN-DAY1.md`. From there, the next logical artifact is a similar **Day 2: Promotion & Stable Track** checklist once you’re actually hitting the accuracy thresholds.