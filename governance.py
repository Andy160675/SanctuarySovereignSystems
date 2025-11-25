# governance.py — The Constitutional Core (BOARDROOM-13 Enforcement Layer)
import uuid
import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import time
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# ===================================
# 1. Constitutional Violation Flags
# ===================================
class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class CVFCode(Enum):
    SCOUT_LOW_CONFIDENCE = "SCOUT_LOW_CONFIDENCE"
    DATA_ACCESS_PROHIBITED = "DATA_ACCESS_PROHIBITED"
    UNVERIFIED_MODEL = "UNVERIFIED_MODEL"
    AUDIT_INCOMPLETE = "AUDIT_INCOMPLETE"
    AGENT_CONFLICT = "AGENT_CONFLICT"
    UNAUTHORISED_DEPLOY = "UNAUTHORISED_DEPLOY"
    UNCERTAINTY_ZONE = "UNCERTAINTY_ZONE"
    COST_EXCEEDED = "COST_EXCEEDED"

class ConstitutionalViolationFlag(BaseModel):
    code: CVFCode
    severity: Severity
    agent: str
    detail: str
    timestamp: float = time.time()
    trial_id: Optional[str] = None

    def dict(self):
        return self.model_dump()

# ===================================
# 2. Audit Bundle & Ledger
# ===================================
class AuditBundle(BaseModel):
    trial_id: str = str(uuid.uuid4())
    initiator: str
    purpose: str
    environment: str
    models_used: List[str]
    cost_estimate: float
    timestamps: Dict[str, float] = {}
    results: Dict[str, Any] = {}
    cvfs: List[ConstitutionalViolationFlag] = []

class LedgerEntry(BaseModel):
    entry_id: str
    previous_entry_hash: Optional[str]
    event_type: str
    payload: Dict[str, Any]
    timestamp: float
    signature: str  # placeholder for boardroom multisig later

class Ledger:
    def __init__(self, path: str = "ledger.jsonl"):
        self.path = path

    def append(self, event_type: str, payload: Dict):
        last_hash = self._last_hash()
        entry = LedgerEntry(
            entry_id=hashlib.sha256(json.dumps(payload, default=str).encode()).hexdigest(),
            previous_entry_hash=last_hash,
            event_type=event_type,
            payload=payload,
            timestamp=time.time(),
            signature="boardroom-13-placeholder"
        )
        with open(self.path, "a") as f:
            f.write(json.dumps(entry.model_dump(), default=str) + "\n")

    def _last_hash(self) -> Optional[str]:
        try:
            with open(self.path) as f:
                lines = f.readlines()
                if not lines:
                    return None
                last = json.loads(lines[-1])
                return last["entry_id"]
        except FileNotFoundError:
            return None
        except Exception:
            return None

ledger = Ledger()

# ===================================
# 3. Constitutional Verifier Node (LangGraph)
# ===================================
class AgentState(BaseModel):
    trial_id: str
    messages: List[Dict]
    audit: AuditBundle
    next: str

