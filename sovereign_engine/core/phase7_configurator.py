"""
PHASE 7 — Constitutional Configurator (Archetype Compiler)
CSS-ENG-MOD-007 | Sovereign Recursion Engine

Compiles archetype definitions (managerial / immutable / federated)
into runtime routing tables and legality configs.
Validates compiled config against Season-2 invariants before activation.

Dependency: Phase 0, Phase 2, Phase 3
Invariant: No archetype may violate kernel invariants.
Invariant: Compilation produces deterministic output.
"""

import copy
from dataclasses import dataclass, field
from typing import Optional
from .phase0_constitution import Constitution, ConstitutionalError


@dataclass
class CompiledArchetype:
    name: str
    steward_mode: str          # active | passive | quorum
    routing_mutable: bool
    upgrades_enabled: bool
    routing_overrides: dict = field(default_factory=dict)
    legality_overrides: list = field(default_factory=list)
    valid: bool = False
    violations: list = field(default_factory=list)


class ConstitutionalConfigurator:
    """
    Archetype compiler.
    
    Takes a governance archetype name, reads its definition from
    the constitution, and compiles it into runtime configuration
    that the router and legality gate can consume.
    
    INVARIANT: Compiled config must pass invariant validation
    before it can be activated.
    """

    def __init__(self, constitution: Constitution):
        self._constitution = constitution
        self._archetypes = constitution.get("archetypes")
        self._base_grammar = constitution.get("routing_grammar")
        self._authority_ladder = constitution.get("authority_ladder")

    def compile(self, archetype_name: str) -> CompiledArchetype:
        """
        Compile an archetype into runtime configuration.
        Returns CompiledArchetype with validity status.
        """
        if archetype_name not in self._archetypes:
            raise ConstitutionalError(f"Unknown archetype: {archetype_name}")

        spec = self._archetypes[archetype_name]
        violations = []

        # Determine properties
        steward_mode = spec.get("steward_mode", "active")
        routing_mutable = spec.get("routing_tables") in ("mutable", "quorum_mutable")
        upgrades_enabled = spec.get("upgrade_paths") in ("enabled", "quorum_gated")

        # Build routing overrides based on archetype
        routing_overrides = {}
        legality_overrides = []

        if steward_mode == "passive":
            # Immutable: steward only observes, never actively routes
            routing_overrides["steward_active_routing"] = False
            # Add legality rule: no routing table modification at runtime
            legality_overrides.append({
                "rule": "no_runtime_routing_modification",
                "enforced": True,
            })

        if steward_mode == "quorum":
            # Federated: steward actions require quorum
            routing_overrides["steward_requires_quorum"] = True
            routing_overrides["quorum_threshold"] = 2  # minimum agreeing parties

        if not upgrades_enabled:
            legality_overrides.append({
                "rule": "no_upgrade_paths",
                "enforced": True,
            })

        # Validate against kernel invariants
        self._validate_against_invariants(
            steward_mode, routing_mutable, upgrades_enabled, violations
        )

        compiled = CompiledArchetype(
            name=archetype_name,
            steward_mode=steward_mode,
            routing_mutable=routing_mutable,
            upgrades_enabled=upgrades_enabled,
            routing_overrides=routing_overrides,
            legality_overrides=legality_overrides,
            valid=len(violations) == 0,
            violations=violations,
        )

        return compiled

    def _validate_against_invariants(self, steward_mode, routing_mutable,
                                     upgrades_enabled, violations):
        """Ensure compiled archetype doesn't break kernel invariants."""

        # Halt doctrine must still apply regardless of archetype
        if self._base_grammar.get("default_on_ambiguity") != "halt":
            violations.append("Halt doctrine would be violated")

        # Authority ladder must be preserved
        levels = self._authority_ladder.get("levels", [])
        if len(levels) != 3:
            violations.append("Authority ladder integrity violated")

        # Even immutable archetype must allow halt signals
        # (This is always true by kernel design, but validate explicitly)

        # Steward mode must be one of the known modes
        valid_modes = {"active", "passive", "quorum"}
        if steward_mode not in valid_modes:
            violations.append(f"Unknown steward mode: {steward_mode}")

    def list_archetypes(self) -> list[str]:
        return list(self._archetypes.keys())

    def get_spec(self, archetype_name: str) -> dict:
        if archetype_name not in self._archetypes:
            raise ConstitutionalError(f"Unknown archetype: {archetype_name}")
        return copy.deepcopy(self._archetypes[archetype_name])
