# =============================================================================
# GOVERNANCE CONFIG - Single Source of Truth
# =============================================================================
# This file is the ONLY source for:
#   - Active operational phase
#   - Allowed autonomy levels per agent
#   - Forbidden capabilities
#   - Cost thresholds and rate limits
#
# ISO/IEC 42001 Alignment:
#   - Annex A A.2: Policies related to AI systems
#   - Clause 5: Leadership and commitment (policy ownership)
#
# IMPORTANT: Changes to this file require:
#   1. Pull request with justification
#   2. CI pipeline must pass (including red-team tests)
#   3. Human review approval
# =============================================================================

from enum import Enum
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime


# =============================================================================
# OPERATIONAL PHASES
# =============================================================================

class Phase(Enum):
    """
    Deployment phases with increasing autonomy.

    Phase 1.0: Full human control, AI only suggests
    Phase 1.5: Supervised autonomy, human approves actions
    Phase 2.0: Bounded autonomy within guardrails
    Phase 3.0: Full autonomy (not yet authorized)
    """
    PHASE_1_0 = "1.0"  # Human control
    PHASE_1_5 = "1.5"  # Supervised autonomy (CURRENT)
    PHASE_2_0 = "2.0"  # Bounded autonomy
    PHASE_3_0 = "3.0"  # Full autonomy (LOCKED)


# =============================================================================
# CURRENT CONFIGURATION
# =============================================================================

# Active phase - THE source of truth
ACTIVE_PHASE = Phase.PHASE_1_5

# Human-in-the-loop requirements by phase
PHASE_REQUIREMENTS = {
    Phase.PHASE_1_0: {
        "human_approval_required": True,
        "auto_execute_allowed": False,
        "description": "Full human control - AI suggests only",
    },
    Phase.PHASE_1_5: {
        "human_approval_required": True,
        "auto_execute_allowed": False,
        "description": "Supervised autonomy - human approves all actions",
    },
    Phase.PHASE_2_0: {
        "human_approval_required": False,
        "auto_execute_allowed": True,
        "description": "Bounded autonomy within guardrails",
    },
    Phase.PHASE_3_0: {
        "human_approval_required": False,
        "auto_execute_allowed": True,
        "description": "Full autonomy - NOT AUTHORIZED",
    },
}


# =============================================================================
# AUTONOMY LEVELS
# =============================================================================

class AutonomyLevel(Enum):
    """Agent autonomy levels."""
    NONE = 0        # Cannot act, only report
    SUGGEST = 1     # Can suggest actions, cannot execute
    EXECUTE_SAFE = 2  # Can execute pre-approved safe actions
    EXECUTE_ALL = 3   # Can execute any allowed action
    FULL = 4        # Full autonomy (LOCKED)


# Agent autonomy assignments for Phase 1.5
AGENT_AUTONOMY = {
    "advocate": AutonomyLevel.SUGGEST,
    "confessor": AutonomyLevel.EXECUTE_SAFE,  # Can read ledger, write reports
    "scout": AutonomyLevel.SUGGEST,
    "executor": AutonomyLevel.NONE,  # Disabled in Phase 1.5
}


# =============================================================================
# FORBIDDEN CAPABILITIES
# =============================================================================

# Capabilities that are NEVER allowed regardless of phase
FORBIDDEN_CAPABILITIES: Set[str] = {
    # Model manipulation
    "model_training",
    "model_fine_tuning",
    "weight_modification",

    # Production data access
    "production_database_write",
    "production_database_delete",
    "customer_pii_access",
    "real_data_export",

    # System manipulation
    "system_config_modify",
    "security_bypass",
    "audit_log_delete",
    "ledger_modify",

    # External communication
    "external_api_unrestricted",
    "email_send",
    "webhook_arbitrary",

    # Privilege escalation
    "admin_grant",
    "role_escalation",
    "phase_override",
}

# Capabilities restricted by phase (allowed in higher phases)
PHASE_RESTRICTED_CAPABILITIES: Dict[Phase, Set[str]] = {
    Phase.PHASE_1_0: {
        "auto_execute",
        "batch_process",
        "scheduled_task",
    },
    Phase.PHASE_1_5: {
        "auto_execute",  # Still restricted
        "batch_process",  # Still restricted
    },
    Phase.PHASE_2_0: set(),  # Most restrictions lifted
    Phase.PHASE_3_0: set(),  # All restrictions lifted
}


# =============================================================================
# ALLOWED CAPABILITIES
# =============================================================================

ALLOWED_CAPABILITIES: Set[str] = {
    # Read operations
    "read_logs",
    "read_ledger",
    "read_config",
    "read_sandbox_data",

    # Analysis operations
    "analyze_document",
    "analyze_property",
    "generate_report",
    "calculate_metrics",

    # Safe write operations
    "write_sandbox",
    "write_report",
    "append_ledger",  # Append-only, no modify

    # Status operations
    "health_check",
    "status_query",
    "list_agents",
}


# =============================================================================
# COST AND RATE LIMITS
# =============================================================================

@dataclass
class CostLimits:
    """Cost thresholds for operations."""
    max_per_request_usd: float = 0.50
    max_per_hour_usd: float = 5.00
    max_per_day_usd: float = 50.00
    alert_threshold_percent: float = 80.0


@dataclass
class RateLimits:
    """Rate limits for operations."""
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_tool_calls_per_request: int = 10
    max_tokens_per_request: int = 8000


COST_LIMITS = CostLimits()
RATE_LIMITS = RateLimits()


# =============================================================================
# APPROVED MODELS
# =============================================================================

