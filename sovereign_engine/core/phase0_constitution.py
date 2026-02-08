"""
PHASE 0 — Constitutional Ground Truth
CSS-ENG-MOD-000 | Sovereign Recursion Engine

Loads the constitution, validates internal consistency,
provides the invariant test harness that all modules must pass
before activation.

Principle: Nothing executes until the constitution is online.
"""

import json
import copy
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class ConstitutionalError(Exception):
    """Raised when a constitutional invariant is violated."""
    pass


class BootError(ConstitutionalError):
    """Raised when the engine cannot boot."""
    pass


@dataclass
class InvariantResult:
    name: str
    passed: bool
    reason: Optional[str] = None

    def __repr__(self):
        status = "PASS" if self.passed else f"FAIL: {self.reason}"
        return f"  [{status}] {self.name}"


@dataclass
class ValidationReport:
    passed: int = 0
    failed: int = 0
    results: list = field(default_factory=list)

    @property
    def total(self):
        return self.passed + self.failed

    @property
    def all_passed(self):
        return self.failed == 0

    def __repr__(self):
        lines = [f"Invariant Tests: {self.passed}/{self.total} passed"]
        for r in self.results:
            lines.append(str(r))
        return "\n".join(lines)


class Constitution:
    """
    Machine-readable constitutional ground truth.
    
    Immutable after validation. All reads return frozen copies.
    """

    REQUIRED_SECTIONS = frozenset([
        "meta", "authority_ladder", "signal_schema", "routing_grammar",
        "legality_constraints", "failure_semantics", "timing_contracts",
        "audit_requirements", "archetypes"
    ])

    VALID_FAILURE_ACTIONS = frozenset(["halt", "escalate", "escalate_and_contain"])

    def __init__(self, config_path: Optional[str] = None):
        self._raw: Optional[dict] = None
        self._validated: bool = False
        self._config_path = config_path or str(
            Path(__file__).parent.parent / "configs" / "constitution.json"
        )
        self._invariant_tests: list[tuple[str, Callable]] = []
        self._violations: list[str] = []

    # ──────────────────────────────────────────────
    # LOAD
    # ──────────────────────────────────────────────

    def load(self) -> "Constitution":
        """Load constitution from disk. Hard fail on missing or malformed."""
        try:
            with open(self._config_path, "r") as f:
                self._raw = json.load(f)
        except FileNotFoundError:
            raise BootError(f"BOOT FAILURE: Constitution not found at {self._config_path}")
        except json.JSONDecodeError as e:
            raise BootError(f"BOOT FAILURE: Constitution is malformed JSON: {e}")
        return self

    def load_from_dict(self, data: dict) -> "Constitution":
        """Load constitution from a dict (for testing)."""
        self._raw = copy.deepcopy(data)
        return self

    # ──────────────────────────────────────────────
    # VALIDATE
    # ──────────────────────────────────────────────

    def validate(self) -> "Constitution":
        """
        Validate internal consistency. Every cross-reference must resolve.
        Raises ConstitutionalError on failure.
        """
        if self._raw is None:
            raise BootError("Constitution not loaded")

        self._violations = []

        self._check_required_sections()
        self._check_authority_ladder()
        self._check_signal_schema()
        self._check_routing_grammar()
        self._check_halt_doctrine()
        self._check_failure_semantics()
        self._check_timing_contracts()
        self._check_audit_requirements()
        self._check_archetypes()

        if self._violations:
            msg = "CONSTITUTION INVALID:\n" + "\n".join(f"  - {v}" for v in self._violations)
            raise ConstitutionalError(msg)

        self._validated = True
        return self

    def _check_required_sections(self):
        for section in self.REQUIRED_SECTIONS:
            if section not in self._raw:
                self._violations.append(f"Missing required section: {section}")

    def _check_authority_ladder(self):
        ladder = self._raw.get("authority_ladder", {})
        levels = ladder.get("levels", [])
        if not levels:
            self._violations.append("Authority ladder has no levels")
            return

        rules = ladder.get("escalation_rules", {})
        for condition, target in rules.items():
            if target not in levels:
                self._violations.append(
                    f"Escalation target '{target}' (condition: {condition}) not in authority levels"
                )

        # Invariants must be present
        invariants = ladder.get("invariants", [])
        if not invariants:
            self._violations.append("Authority ladder has no invariants defined")

    def _check_signal_schema(self):
        schema = self._raw.get("signal_schema", {})
        if not schema.get("required_fields"):
            self._violations.append("Signal schema has no required fields")
        if not schema.get("valid_types"):
            self._violations.append("Signal schema has no valid types")
        if not schema.get("valid_domains"):
            self._violations.append("Signal schema has no valid domains")
        if not schema.get("valid_authorities"):
            self._violations.append("Signal schema has no valid authorities")

    def _check_routing_grammar(self):
        grammar = self._raw.get("routing_grammar", {})
        rules = grammar.get("rules", [])
        levels = self._raw.get("authority_ladder", {}).get("levels", [])
        valid_targets = set(levels) | {"system"}

        for rule in rules:
            if "target" not in rule or "condition" not in rule:
                self._violations.append(f"Routing rule missing target or condition: {rule}")
            elif rule["target"] not in valid_targets:
                self._violations.append(
                    f"Routing rule targets unknown authority: {rule['target']}"
                )

    def _check_halt_doctrine(self):
        grammar = self._raw.get("routing_grammar", {})
        if grammar.get("default_on_ambiguity") != "halt":
            self._violations.append(
                "HALT DOCTRINE VIOLATED: default_on_ambiguity must be 'halt'"
            )

    def _check_failure_semantics(self):
        semantics = self._raw.get("failure_semantics", {})
        for key, sem in semantics.items():
            action = sem.get("action")
            if action not in self.VALID_FAILURE_ACTIONS:
                self._violations.append(
                    f"Failure semantic '{key}' has unknown action: {action}"
                )
            if "recovery" not in sem:
                self._violations.append(
                    f"Failure semantic '{key}' has no recovery path defined"
                )

    def _check_timing_contracts(self):
        contracts = self._raw.get("timing_contracts", {})
        for key, val in contracts.items():
            if not isinstance(val, (int, float)) or val <= 0:
                self._violations.append(
                    f"Timing contract '{key}' must be positive number, got: {val}"
                )

    def _check_audit_requirements(self):
        audit = self._raw.get("audit_requirements", {})
        if audit.get("format") != "append_only":
            self._violations.append("Audit format must be 'append_only'")
        integrity = audit.get("integrity", "")
        if "sha256" not in integrity:
            self._violations.append("Audit integrity must use sha256")
        if not audit.get("minimum_record"):
            self._violations.append("Audit minimum_record not defined")

    def _check_archetypes(self):
        archetypes = self._raw.get("archetypes", {})
        if not archetypes:
            self._violations.append("No archetypes defined")
        for name, arch in archetypes.items():
            if "steward_mode" not in arch:
                self._violations.append(f"Archetype '{name}' missing steward_mode")
            if "routing_tables" not in arch:
                self._violations.append(f"Archetype '{name}' missing routing_tables")

    # ──────────────────────────────────────────────
    # ACCESSORS (all return frozen copies)
    # ──────────────────────────────────────────────

    def get(self, section: str) -> Any:
        self._ensure_valid()
        if section not in self._raw:
            raise ConstitutionalError(f"No such constitutional section: {section}")
        return copy.deepcopy(self._raw[section])

    def is_forbidden(self, state_name: str) -> bool:
        self._ensure_valid()
        return state_name in self._raw["legality_constraints"]["forbidden_states"]

    def get_failure_response(self, failure_type: str) -> dict:
        self._ensure_valid()
        response = self._raw["failure_semantics"].get(failure_type)
        if not response:
            return {"action": "halt", "recovery": "unknown_failure_constitutional_review"}
        return copy.deepcopy(response)

    def get_timing(self, key: str) -> int:
        self._ensure_valid()
        val = self._raw["timing_contracts"].get(key)
        if val is None:
            raise ConstitutionalError(f"No timing contract for: {key}")
        return val

    def get_archetype(self, name: str) -> dict:
        self._ensure_valid()
        arch = self._raw["archetypes"].get(name)
        if not arch:
            raise ConstitutionalError(f"Unknown archetype: {name}")
        return copy.deepcopy(arch)

    @property
    def authority_levels(self) -> list[str]:
        self._ensure_valid()
        return list(self._raw["authority_ladder"]["levels"])

    @property
    def forbidden_states(self) -> list[str]:
        self._ensure_valid()
        return list(self._raw["legality_constraints"]["forbidden_states"])

    @property
    def valid_signal_types(self) -> list[str]:
        self._ensure_valid()
        return list(self._raw["signal_schema"]["valid_types"])

    @property
    def valid_signal_domains(self) -> list[str]:
        self._ensure_valid()
        return list(self._raw["signal_schema"]["valid_domains"])

    @property
    def valid_signal_authorities(self) -> list[str]:
        self._ensure_valid()
        return list(self._raw["signal_schema"]["valid_authorities"])

    # ──────────────────────────────────────────────
    # INVARIANT TEST HARNESS
    # ──────────────────────────────────────────────

    def register_invariant_test(self, name: str, test_fn: Callable):
        """Register an invariant test. Runs before engine start."""
        self._invariant_tests.append((name, test_fn))

    def run_invariant_tests(self) -> ValidationReport:
        """Run all registered invariant tests."""
        self._ensure_valid()
        report = ValidationReport()

        for name, test_fn in self._invariant_tests:
            try:
                result = test_fn(self)
                if result is True:
                    report.results.append(InvariantResult(name, True))
                    report.passed += 1
                else:
                    reason = result if isinstance(result, str) else "returned non-True"
                    report.results.append(InvariantResult(name, False, reason))
                    report.failed += 1
            except Exception as e:
                report.results.append(InvariantResult(name, False, str(e)))
                report.failed += 1

        return report

    def _ensure_valid(self):
        if self._raw is None:
            raise BootError("Constitution not loaded")
        if not self._validated:
            raise BootError("Constitution not validated")


