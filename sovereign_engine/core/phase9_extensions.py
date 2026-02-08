"""
PHASE 9 — Extension Scaffold (Season-3 Boundary)
CSS-ENG-MOD-009 | Sovereign Recursion Engine

Defines the interface for Season-3 bolt-ons.
All extensions must pass invariant compliance before activation.
Extensions can observe and suggest — never override kernel invariants.

Dependency: All prior phases
Invariant: No extension can modify Season-2 invariants.
Invariant: All plugins pass compliance tests before activation.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from .phase0_constitution import Constitution, ConstitutionalError


class ExtensionError(Exception):
    pass


@dataclass
class ExtensionManifest:
    """Declares what an extension needs and provides."""
    name: str
    version: str
    author: str
    description: str
    requires_authority: str           # which authority level it operates under
    reads_from: list[str] = field(default_factory=list)   # what it observes
    writes_to: list[str] = field(default_factory=list)    # what it can suggest changes to
    modifies_routing: bool = False    # does it suggest routing changes?
    modifies_legality: bool = False   # does it add legality rules?


@dataclass
class ComplianceResult:
    extension: str
    compliant: bool
    violations: list[str] = field(default_factory=list)


class ExtensionRegistry:
    """
    Registry and compliance gate for Season-3 extensions.
    
    Extensions register with a manifest.
    Compliance check validates against kernel invariants.
    Only compliant extensions are activated.
    """

    def __init__(self, constitution: Constitution):
        self._constitution = constitution
        self._registered: dict[str, dict] = {}
        self._activated: set[str] = set()

    def register(self, manifest: ExtensionManifest, handler: Callable) -> ComplianceResult:
        """
        Register an extension. Checks compliance before allowing activation.
        """
        violations = []

        # Check authority level is valid
        valid_authorities = self._constitution.valid_signal_authorities
        if manifest.requires_authority not in valid_authorities:
            violations.append(
                f"Unknown authority level: {manifest.requires_authority}"
            )

        # Extensions cannot claim steward-level modification rights
        # unless explicitly authorised by the constitution
        if manifest.requires_authority == "steward" and manifest.modifies_routing:
            # Only the configurator can modify routing at steward level
            violations.append(
                "Extensions cannot modify routing at steward level — "
                "use ConstitutionalConfigurator instead"
            )

        # Extensions cannot modify the halt doctrine
        if "default_on_ambiguity" in manifest.writes_to:
            violations.append("Cannot modify halt doctrine")

        # Extensions cannot modify the authority ladder
        if "authority_ladder" in manifest.writes_to:
            violations.append("Cannot modify authority ladder")

        # Extensions cannot modify audit integrity requirements
        if "audit_requirements" in manifest.writes_to:
            violations.append("Cannot modify audit requirements")

        result = ComplianceResult(
            extension=manifest.name,
            compliant=len(violations) == 0,
            violations=violations,
        )

        # Store regardless, but only compliant extensions can be activated
        self._registered[manifest.name] = {
            "manifest": manifest,
            "handler": handler,
            "compliance": result,
        }

        return result

    def activate(self, name: str) -> bool:
        """Activate a registered extension. Must be compliant."""
        if name not in self._registered:
            raise ExtensionError(f"Extension not registered: {name}")

        entry = self._registered[name]
        if not entry["compliance"].compliant:
            raise ExtensionError(
                f"Extension '{name}' is not compliant: "
                f"{entry['compliance'].violations}"
            )

        self._activated.add(name)
        return True

    def is_activated(self, name: str) -> bool:
        return name in self._activated

    @property
    def registered_extensions(self) -> list[str]:
        return list(self._registered.keys())

    @property
    def activated_extensions(self) -> list[str]:
        return list(self._activated)

    def get_compliance(self, name: str) -> Optional[ComplianceResult]:
        if name not in self._registered:
            return None
        return self._registered[name]["compliance"]
