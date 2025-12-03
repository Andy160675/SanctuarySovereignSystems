# Mission Authorization Policy
# Charter-aligned access control for agents

package mission.authz

import rego.v1

default allow := false

# Allow read operations for approved agents in approved jurisdictions
allow if {
    input.action == "read"
    input.agent in approved_agents
    input.jurisdiction in approved_jurisdictions
    not blocked_path(input.path)
}

# Allow write operations only for advocate with explicit approval
allow if {
    input.action == "write"
    input.agent == "advocate"
    input.jurisdiction in approved_jurisdictions
    approved_write_path(input.path)
}

# Deny all operations if agent is in quarantine
allow := false if {
    input.agent in quarantined_agents
}

# Approved agents list
approved_agents := {"advocate", "confessor", "validator"}

# Approved jurisdictions
approved_jurisdictions := {"UK", "EU", "US"}

# Quarantined agents (emergency block)
quarantined_agents := set()

# Blocked paths - never allow access
blocked_path(path) if {
    startswith(path, "/etc/")
}
blocked_path(path) if {
    startswith(path, "/var/run/")
}
blocked_path(path) if {
    contains(path, "..")
}

# Approved write paths
approved_write_path(path) if {
    startswith(path, "/outputs/")
}
approved_write_path(path) if {
    startswith(path, "/evidence/")
}