# ═══════════════════════════════════════════════════════════
# BUILT-IN INVARIANT TESTS
# ═══════════════════════════════════════════════════════════

def register_builtin_tests(constitution: Constitution):
    """Register the non-negotiable invariant tests."""

    constitution.register_invariant_test(
        "halt_doctrine_enforced",
        lambda c: c.get("routing_grammar")["default_on_ambiguity"] == "halt"
    )

    constitution.register_invariant_test(
        "authority_ladder_has_three_levels",
        lambda c: len(c.get("authority_ladder")["levels"]) == 3
    )

    constitution.register_invariant_test(
        "authority_order_is_operator_innovator_steward",
        lambda c: c.get("authority_ladder")["levels"] == ["operator", "innovator", "steward"]
    )

    constitution.register_invariant_test(
        "audit_is_append_only",
        lambda c: c.get("audit_requirements")["format"] == "append_only"
    )

    constitution.register_invariant_test(
        "audit_uses_sha256",
        lambda c: "sha256" in c.get("audit_requirements")["integrity"]
    )

    constitution.register_invariant_test(
        "all_forbidden_states_are_strings",
        lambda c: all(isinstance(s, str) for s in c.forbidden_states)
    )

    constitution.register_invariant_test(
        "every_escalation_targets_valid_authority",
        lambda c: all(
            t in c.authority_levels
            for t in c.get("authority_ladder")["escalation_rules"].values()
        )
    )

    constitution.register_invariant_test(
        "every_routing_rule_has_target_and_condition",
        lambda c: all(
            "target" in r and "condition" in r
            for r in c.get("routing_grammar")["rules"]
        )
    )

    constitution.register_invariant_test(
        "all_timing_contracts_positive",
        lambda c: all(v > 0 for v in c.get("timing_contracts").values())
    )

    constitution.register_invariant_test(
        "router_failure_halts",
        lambda c: c.get_failure_response("router_failure")["action"] == "halt"
    )

    constitution.register_invariant_test(
        "audit_failure_halts",
        lambda c: c.get_failure_response("audit_failure")["action"] == "halt"
    )

    constitution.register_invariant_test(
        "authority_breach_halts",
        lambda c: c.get_failure_response("authority_breach")["action"] == "halt"
    )

    constitution.register_invariant_test(
        "unknown_failure_defaults_to_halt",
        lambda c: c.get_failure_response("nonexistent_xyz")["action"] == "halt"
    )

    constitution.register_invariant_test(
        "at_least_one_archetype_defined",
        lambda c: len(c.get("archetypes")) >= 1
    )

    constitution.register_invariant_test(
        "all_archetypes_have_steward_mode",
        lambda c: all("steward_mode" in a for a in c.get("archetypes").values())
    )

    constitution.register_invariant_test(
        "fallback_on_failure_is_contain",
        lambda c: c.get("routing_grammar")["fallback_on_failure"] == "contain_and_log"
    )
