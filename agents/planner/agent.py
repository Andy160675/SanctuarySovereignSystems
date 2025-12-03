"""
Planner Agent - Mission decomposition and task orchestration
Breaks high-level objectives into actionable tasks and delegates to executors

Risk Governance Addendum Implementation:
- HIGH risk → REJECTED (mandatory block)
- UNKNOWN risk → PENDING_HUMAN_AUTH (human authorization required)
- LOW/MEDIUM risk → APPROVED (proceed with execution)
- Timeout → PENDING_HUMAN_AUTH (fail-safe to human oversight)

Emergency Freeze (7956):
- /plan endpoint checks freeze state before creating new missions
- Returns HALTED status when GLOBAL_FREEZE=true

EU AI Act Article 14 Compliance: Human oversight preserved at all decision points.
"""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Add shared module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

try:
    from shared.freeze_guard import emergency_freeze_active, get_freeze_status
except ImportError:
    # Fallback if shared module not available
    def emergency_freeze_active() -> bool:
        """Check freeze state from config file directly."""
        import json as _json
        state_path = Path(__file__).parent.parent.parent / "config" / "system_state.json"
        if state_path.exists():
            try:
                with state_path.open() as f:
                    return _json.load(f).get("emergency_freeze", False)
            except Exception:
                return False
        return False

    def get_freeze_status() -> dict:
        return {"emergency_freeze": emergency_freeze_active()}

app = FastAPI(title="Planner Agent", version="2.0.0")

# Configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
ADVOCATE_URL = os.environ.get("ADVOCATE_URL", "http://advocate-agent:8000")
CONFESSOR_URL = os.environ.get("CONFESSOR_URL", "http://confessor-agent:8000")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://ledger_service:8082")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3.2")

# Risk assessment timeout (seconds) - fail-safe to human oversight
RISK_ASSESSMENT_TIMEOUT = int(os.environ.get("RISK_ASSESSMENT_TIMEOUT", "30"))

# In-memory stores (would use Redis/DB in production)
active_plans: Dict[str, "Plan"] = {}
assessment_store: Dict[str, Dict[str, Any]] = {}  # mission_id -> assessment result


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class PlanStatus(str, Enum):
    """Plan lifecycle states per Risk Governance Addendum."""
    CREATED = "created"
    AWAITING_ASSESSMENT = "awaiting_assessment"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_HUMAN_AUTH = "pending_human_auth"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    sequence: int
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class Plan(BaseModel):
    mission_id: str = Field(default_factory=lambda: f"M-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    objective: str
    tasks: List[Task] = []
    status: str = "created"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    current_task_index: int = 0


class MissionRequest(BaseModel):
    objective: str
    context: Optional[str] = None
    jurisdiction: str = "UK"


class TaskCompletionReport(BaseModel):
    task_id: str
    mission_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class PlanResponse(BaseModel):
    mission_id: str
    objective: str
    tasks: List[Task]
    status: str
    risk_level: Optional[str] = None
    risk_reason: Optional[str] = None


class RiskAssessmentCallback(BaseModel):
    """Callback from Confessor with risk assessment result."""
    mission_id: str
    risk_level: str  # LOW, MEDIUM, HIGH, UNKNOWN
    reason: str
    factors: Optional[List[str]] = None


class HumanAuthRequest(BaseModel):
    """Human authorization for PENDING_HUMAN_AUTH plans."""
    mission_id: str
    authorized: bool
    authorizer: str
    reason: Optional[str] = None


# LLM Integration
async def call_ollama(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Call local Ollama instance for reasoning."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            }
            if system_prompt:
                payload["system"] = system_prompt

            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload
            )

            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                print(f"Ollama error: {response.status_code} - {response.text}")
                return ""
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return ""


async def decompose_objective(objective: str, context: Optional[str] = None) -> List[Task]:
    """Use LLM to break down a high-level objective into sequential tasks."""

    system_prompt = """You are a mission planner AI for a sovereign AI system.
Your job is to break down objectives into clear, sequential, actionable tasks.
Each task should be:
- Specific and concrete
- Achievable by a single agent action
- Independent or with clear dependencies
- Auditable and evidence-generating

Output ONLY a numbered list of tasks, nothing else. Format:
1. [Task description]
2. [Task description]
..."""

    user_prompt = f"""Break down this objective into a numbered list of tasks:

Objective: {objective}
"""
    if context:
        user_prompt += f"\nContext: {context}"

    llm_response = await call_ollama(user_prompt, system_prompt)

    tasks = []
    if llm_response:
        lines = llm_response.strip().split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            # Extract task description (remove numbering)
            description = line
            for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '-', '*']:
                if line.startswith(prefix):
                    description = line[len(prefix):].strip()
                    break

            if description:
                tasks.append(Task(
                    sequence=len(tasks) + 1,
                    description=description
                ))

    # Fallback if LLM fails
    if not tasks:
        tasks = [Task(sequence=1, description=f"Execute: {objective}")]

    return tasks


