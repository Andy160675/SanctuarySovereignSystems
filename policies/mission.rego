# Sovereign Mission - OPA Policy Gate
# Enforces AUTONOMY_LIMITS.md at runtime

package mission.authz

import rego.v1

default allow := false

# Forbidden actions - NEVER allowed autonomously
forbidden_actions := {
    "execute_payment", "transfer_funds", "approve_loan", "sign_financial_instrument",
    "sign_contract", "submit_regulatory_filing", "file_legal_document", "accept_terms",
    "make_medical_decision", "prescribe_treatment", "modify_patient_record",
    "modify_policy", "change_autonomy_level", "deploy_system", "modify_self",
    "send_external_email", "post_to_external_api", "trigger_webhook", "notify_external_party"
}

# Allowed autonomous actions - proposal mode only
allowed_actions := {
    "analyze_document", "classify_document", "extract_entities", "summarize_content",
    "classify_risk", "score_priority", "detect_anomaly", "flag_for_review",
    "generate_report", "create_summary", "compile_evidence", "format_output",
    "triage_case", "route_to_queue", "assign_priority", "estimate_complexity",
    "reconstruct_timeline", "correlate_events", "identify_patterns", "map_relationships",
    "map_regulation", "check_compliance_status", "identify_applicable_rules", "compare_to_baseline",
    "read", "list", "search"
}

# Allow if action is in allowed list and agent is valid
allow if {
    input.action in allowed_actions
    valid_agent(input.agent)
    valid_jurisdiction(input.jurisdiction)
}

# Block forbidden actions always
deny[msg] if {
    input.action in forbidden_actions
    msg := sprintf("FORBIDDEN: Action '%s' requires human seal", [input.action])
}

# Valid agents
valid_agent(agent) if {
    agent in {"advocate", "confessor", "evidence_validator", "analyst", "system"}
}

# Valid jurisdictions
valid_jurisdiction(jurisdiction) if {
    jurisdiction in {"UK", "EU", "US", "AU", "GLOBAL"}
}

# Decision output
decision := {
    "allow": allow,
    "deny_reasons": deny,
    "agent": input.agent,
    "action": input.action,
    "timestamp": time.now_ns()
}