APPROVED_MODELS: Set[str] = {
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "claude-3-5-sonnet",
    "claude-3-haiku",
    "grok-4",
    "o3-mini",
    # Local models via Ollama
    "llama3:8b",
    "mistral:7b",
    "codellama:13b",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_active_phase() -> Phase:
    """Get the current active phase."""
    return ACTIVE_PHASE


def get_phase_id() -> str:
    """Get the current phase ID as string."""
    return ACTIVE_PHASE.value


def get_phase_requirements() -> dict:
    """Get requirements for current phase."""
    return PHASE_REQUIREMENTS[ACTIVE_PHASE]


def is_human_approval_required() -> bool:
    """Check if human approval is required in current phase."""
    return PHASE_REQUIREMENTS[ACTIVE_PHASE]["human_approval_required"]


def get_agent_autonomy(agent_name: str) -> AutonomyLevel:
    """Get autonomy level for an agent."""
    return AGENT_AUTONOMY.get(agent_name, AutonomyLevel.NONE)


def is_capability_allowed(capability: str) -> bool:
    """Check if a capability is allowed in current phase."""
    # Check absolute forbidden list
    if capability in FORBIDDEN_CAPABILITIES:
        return False

    # Check phase-specific restrictions
    phase_restricted = PHASE_RESTRICTED_CAPABILITIES.get(ACTIVE_PHASE, set())
    if capability in phase_restricted:
        return False

    # Check if explicitly allowed
    return capability in ALLOWED_CAPABILITIES


def is_capability_forbidden(capability: str) -> bool:
    """Check if a capability is forbidden."""
    return capability in FORBIDDEN_CAPABILITIES


def get_forbidden_capabilities() -> Set[str]:
    """Get all forbidden capabilities."""
    return FORBIDDEN_CAPABILITIES.copy()


def get_allowed_capabilities() -> Set[str]:
    """Get all allowed capabilities for current phase."""
    phase_restricted = PHASE_RESTRICTED_CAPABILITIES.get(ACTIVE_PHASE, set())
    return ALLOWED_CAPABILITIES - phase_restricted


def is_model_approved(model_name: str) -> bool:
    """Check if a model is approved for use."""
    return model_name in APPROVED_MODELS


def get_cost_limits() -> CostLimits:
    """Get current cost limits."""
    return COST_LIMITS


def get_rate_limits() -> RateLimits:
    """Get current rate limits."""
    return RATE_LIMITS


# =============================================================================
# POLICY VALIDATION
# =============================================================================

def validate_request(
    agent: str,
    capability: str,
    model: Optional[str] = None,
    estimated_cost: float = 0.0,
) -> Dict:
    """
    Validate a request against governance policy.

    Returns:
        Dict with 'allowed', 'reason', and 'requires_approval' keys
    """
    # Check agent autonomy
    autonomy = get_agent_autonomy(agent)
    if autonomy == AutonomyLevel.NONE:
        return {
            "allowed": False,
            "reason": f"Agent '{agent}' has no autonomy in Phase {get_phase_id()}",
            "requires_approval": False,
        }

    # Check capability
    if is_capability_forbidden(capability):
        return {
            "allowed": False,
            "reason": f"Capability '{capability}' is forbidden",
            "requires_approval": False,
        }

    if not is_capability_allowed(capability):
        return {
            "allowed": False,
            "reason": f"Capability '{capability}' not in allowed list for Phase {get_phase_id()}",
            "requires_approval": False,
        }

    # Check model
    if model and not is_model_approved(model):
        return {
            "allowed": False,
            "reason": f"Model '{model}' is not approved",
            "requires_approval": False,
        }

    # Check cost
    if estimated_cost > COST_LIMITS.max_per_request_usd:
        return {
            "allowed": False,
            "reason": f"Estimated cost ${estimated_cost:.2f} exceeds limit ${COST_LIMITS.max_per_request_usd:.2f}",
            "requires_approval": True,  # Could be approved by human
        }

    # All checks passed
    return {
        "allowed": True,
        "reason": "Request validated",
        "requires_approval": is_human_approval_required(),
    }


# =============================================================================
# CONFIG METADATA
# =============================================================================

CONFIG_VERSION = "1.0.0"
CONFIG_UPDATED = datetime.utcnow().isoformat() + "Z"
CONFIG_AUTHOR = "sovereign-system"

def get_config_metadata() -> Dict:
    """Get configuration metadata for audit."""
    return {
        "version": CONFIG_VERSION,
        "updated": CONFIG_UPDATED,
        "active_phase": get_phase_id(),
        "human_approval_required": is_human_approval_required(),
        "forbidden_capabilities_count": len(FORBIDDEN_CAPABILITIES),
        "allowed_capabilities_count": len(get_allowed_capabilities()),
        "approved_models_count": len(APPROVED_MODELS),
    }


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    print("=== Governance Config ===")
    print(f"Active Phase: {get_phase_id()}")
    print(f"Human Approval Required: {is_human_approval_required()}")
    print(f"Forbidden Capabilities: {len(FORBIDDEN_CAPABILITIES)}")
    print(f"Allowed Capabilities: {len(get_allowed_capabilities())}")
    print()

    # Test validation
    test_cases = [
        ("advocate", "read_logs", None),
        ("advocate", "model_training", None),
        ("executor", "read_logs", None),
        ("confessor", "append_ledger", "gemini-1.5-flash"),
    ]

    for agent, cap, model in test_cases:
        result = validate_request(agent, cap, model)
        status = "ALLOWED" if result["allowed"] else "DENIED"
        print(f"{agent}/{cap}: {status} - {result['reason']}")