# Ledger Integration
async def log_to_ledger(event_type: str, data: dict):
    """Log planning events to the ledger."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{LEDGER_URL}/append",
                json={
                    "event_type": event_type,
                    "agent": "planner",
                    "action": event_type,
                    "target": data.get("mission_id", "unknown"),
                    "outcome": "logged",
                    "metadata": data
                }
            )
    except Exception as e:
        print(f"Failed to log to ledger: {e}")


async def log_to_evidence(event_type: str, data: dict):
    """Log planning events to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{EVIDENCE_URL}/log",
                json={
                    "event_type": event_type,
                    "agent": "planner",
                    "action": event_type,
                    "target": data.get("mission_id", "unknown"),
                    "outcome": "success",
                    "jurisdiction": data.get("jurisdiction", "UK"),
                    "data": data
                }
            )
    except Exception as e:
        print(f"Failed to log to evidence: {e}")


# Confessor Integration - Risk Assessment with Gating
async def request_risk_assessment(plan: Plan) -> None:
    """
    Request risk assessment from Confessor.
    Confessor will callback to /risk_assessment when complete.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "mission_id": plan.mission_id,
                "objective": plan.objective,
                "callback_url": "http://planner-agent:8000/risk_assessment",
            }
            response = await client.post(
                f"{CONFESSOR_URL}/assess_plan",
                json=payload
            )
            if response.status_code == 200:
                result = response.json()
                # Store assessment if returned synchronously
                if "assessment" in result:
                    assessment = result["assessment"]
                    assessment_store[plan.mission_id] = {
                        "risk_level": assessment.get("risk_level", "UNKNOWN"),
                        "reason": assessment.get("reasoning", "No reason provided"),
                        "factors": assessment.get("risk_factors", []),
                        "received_at": datetime.now(timezone.utc).isoformat()
                    }
                print(f"[planner] Risk assessment requested for {plan.mission_id}")
            else:
                print(f"[planner] Confessor returned {response.status_code}")
    except Exception as e:
        print(f"[planner] Error requesting risk assessment: {e}")


async def wait_for_assessment(mission_id: str, timeout: int = None) -> Dict[str, Any]:
    """
    Wait for risk assessment with timeout.
    Returns assessment dict or UNKNOWN on timeout.

    Per Risk Governance Addendum: timeout → PENDING_HUMAN_AUTH
    """
    timeout = timeout or RISK_ASSESSMENT_TIMEOUT
    start = datetime.now(timezone.utc)

    while (datetime.now(timezone.utc) - start).total_seconds() < timeout:
        if mission_id in assessment_store:
            return assessment_store[mission_id]
        await asyncio.sleep(0.5)

    # Timeout - return UNKNOWN which triggers PENDING_HUMAN_AUTH
    print(f"[planner] Risk assessment timeout for {mission_id} - defaulting to UNKNOWN")
    return {
        "risk_level": "UNKNOWN",
        "reason": f"Assessment timeout after {timeout}s - requires human authorization",
        "factors": ["timeout"],
        "received_at": datetime.now(timezone.utc).isoformat()
    }


def apply_risk_gate(assessment: Dict[str, Any]) -> str:
    """
    Apply risk gating logic per Risk Governance Addendum.

    Returns:
        - APPROVED: LOW or MEDIUM risk → proceed
        - REJECTED: HIGH risk → mandatory block
        - PENDING_HUMAN_AUTH: UNKNOWN risk → requires human authorization
    """
    risk_level = assessment.get("risk_level", "UNKNOWN").upper()

    if risk_level == "HIGH":
        return PlanStatus.REJECTED
    elif risk_level == "UNKNOWN":
        return PlanStatus.PENDING_HUMAN_AUTH
    else:  # LOW, MEDIUM
        return PlanStatus.APPROVED


async def execute_with_risk_gate(mission_id: str):
    """
    Main execution flow with risk gating.

    1. Request risk assessment from Confessor
    2. Wait for assessment (with timeout)
    3. Apply risk gate
    4. Execute if approved, block if rejected, wait for human if unknown
    """
    plan = active_plans.get(mission_id)
    if not plan:
        return

    # Update status
    plan.status = PlanStatus.AWAITING_ASSESSMENT

    # Request assessment from Confessor
    await request_risk_assessment(plan)

    # Wait for assessment result
    assessment = await wait_for_assessment(mission_id)

    # Apply risk gate
    gate_result = apply_risk_gate(assessment)
    plan.status = gate_result

    # Log the gating decision
    await log_to_ledger("risk_gate_decision", {
        "mission_id": mission_id,
        "risk_level": assessment.get("risk_level"),
        "gate_result": gate_result,
        "reason": assessment.get("reason")
    })

    await log_to_evidence("risk_gate_decision", {
        "mission_id": mission_id,
        "risk_level": assessment.get("risk_level"),
        "gate_result": gate_result,
        "reason": assessment.get("reason"),
        "factors": assessment.get("factors", [])
    })

    if gate_result == PlanStatus.APPROVED:
        print(f"[planner] Mission {mission_id} APPROVED - executing")
        # Log plan_approved for CI verification
        await log_to_ledger("plan_approved", {
            "mission_id": mission_id,
            "risk_level": assessment.get("risk_level"),
            "reason": assessment.get("reason")
        })
        await execute_plan(mission_id)
    elif gate_result == PlanStatus.REJECTED:
        print(f"[planner] Mission {mission_id} REJECTED - HIGH risk blocked")
        # Log plan_rejected for CI verification
        await log_to_ledger("plan_rejected", {
            "mission_id": mission_id,
            "risk_level": "HIGH",
            "reason": assessment.get("reason")
        })
    else:  # PENDING_HUMAN_AUTH
        print(f"[planner] Mission {mission_id} PENDING_HUMAN_AUTH - awaiting human authorization")
        await log_to_ledger("plan_hold_unknown_risk", {
            "mission_id": mission_id,
            "risk_level": assessment.get("risk_level"),
            "reason": assessment.get("reason")
        })


# Task Delegation
async def delegate_task_to_advocate(task: Task, mission_id: str) -> bool:
    """Delegate a single task to the Advocate agent."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ADVOCATE_URL}/task",
                json={
                    "task_id": task.id,
                    "mission_id": mission_id,
                    "description": task.description,
                    "sequence": task.sequence
                }
            )

            if response.status_code == 200:
                # Log task_dispatched for audit trail
                await log_to_ledger("task_dispatched", {
                    "mission_id": mission_id,
                    "task_id": task.id,
                    "sequence": task.sequence,
                    "description": task.description[:100],
                    "advocate_response": response.json()
                })
                return True
            else:
                print(f"[planner] Advocate returned {response.status_code} for task {task.id}")
                return False
    except Exception as e:
        print(f"Failed to delegate task {task.id}: {e}")
        return False


