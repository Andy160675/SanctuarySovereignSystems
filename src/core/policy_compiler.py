"""
Sovereign Policy Compiler v1.0
Converts YAML/JSON policies into executable Python validation functions.
"""

import json
from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from .evidence.api import get_global_evidence_chain

@dataclass
class PolicyResult:
    passed: bool
    violations: List[str]
    metadata: Dict[str, Any]

class PolicyCompiler:
    """Compiles and executes governance policies."""
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.policies: Dict[str, Callable[[Dict[str, Any]], PolicyResult]] = {}
        self.evidence = get_global_evidence_chain()

    def load_policy(self, name: str, schema: Dict[str, Any]):
        """
        Compiles a policy schema into a validation function.
        Example schema:
        {
            "rules": [
                {"field": "amount", "operator": "lt", "value": 1000},
                {"field": "authority", "operator": "in", "value": ["steward"]}
            ]
        }
        """
        def validate(context: Dict[str, Any]) -> PolicyResult:
            violations = []
            for rule in schema.get("rules", []):
                field = rule.get("field")
                operator = rule.get("operator")
                expected = rule.get("value")
                actual = context.get(field)
                
                if operator == "lt" and not (actual < expected):
                    violations.append(f"{field} ({actual}) must be less than {expected}")
                elif operator == "gt" and not (actual > expected):
                    violations.append(f"{field} ({actual}) must be greater than {expected}")
                elif operator == "eq" and actual != expected:
                    violations.append(f"{field} ({actual}) must equal {expected}")
                elif operator == "in" and actual not in expected:
                    violations.append(f"{field} ({actual}) must be one of {expected}")
            
            return PolicyResult(
                passed=len(violations) == 0,
                violations=violations,
                metadata={"policy_name": name, "schema_version": self.version}
            )
        
        self.policies[name] = validate
        
        # Log policy loading to evidence chain
        self.evidence.append(
            "policy_loaded",
            {"name": name, "schema": schema},
            f"policy-compiler/{self.version}"
        )

    def validate(self, name: str, context: Dict[str, Any]) -> PolicyResult:
        """Validate a context against a loaded policy."""
        if name not in self.policies:
            return PolicyResult(False, [f"Policy '{name}' not found"], {})
        
        result = self.policies[name](context)
        
        # Log validation event
        self.evidence.append(
            "policy_execution",
            {
                "policy_name": name,
                "context": context,
                "passed": result.passed,
                "violations": result.violations
            },
            f"policy-compiler/{self.version}"
        )
        
        return result
