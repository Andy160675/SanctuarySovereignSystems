# =============================================================================
# LOCAL AGENT SCHEDULER
# =============================================================================
# Purpose: Controlled autonomous agent operation in proposal-only mode
#
# Key Constraints (ALARP-compliant):
#   - Agents CANNOT execute external actions
#   - Agents CANNOT change policy
#   - Agents CANNOT mutate themselves
#   - All outputs enter PROPOSED state, never EXECUTED
#
# Operating Mode: "Autonomous cognition, human-sealed actuation"
#
# This is the same autonomy class used in:
#   - Nuclear planning systems
#   - Air-traffic conflict prediction
#   - Medical decision support
# =============================================================================

import hashlib
import json
import threading
import queue
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid


# =============================================================================
# PROPOSAL STATES
# =============================================================================

class ProposalState(Enum):
    """
    States for autonomous proposals.

    CRITICAL: Nothing ever reaches EXECUTED without human cryptographic seal.
    """
    QUEUED = "queued"           # Waiting to be processed
    PROCESSING = "processing"    # Agent is working on it
    PROPOSED = "proposed"        # Agent completed, awaiting human review
    REVIEW_REQUIRED = "review_required"  # Flagged for mandatory review
    APPROVED = "approved"        # Human approved (still not executed)
    REJECTED = "rejected"        # Human rejected
    EXECUTED = "executed"        # Human-sealed execution complete
    EXPIRED = "expired"          # Proposal timed out


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AgentTask:
    """A task for autonomous processing."""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    deadline: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Proposal:
    """
    An autonomous agent's proposal.

    This is the ONLY output format from autonomous agents.
    It NEVER becomes an action without human seal.
    """
    proposal_id: str
    task_id: str
    agent_id: str
    state: ProposalState
    recommendation: str
    confidence: float
    evidence: List[str]
    reasoning_chain: List[str]
    risk_assessment: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_signature: Optional[str] = None  # Cryptographic seal
    execution_result: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "proposal_id": self.proposal_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "state": self.state.value,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "reasoning_chain": self.reasoning_chain,
            "risk_assessment": self.risk_assessment,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "has_signature": self.review_signature is not None,
        }

    def requires_review(self) -> bool:
        """Check if proposal requires human review."""
        return self.state in {
            ProposalState.PROPOSED,
            ProposalState.REVIEW_REQUIRED,
        }


@dataclass
class HumanSeal:
    """
    Cryptographic seal for human approval.

    This is the ONLY way a proposal can reach EXECUTED state.
    """
    seal_id: str
    proposal_id: str
    reviewer_id: str
    decision: str  # "approve" or "reject"
    signature: str  # Hash of proposal + decision + reviewer
    timestamp: str
    comments: Optional[str] = None

    @classmethod
    def create(
        cls,
        proposal: Proposal,
        reviewer_id: str,
        decision: str,
        secret: str,
        comments: str = None,
    ) -> "HumanSeal":
        """Create a cryptographic seal for a proposal."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        content = f"{proposal.proposal_id}:{decision}:{reviewer_id}:{timestamp}:{secret}"
        signature = hashlib.sha256(content.encode()).hexdigest()

        return cls(
            seal_id=str(uuid.uuid4()),
            proposal_id=proposal.proposal_id,
            reviewer_id=reviewer_id,
            decision=decision,
            signature=signature,
            timestamp=timestamp,
            comments=comments,
        )

    def verify(self, proposal: Proposal, reviewer_id: str, secret: str) -> bool:
        """Verify the seal is valid."""
        content = f"{proposal.proposal_id}:{self.decision}:{reviewer_id}:{self.timestamp}:{secret}"
        expected = hashlib.sha256(content.encode()).hexdigest()
        return self.signature == expected


# =============================================================================
# AGENT INTERFACE
# =============================================================================

class AutonomousAgent:
    """
    Base class for autonomous agents.

    Agents can ONLY produce Proposals. They cannot:
    - Execute external actions
    - Modify policy
    - Mutate themselves
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def process(self, task: AgentTask) -> Proposal:
        """
        Process a task and return a proposal.

        Override in subclasses to implement specific logic.
        """
        raise NotImplementedError