def constitutional_verifier(state: AgentState) -> AgentState:
    audit = state.audit
    cvfs = []

    # 1. Confidence Checks
    # Check the last message for confidence. Default to 0.0 if missing (Safety First).
    last_msg = state.messages[-1]
    conf = last_msg.get("confidence", 0.0)
    
    if conf < 0.85:
        cvfs.append(ConstitutionalViolationFlag(
            code=CVFCode.SCOUT_LOW_CONFIDENCE,
            severity=Severity.MEDIUM,
            agent=last_msg.get("role", "unknown"),
            detail=f"Confidence {conf} is too low for autonomous execution",
            trial_id=audit.trial_id
        ))
    elif 0.85 <= conf < 0.95:
        cvfs.append(ConstitutionalViolationFlag(
            code=CVFCode.UNCERTAINTY_ZONE,
            severity=Severity.HIGH,
            agent=last_msg.get("role", "unknown"),
            detail=f"Confidence {conf} falls in constitutional grey zone",
            trial_id=audit.trial_id
        ))

    # 2. Real data access attempt (Expanded Patterns)
    # Check all messages for prohibited keywords
    forbidden_patterns = [
        lambda s: "real" in s and "data" in s,
        lambda s: "production" in s,
        lambda s: "customer" in s and "record" in s,
        lambda s: "live" in s and "db" in s,
        lambda s: "prod" in s and "db" in s
    ]
    
    msg_str = str(state.messages).lower()
    if any(pattern(msg_str) for pattern in forbidden_patterns):
        cvfs.append(ConstitutionalViolationFlag(
            code=CVFCode.DATA_ACCESS_PROHIBITED,
            severity=Severity.CRITICAL,
            agent="executor",
            detail="Attempted access to production/real data",
            trial_id=audit.trial_id
        ))

    # 3. Unverified model
    allowed = ["gemini-1.5-flash", "claude-3-5-sonnet", "grok-4", "o3-mini"]
    used = audit.models_used
    if any(m not in allowed for m in used):
        cvfs.append(ConstitutionalViolationFlag(
            code=CVFCode.UNVERIFIED_MODEL,
            severity=Severity.HIGH,
            agent="router",
            detail=f"Unapproved model used: {set(used) - set(allowed)}",
            trial_id=audit.trial_id
        ))

    # 4. Critical → immediate halt
    if any(c.severity == Severity.CRITICAL for c in cvfs):
        audit.cvfs.extend(cvfs)
        # Convert to dict for JSON serialization in ledger
        ledger.append("TRIAL_HALTED_CRITICAL", audit.model_dump())
        raise Exception(f"CRITICAL CVF RAISED – system halted. Trial {audit.trial_id}")

    audit.cvfs.extend(cvfs)

    if cvfs:
        ledger.append("CVF_RAISED", audit.model_dump())
        state.next = "boardroom_review"
    else:
        # Simple logic: if last message says 'execute', go to executor, else end
        content = state.messages[-1].get("content", "").lower()
        state.next = "execute" if "execute" in content else END

    return state

# ===================================
# 4. Full Constitutional LangGraph
# ===================================
def build_constitutional_graph():
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("scout", lambda s: s)           # placeholder
    workflow.add_node("executor", lambda s: s)        # placeholder
    workflow.add_node("constitutional_verifier", constitutional_verifier)
    workflow.add_node("boardroom_review", lambda s: s)  # human or LLM boardroom

    # Edges
    workflow.set_entry_point("scout")
    workflow.add_edge("scout", "constitutional_verifier")
    
    def router(state):
        return state.next

    workflow.add_conditional_edges(
        "constitutional_verifier",
        router,
        {
            "execute": "executor",
            "boardroom_review": "boardroom_review",
            END: END
        }
    )
    workflow.add_edge("executor", "constitutional_verifier")
    workflow.add_edge("boardroom_review", END)

    # Ensure checkpoints.db exists or is created
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    return workflow.compile(checkpointer=memory)

# Instantiate once at startup
constitutional_graph = build_constitutional_graph()