# Background Plan Execution
async def execute_plan(mission_id: str):
    """Execute a plan by delegating tasks sequentially."""
    plan = active_plans.get(mission_id)
    if not plan:
        return

    plan.status = PlanStatus.EXECUTING
    await log_to_ledger("plan_execution_started", {"mission_id": mission_id})

    for i, task in enumerate(plan.tasks):
        if task.status == TaskStatus.COMPLETED:
            continue

        plan.current_task_index = i
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc).isoformat()

        await log_to_evidence("task_started", {
            "mission_id": mission_id,
            "task_id": task.id,
            "description": task.description
        })

        # Delegate to advocate
        success = await delegate_task_to_advocate(task, mission_id)

        if success:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc).isoformat()
            task.result = "Delegated successfully"
        else:
            task.status = TaskStatus.FAILED
            task.error = "Failed to delegate to advocate"
            plan.status = PlanStatus.FAILED
            break

        await log_to_evidence("task_completed", {
            "mission_id": mission_id,
            "task_id": task.id,
            "status": task.status
        })

        # Small delay between tasks
        await asyncio.sleep(1)

    if all(t.status == TaskStatus.COMPLETED for t in plan.tasks):
        plan.status = PlanStatus.COMPLETED

    await log_to_ledger("plan_execution_finished", {
        "mission_id": mission_id,
        "status": plan.status,
        "tasks_completed": sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED),
        "tasks_total": len(plan.tasks)
    })