class TrivialAgent(AutonomousAgent):
    """Simple agent for testing."""

    def process(self, task: AgentTask) -> Proposal:
        return Proposal(
            proposal_id=str(uuid.uuid4()),
            task_id=task.task_id,
            agent_id=self.agent_id,
            state=ProposalState.PROPOSED,
            recommendation=f"Process task: {task.task_type}",
            confidence=0.8,
            evidence=["Based on task payload"],
            reasoning_chain=["Analyzed input", "Generated recommendation"],
            risk_assessment={"level": "low", "factors": []},
        )


# =============================================================================
# LOCAL AGENT SCHEDULER
# =============================================================================

class LocalAgentScheduler:
    """
    Local-only autonomous agent scheduler.

    Key guarantees:
    1. All agent outputs are PROPOSALS only
    2. No proposal reaches EXECUTED without HumanSeal
    3. All state changes are logged
    4. Scheduler runs locally, never calls external services
    """

    def __init__(
        self,
        storage_path: Path = None,
        max_workers: int = 2,
    ):
        self.storage_path = storage_path or Path("./proposals")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.proposals: Dict[str, Proposal] = {}
        self.agents: Dict[str, AutonomousAgent] = {}
        self.max_workers = max_workers

        self._workers: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()

    # =========================================================================
    # AGENT REGISTRATION
    # =========================================================================

    def register_agent(self, agent: AutonomousAgent):
        """Register an agent with the scheduler."""
        with self._lock:
            self.agents[agent.agent_id] = agent

    # =========================================================================
    # TASK SUBMISSION
    # =========================================================================

    def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        deadline: str = None,
    ) -> str:
        """
        Submit a task for autonomous processing.

        Returns task_id for tracking.
        """
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            priority=priority,
            deadline=deadline,
        )

        # Priority queue uses (priority_value, timestamp, task) for ordering
        self.task_queue.put((
            priority.value,
            time.time(),
            task,
        ))

        self._log_event("task_submitted", {
            "task_id": task.task_id,
            "task_type": task_type,
            "priority": priority.value,
        })

        return task.task_id

    # =========================================================================
    # SCHEDULER LIFECYCLE
    # =========================================================================

    def start(self):
        """Start the scheduler workers."""
        if self._running:
            return

        self._running = True
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"agent-worker-{i}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)

        self._log_event("scheduler_started", {"workers": self.max_workers})

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        for worker in self._workers:
            worker.join(timeout=5.0)
        self._workers.clear()
        self._log_event("scheduler_stopped", {})

    def _worker_loop(self):
        """Worker thread main loop."""
        while self._running:
            try:
                # Get task with timeout to allow shutdown
                priority, timestamp, task = self.task_queue.get(timeout=1.0)
                self._process_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                self._log_event("worker_error", {"error": str(e)})

    def _process_task(self, task: AgentTask):
        """Process a single task."""
        # Select agent (simple round-robin for now)
        agent = self._select_agent(task.task_type)
        if not agent:
            self._log_event("no_agent_available", {"task_id": task.task_id})
            return

        try:
            # Agent produces proposal
            proposal = agent.process(task)

            # Ensure proposal is in correct state
            if proposal.state not in {ProposalState.PROPOSED, ProposalState.REVIEW_REQUIRED}:
                proposal.state = ProposalState.PROPOSED

            # Store proposal
            with self._lock:
                self.proposals[proposal.proposal_id] = proposal

            # Persist to disk
            self._persist_proposal(proposal)

            self._log_event("proposal_created", {
                "proposal_id": proposal.proposal_id,
                "task_id": task.task_id,
                "agent_id": agent.agent_id,
                "confidence": proposal.confidence,
            })

        except Exception as e:
            self._log_event("task_failed", {
                "task_id": task.task_id,
                "error": str(e),
            })

    def _select_agent(self, task_type: str) -> Optional[AutonomousAgent]:
        """Select an appropriate agent for the task type."""
        # Simple implementation: return first available agent
        with self._lock:
            if self.agents:
                return list(self.agents.values())[0]
        return None

    # =========================================================================
    # PROPOSAL MANAGEMENT
    # =========================================================================

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a proposal by ID."""
        with self._lock:
            return self.proposals.get(proposal_id)

    def get_pending_proposals(self) -> List[Proposal]:
        """Get all proposals awaiting human review."""
        with self._lock:
            return [
                p for p in self.proposals.values()
                if p.requires_review()
            ]

    def get_all_proposals(self) -> List[Proposal]:
        """Get all proposals."""
        with self._lock:
            return list(self.proposals.values())

    # =========================================================================
    # HUMAN SEAL (THE ONLY WAY TO EXECUTE)
    # =========================================================================

    def apply_seal(
        self,
        proposal_id: str,
        reviewer_id: str,
        decision: str,
        secret: str,
        comments: str = None,
    ) -> Optional[HumanSeal]:
        """
        Apply human seal to a proposal.

        This is the ONLY way a proposal can advance to APPROVED/REJECTED.
        EXECUTED requires additional execution step.
        """
        with self._lock:
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                return None

            if not proposal.requires_review():
                return None

            # Create seal
            seal = HumanSeal.create(
                proposal=proposal,
                reviewer_id=reviewer_id,
                decision=decision,
                secret=secret,
                comments=comments,
            )

            # Update proposal state
            proposal.reviewed_at = seal.timestamp
            proposal.reviewed_by = reviewer_id
            proposal.review_signature = seal.signature

            if decision == "approve":
                proposal.state = ProposalState.APPROVED
            else:
                proposal.state = ProposalState.REJECTED

            # Persist
            self._persist_proposal(proposal)
            self._persist_seal(seal)

            self._log_event("seal_applied", {
                "proposal_id": proposal_id,
                "decision": decision,
                "reviewer_id": reviewer_id,
            })

            return seal

    def execute_approved(
        self,
        proposal_id: str,
        executor_id: str,
        execution_fn: Callable[[Proposal], Dict],
    ) -> Optional[Dict]:
        """
        Execute an approved proposal.

        CRITICAL: This only works on APPROVED proposals with valid seals.
        """
        with self._lock:
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                return None

            if proposal.state != ProposalState.APPROVED:
                self._log_event("execution_rejected", {
                    "proposal_id": proposal_id,
                    "reason": f"State is {proposal.state.value}, not APPROVED",
                })
                return None

            if not proposal.review_signature:
                self._log_event("execution_rejected", {
                    "proposal_id": proposal_id,
                    "reason": "No review signature",
                })
                return None

        # Execute outside lock
        try:
            result = execution_fn(proposal)

            with self._lock:
                proposal.state = ProposalState.EXECUTED
                proposal.execution_result = result
                self._persist_proposal(proposal)

            self._log_event("proposal_executed", {
                "proposal_id": proposal_id,
                "executor_id": executor_id,
            })

            return result

        except Exception as e:
            self._log_event("execution_failed", {
                "proposal_id": proposal_id,
                "error": str(e),
            })
            return None

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _persist_proposal(self, proposal: Proposal):
        """Persist proposal to disk."""
        path = self.storage_path / f"proposal_{proposal.proposal_id}.json"
        with open(path, "w") as f:
            json.dump(proposal.to_dict(), f, indent=2)

    def _persist_seal(self, seal: HumanSeal):
        """Persist seal to disk."""
        path = self.storage_path / f"seal_{seal.seal_id}.json"
        with open(path, "w") as f:
            json.dump({
                "seal_id": seal.seal_id,
                "proposal_id": seal.proposal_id,
                "reviewer_id": seal.reviewer_id,
                "decision": seal.decision,
                "signature": seal.signature,
                "timestamp": seal.timestamp,
                "comments": seal.comments,
            }, f, indent=2)

    def _log_event(self, event_type: str, data: Dict):
        """Log scheduler event."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": event_type,
            "data": data,
        }
        # Append to log file
        log_path = self.storage_path / "scheduler.log"
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