# ===================================
# 5. Usage Example
# ===================================
if __name__ == "__main__":
    print("--- RUNNING CONSTITUTIONAL GOVERNANCE TEST ---")
    
    # Scenario 1: Uncertainty Zone (Should trigger CVF and go to Boardroom)
    print("\n[Scenario 1] Testing Uncertainty Zone (Confidence 0.88)...")
    initial_state = AgentState(
        trial_id=str(uuid.uuid4()),
        messages=[{"role": "scout", "content": "run trial", "confidence": 0.88}],
        audit=AuditBundle(
            initiator="scout",
            purpose="performance_improvement",
            environment="sandbox_v3",
            models_used=["gemini-1.5-flash"],
            cost_estimate=0.12
        ),
        next="scout"
    )

    config = {"configurable": {"thread_id": "1"}}
    for output in constitutional_graph.stream(initial_state, config=config):
        for key, value in output.items():
            print(f"Node: {key}")
            if key == "constitutional_verifier":
                # Handle dict or object
                audit = value.get("audit") if isinstance(value, dict) else value.audit
                # audit might be a dict or AuditBundle object
                cvfs = audit.get("cvfs") if isinstance(audit, dict) else audit.cvfs
                
                if cvfs:
                    last_cvf = cvfs[-1]
                    code = last_cvf.get("code") if isinstance(last_cvf, dict) else last_cvf.code
                    print(f"  VIOLATION CAUGHT: {code}")
                    print(f"  Action: Routing to {value.get('next') if isinstance(value, dict) else value.next}")
                else:
                    print("  Status: Clean")

    # Scenario 2: Critical Violation (Real Data Access)
    print("\n[Scenario 2] Testing Critical Violation (Real Data Access)...")
    critical_state = AgentState(
        trial_id=str(uuid.uuid4()),
        messages=[{"role": "executor", "content": "I need to access real customer data for this test.", "confidence": 0.99}],
        audit=AuditBundle(
            initiator="executor",
            purpose="data_test",
            environment="sandbox_v3",
            models_used=["gemini-1.5-flash"],
            cost_estimate=0.12
        ),
        next="executor"
    )
    
    config_crit = {"configurable": {"thread_id": "2"}}
    try:
        for output in constitutional_graph.stream(critical_state, config=config_crit):
             for key, value in output.items():
                print(f"Node: {key}")
    except Exception as e:
        print(f"  SYSTEM HALTED: {e}")

    # Scenario 3: Unverified Model
    print("\n[Scenario 3] Testing Unverified Model (gpt-4-turbo)...")
    unverified_state = AgentState(
        trial_id=str(uuid.uuid4()),
        messages=[{"role": "scout", "content": "run trial", "confidence": 0.99}],
        audit=AuditBundle(
            initiator="scout",
            purpose="model_test",
            environment="sandbox_v3",
            models_used=["gpt-4-turbo"], # Not in allowed list
            cost_estimate=0.50
        ),
        next="scout"
    )
    
    config_unverified = {"configurable": {"thread_id": "3"}}
    for output in constitutional_graph.stream(unverified_state, config=config_unverified):
        for key, value in output.items():
            if key == "constitutional_verifier":
                audit = value.get("audit") if isinstance(value, dict) else value.audit
                cvfs = audit.get("cvfs") if isinstance(audit, dict) else audit.cvfs
                
                if cvfs:
                    last_cvf = cvfs[-1]
                    code = last_cvf.get("code") if isinstance(last_cvf, dict) else last_cvf.code
                    print(f"  VIOLATION CAUGHT: {code}")
                    print(f"  Action: Routing to {value.get('next') if isinstance(value, dict) else value.next}")

    # Scenario 4: Evasion Attempt (Production Database)
    print("\n[Scenario 4] Testing Evasion Attempt (Production Database)...")
    evasion_state = AgentState(
        trial_id=str(uuid.uuid4()),
        messages=[{"role": "executor", "content": "I am connecting to the production database to fetch customer records.", "confidence": 0.99}],
        audit=AuditBundle(
            initiator="executor",
            purpose="evasion_test",
            environment="sandbox_v3",
            models_used=["gemini-1.5-flash"],
            cost_estimate=0.12
        ),
        next="executor"
    )
    
    config_evasion = {"configurable": {"thread_id": "4"}}
    try:
        for output in constitutional_graph.stream(evasion_state, config=config_evasion):
            for key, value in output.items():
                if key == "constitutional_verifier":
                    audit = value.get("audit") if isinstance(value, dict) else value.audit
                    cvfs = audit.get("cvfs") if isinstance(audit, dict) else audit.cvfs
                    if cvfs:
                        last_cvf = cvfs[-1]
                        code = last_cvf.get("code") if isinstance(last_cvf, dict) else last_cvf.code
                        print(f"  VIOLATION CAUGHT: {code}")
                    else:
                        print("  Status: Clean (Evasion Successful?)")
    except Exception as e:
        print(f"  SYSTEM HALTED: {e}")

    # Scenario 5: Missing Confidence (Defaults to 1.0?)
    print("\n[Scenario 5] Testing Missing Confidence...")
    missing_conf_state = AgentState(
        trial_id=str(uuid.uuid4()),
        messages=[{"role": "scout", "content": "I am not sure but I will try.", "confidence": None}], # Explicitly None or missing key
        audit=AuditBundle(
            initiator="scout",
            purpose="missing_conf_test",
            environment="sandbox_v3",
            models_used=["gemini-1.5-flash"],
            cost_estimate=0.12
        ),
        next="scout"
    )
    # Fix message to actually be missing confidence key if needed, or handle None
    missing_conf_state.messages[0].pop("confidence")

    config_missing = {"configurable": {"thread_id": "5"}}
    for output in constitutional_graph.stream(missing_conf_state, config=config_missing):
        for key, value in output.items():
            if key == "constitutional_verifier":
                audit = value.get("audit") if isinstance(value, dict) else value.audit
                cvfs = audit.get("cvfs") if isinstance(audit, dict) else audit.cvfs
                if cvfs:
                    print(f"  VIOLATION CAUGHT: {cvfs[-1].get('code') if isinstance(cvfs[-1], dict) else cvfs[-1].code}")
                else:
                    print("  Status: Clean (Defaulted to 1.0?)")