# API Endpoints
@app.get("/health")
async def health():
    freeze_status = get_freeze_status()
    return {
        "status": "healthy",
        "service": "planner",
        "model": MODEL_NAME,
        "emergency_freeze": freeze_status.get("emergency_freeze", False)
    }


@app.get("/freeze_status")
async def get_system_freeze_status():
    """Get current emergency freeze status."""
    return get_freeze_status()


@app.post("/plan", response_model=PlanResponse, status_code=202)
async def create_plan(request: MissionRequest, background_tasks: BackgroundTasks):
    """
    Create a plan from a high-level objective.
    Decomposes the objective into tasks using LLM reasoning.

    Risk Governance Addendum Flow:
    1. Decompose objective into tasks
    2. Request risk assessment from Confessor
    3. Apply risk gate (HIGH→reject, UNKNOWN→human auth, LOW/MEDIUM→approve)
    4. Execute only if approved
    """
    # EMERGENCY FREEZE CHECK (7956)
    if emergency_freeze_active():
        # Return a valid PlanResponse but with HALTED status
        return PlanResponse(
            mission_id=f"M-HALTED-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            objective=request.objective,
            tasks=[],
            status="HALTED",
            risk_level="BLOCKED",
            risk_reason="SYSTEM_EMERGENCY_FREEZE_ACTIVE - All mission creation is blocked"
        )

    # Decompose objective into tasks
    tasks = await decompose_objective(request.objective, request.context)

    # Create plan
    plan = Plan(
        objective=request.objective,
        tasks=tasks,
        status=PlanStatus.CREATED
    )

    # Store plan
    active_plans[plan.mission_id] = plan

    # Log plan creation
    await log_to_ledger("plan_created", {
        "mission_id": plan.mission_id,
        "objective": plan.objective,
        "task_count": len(tasks),
        "jurisdiction": request.jurisdiction
    })

    await log_to_evidence("plan_created", {
        "mission_id": plan.mission_id,
        "objective": plan.objective,
        "tasks": [t.dict() for t in tasks],
        "jurisdiction": request.jurisdiction
    })

    # Start risk-gated execution in background
    # This will: request assessment → wait → apply gate → execute if approved
    background_tasks.add_task(execute_with_risk_gate, plan.mission_id)

    return PlanResponse(
        mission_id=plan.mission_id,
        objective=plan.objective,
        tasks=plan.tasks,
        status=plan.status
    )