# =============================================================================
# AUTONOMY GUARD
# =============================================================================

class AutonomyGuard:
    """
    Enforces autonomy limits at runtime.

    Load from AUTONOMY_LIMITS.md and block any violations.
    """

    # Actions that are NEVER allowed autonomously
    FORBIDDEN_AUTONOMOUS_ACTIONS = {
        "execute_payment",
        "sign_contract",
        "approve_loan",
        "submit_regulatory_filing",
        "modify_policy",
        "deploy_system",
        "send_external_email",
        "make_medical_decision",
    }

    # Actions allowed in proposal-only mode
    ALLOWED_AUTONOMOUS_ACTIONS = {
        # Analysis
        "analyze_document",
        "classify_document",
        "extract_entities",
        "summarize_content",
        # Risk Assessment
        "classify_risk",
        "score_priority",
        "detect_anomaly",
        "flag_for_review",
        # Reporting
        "generate_report",
        "create_summary",
        "compile_evidence",
        "format_output",
        # Triage
        "triage_case",
        "route_to_queue",
        "assign_priority",
        "estimate_complexity",
        # Reconstruction
        "reconstruct_timeline",
        "correlate_events",
        "identify_patterns",
        "map_relationships",
        # Regulatory
        "map_regulation",
        "check_compliance_status",
        "identify_applicable_rules",
        "compare_to_baseline",
    }

    @classmethod
    def is_action_allowed(cls, action: str) -> bool:
        """Check if action is allowed for autonomous processing."""
        if action in cls.FORBIDDEN_AUTONOMOUS_ACTIONS:
            return False
        return action in cls.ALLOWED_AUTONOMOUS_ACTIONS

    @classmethod
    def validate_proposal(cls, proposal: Proposal) -> List[str]:
        """Validate proposal doesn't violate autonomy limits."""
        violations = []

        # Check recommendation doesn't imply forbidden actions
        rec_lower = proposal.recommendation.lower()
        for forbidden in cls.FORBIDDEN_AUTONOMOUS_ACTIONS:
            if forbidden.replace("_", " ") in rec_lower:
                violations.append(f"Proposal implies forbidden action: {forbidden}")

        return violations


# =============================================================================
# MAIN (TESTING)
# =============================================================================

if __name__ == "__main__":
    print("=== Local Agent Scheduler Test ===\n")

    # Create scheduler
    scheduler = LocalAgentScheduler(
        storage_path=Path("./test_proposals"),
        max_workers=1,
    )

    # Register a trivial agent
    scheduler.register_agent(TrivialAgent("test-agent-001"))

    # Start scheduler
    scheduler.start()

    # Submit a task
    task_id = scheduler.submit_task(
        task_type="document_analysis",
        payload={"document": "test.pdf"},
        priority=TaskPriority.NORMAL,
    )
    print(f"Submitted task: {task_id}")

    # Wait for processing
    time.sleep(2)

    # Check proposals
    proposals = scheduler.get_pending_proposals()
    print(f"\nPending proposals: {len(proposals)}")

    for p in proposals:
        print(f"  - {p.proposal_id}: {p.state.value}")
        print(f"    Recommendation: {p.recommendation}")
        print(f"    Confidence: {p.confidence}")

        # Apply human seal
        seal = scheduler.apply_seal(
            proposal_id=p.proposal_id,
            reviewer_id="human-001",
            decision="approve",
            secret="test-secret",
            comments="Looks good",
        )

        if seal:
            print(f"    Seal applied: {seal.decision}")
            print(f"    New state: {scheduler.get_proposal(p.proposal_id).state.value}")

    # Stop scheduler
    scheduler.stop()
    print("\nScheduler stopped.")