@app.get("/plan/{mission_id}", response_model=PlanResponse)
async def get_plan(mission_id: str):
    """Get the status of a plan."""
    plan = active_plans.get(mission_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return PlanResponse(
        mission_id=plan.mission_id,
        objective=plan.objective,
        tasks=plan.tasks,
        status=plan.status
    )


@app.get("/plans")
async def list_plans():
    """List all active plans."""
    return {
        "plans": [
            {
                "mission_id": p.mission_id,
                "objective": p.objective[:50] + "..." if len(p.objective) > 50 else p.objective,
                "status": p.status,
                "tasks_total": len(p.tasks),
                "tasks_completed": sum(1 for t in p.tasks if t.status == TaskStatus.COMPLETED)
            }
            for p in active_plans.values()
        ]
    }


@app.post("/task_complete")
async def handle_task_completion(report: TaskCompletionReport):
    """
    Callback from executor agents when a task is complete.
    Updates plan state and triggers next task if available.
    """
    plan = active_plans.get(report.mission_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Find and update the task
    for task in plan.tasks:
        if task.id == report.task_id:
            task.status = TaskStatus.COMPLETED if report.success else TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc).isoformat()
            task.result = report.result
            task.error = report.error
            break

    await log_to_evidence("task_completion_received", {
        "mission_id": report.mission_id,
        "task_id": report.task_id,
        "success": report.success
    })

    return {"status": "acknowledged", "mission_id": report.mission_id}


@app.delete("/plan/{mission_id}")
async def cancel_plan(mission_id: str):
    """Cancel an active plan."""
    plan = active_plans.get(mission_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.status = PlanStatus.CANCELLED

    await log_to_ledger("plan_cancelled", {"mission_id": mission_id})

    return {"status": "cancelled", "mission_id": mission_id}


# Risk Governance Addendum Endpoints

@app.post("/risk_assessment")
async def receive_risk_assessment(callback: RiskAssessmentCallback):
    """
    Callback endpoint for Confessor to deliver risk assessment results.
    This allows asynchronous assessment delivery.
    """
    assessment_store[callback.mission_id] = {
        "risk_level": callback.risk_level,
        "reason": callback.reason,
        "factors": callback.factors or [],
        "received_at": datetime.now(timezone.utc).isoformat()
    }

    print(f"[planner] Received risk assessment for {callback.mission_id}: {callback.risk_level}")

    await log_to_ledger("risk_assessment_received", {
        "mission_id": callback.mission_id,
        "risk_level": callback.risk_level,
        "reason": callback.reason
    })

    return {"status": "received", "mission_id": callback.mission_id}


@app.post("/human_auth")
async def authorize_plan(auth: HumanAuthRequest, background_tasks: BackgroundTasks):
    """
    Human authorization endpoint for PENDING_HUMAN_AUTH plans.

    Per Risk Governance Addendum:
    - Only plans in PENDING_HUMAN_AUTH state can be authorized
    - Authorization decision is logged with authorizer identity
    - Audit trail preserved for EU AI Act Article 14 compliance
    """
    plan = active_plans.get(auth.mission_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.status != PlanStatus.PENDING_HUMAN_AUTH:
        raise HTTPException(
            status_code=400,
            detail=f"Plan is not pending human authorization (current status: {plan.status})"
        )

    # Log the authorization decision
    await log_to_ledger("human_authorization", {
        "mission_id": auth.mission_id,
        "authorized": auth.authorized,
        "authorizer": auth.authorizer,
        "reason": auth.reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    await log_to_evidence("human_authorization", {
        "mission_id": auth.mission_id,
        "authorized": auth.authorized,
        "authorizer": auth.authorizer,
        "reason": auth.reason,
        "eu_ai_act_article_14": "human_oversight_preserved"
    })

    if auth.authorized:
        print(f"[planner] Mission {auth.mission_id} AUTHORIZED by {auth.authorizer} - executing")
        plan.status = PlanStatus.APPROVED
        # Start execution
        background_tasks.add_task(execute_plan, auth.mission_id)
        return {
            "status": "authorized",
            "mission_id": auth.mission_id,
            "authorizer": auth.authorizer,
            "message": "Plan authorized and execution started"
        }
    else:
        print(f"[planner] Mission {auth.mission_id} DENIED by {auth.authorizer}")
        plan.status = PlanStatus.REJECTED
        return {
            "status": "denied",
            "mission_id": auth.mission_id,
            "authorizer": auth.authorizer,
            "message": "Plan denied by human authorizer"
        }


@app.get("/pending_auth")
async def list_pending_authorizations():
    """
    List all plans pending human authorization.
    UI can poll this endpoint to show authorization queue.
    """
    pending = [
        {
            "mission_id": p.mission_id,
            "objective": p.objective,
            "task_count": len(p.tasks),
            "created_at": p.created_at,
            "risk_assessment": assessment_store.get(p.mission_id, {})
        }
        for p in active_plans.values()
        if p.status == PlanStatus.PENDING_HUMAN_AUTH
    ]
    return {"pending_authorizations": pending, "count": len(pending)}


@app.get("/continue_prompt/{mission_id}")
async def get_continue_prompt(mission_id: str):
    """
    Generate a safe resume prompt for halted/pending missions.
    Used by operators to craft follow-up missions or responses.

    Returns:
    - Mission context
    - Risk assessment details
    - Suggested safer alternatives
    - Timeline from ledger (if available)
    """
    plan = active_plans.get(mission_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    assessment = assessment_store.get(mission_id, {})

    # Try to get timeline from Watcher
    timeline = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://watcher-agent:8000/mission/{mission_id}/timeline")
            if resp.status_code == 200:
                timeline = resp.json().get("events", [])
    except Exception:
        pass

    # Generate continuation context
    prompt = {
        "mission_id": mission_id,
        "objective": plan.objective,
        "status": plan.status,
        "tasks": [{"sequence": t.sequence, "description": t.description, "status": t.status} for t in plan.tasks],
        "risk_assessment": {
            "risk_level": assessment.get("risk_level", "UNKNOWN"),
            "reason": assessment.get("reason", "No assessment available"),
            "factors": assessment.get("factors", [])
        },
        "timeline": timeline[-10:] if timeline else [],
        "continuation_options": []
    }

    # Suggest options based on status
    if plan.status == PlanStatus.PENDING_HUMAN_AUTH:
        prompt["continuation_options"] = [
            {
                "action": "approve",
                "description": "Authorize execution if risk is acceptable",
                "endpoint": f"POST /human_auth",
                "payload": {"mission_id": mission_id, "authorized": True, "authorizer": "<your_id>", "reason": "<justification>"}
            },
            {
                "action": "reject",
                "description": "Reject execution and archive mission",
                "endpoint": f"POST /human_auth",
                "payload": {"mission_id": mission_id, "authorized": False, "authorizer": "<your_id>", "reason": "<justification>"}
            },
            {
                "action": "resubmit",
                "description": "Create a modified, lower-risk mission",
                "endpoint": "POST /plan",
                "suggestion": f"Consider rephrasing: '{plan.objective}' with more specific constraints"
            }
        ]
    elif plan.status == PlanStatus.REJECTED:
        prompt["continuation_options"] = [
            {
                "action": "resubmit_safer",
                "description": "Submit a modified mission with reduced scope",
                "endpoint": "POST /plan",
                "suggestion": "Break this objective into smaller, verifiable steps"
            }
        ]

    return prompt


class AmendmentVoteRequest(BaseModel):
    amendment_id: str
    proposal_id: str
    target_file: str
    new_content: str
    justification: str
    proposer: Optional[str] = None


class AmendmentVoteResponse(BaseModel):
    vote: str  # "AGREE", "DISAGREE", "ABSTAIN"
    reasoning: str


@app.post("/vote_on_amendment", response_model=AmendmentVoteResponse)
async def vote_on_amendment(request: AmendmentVoteRequest):
    """
    Vote on a proposed constitutional amendment.

    The Planner evaluates amendments from a STRATEGIC perspective:
    - Does this change improve mission planning capabilities?
    - Does it maintain appropriate governance structure?
    - Will this help achieve objectives more effectively?
    """
    print(f"[planner] Voting on amendment {request.amendment_id}")

    vote_prompt = f"""You are the Planner agent in a governed AI system.
You must vote on a proposed constitutional amendment.

Your role is to assess STRATEGIC IMPACT - evaluate whether this change:
- Improves mission planning and decomposition capabilities
- Maintains appropriate governance and oversight structure
- Helps achieve objectives more effectively and safely
- Preserves the ability to coordinate with other agents

Amendment Details:
- Target file: {request.target_file}
- Justification: {request.justification}
- Proposer: {request.proposer or 'unknown'}

Proposed new content (excerpt):
{request.new_content[:500]}

Respond in JSON format:
{{"vote": "AGREE" or "DISAGREE" or "ABSTAIN", "reasoning": "brief explanation"}}

Only respond with the JSON object."""

    # Call Ollama for reasoning
    import json as _json
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": vote_prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                response_text = response.json().get("response", "").strip()
            else:
                response_text = ""
    except Exception as e:
        print(f"[planner] Error calling Ollama for amendment vote: {e}")
        response_text = ""

    # Parse response
    vote = "ABSTAIN"
    reasoning = "Unable to process amendment vote"

    try:
        if response_text:
            if "```" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    response_text = response_text[json_start:json_end]

            result = _json.loads(response_text)
            vote = result.get("vote", "ABSTAIN").upper()
            reasoning = result.get("reasoning", "No reasoning provided")

            if vote not in ["AGREE", "DISAGREE", "ABSTAIN"]:
                vote = "ABSTAIN"
    except Exception:
        # Fallback: extract vote from text
        if response_text:
            response_upper = response_text.upper()
            if "AGREE" in response_upper and "DISAGREE" not in response_upper:
                vote = "AGREE"
            elif "DISAGREE" in response_upper:
                vote = "DISAGREE"
            reasoning = f"Extracted from response: {response_text[:200]}"

    # Log the vote to ledger
    await log_to_ledger("amendment_vote", {
        "mission_id": request.amendment_id,
        "agent": "planner",
        "vote": vote,
        "reasoning": reasoning[:200]
    })

    print(f"[planner] Vote on {request.amendment_id}: {vote}")

    return AmendmentVoteResponse(vote=vote, reasoning=reasoning)


@app.on_event("startup")
async def startup_event():
    """Log planner startup."""
    print(f"[planner] Starting up (v2.0.0 - Risk Governance Addendum)...")
    await log_to_ledger("agent_lifecycle", {
        "agent": "planner",
        "action": "startup",
        "version": "2.0.0",
        "risk_gating": "enabled",
        "timeout_sec": RISK_ASSESSMENT_TIMEOUT
    })
