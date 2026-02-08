"""
PHASE 8 — Integration Engine
CSS-ENG-MOD-008 | Sovereign Recursion Engine

Wires Phase 0-7 into a single governed pipeline.
Boot sequence: constitution → validate → harness → audit boot → handlers → ready.
Process sequence: signal → legality → route → audit → done.

Dependency: All prior phases
Invariant: Boot fails → engine never starts.
Invariant: Every processed signal has an audit entry.
"""

from typing import Any, Callable, Optional
from .phase0_constitution import Constitution, ConstitutionalError, register_builtin_tests
from .phase1_signals import SignalFactory, SignalBus, Signal
from .phase2_router import Router, AuthorityHandler
from .phase3_legality import LegalityGate
from .phase4_audit import AuditLedger
from .phase5_timing import TimingEnforcer, Watchdog, HaltController
from .phase6_failure import FailureMatrix, HealthMonitor
from .phase7_configurator import ConstitutionalConfigurator


class EngineError(Exception):
    pass


class SovereignEngine:
    """
    The full Sovereign Recursion Engine.
    
    Boot sequence enforces constitutional ground truth.
    Process pipeline enforces legality → routing → audit chain.
    No shortcuts. No bypasses. Prefer stopping to lying.
    """

    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path
        self._booted = False

        # Components (initialised during boot)
        self.constitution: Optional[Constitution] = None
        self.factory: Optional[SignalFactory] = None
        self.bus: Optional[SignalBus] = None
        self.router: Optional[Router] = None
        self.gate: Optional[LegalityGate] = None
        self.ledger: Optional[AuditLedger] = None
        self.timing: Optional[TimingEnforcer] = None
        self.watchdog: Optional[Watchdog] = None
        self.halt_ctrl: Optional[HaltController] = None
        self.failure_matrix: Optional[FailureMatrix] = None
        self.health: Optional[HealthMonitor] = None
        self.configurator: Optional[ConstitutionalConfigurator] = None

        # Stats
        self._signals_processed = 0
        self._signals_terminated = 0
        self._signals_routed = 0

    # ──────────────────────────────────────────────
    # BOOT SEQUENCE
    # ──────────────────────────────────────────────

    def boot(self, handlers: Optional[dict[str, Callable]] = None) -> dict:
        """
        Full boot sequence. Fails hard on any constitutional violation.
        
        1. Load constitution
        2. Validate constitution
        3. Run invariant tests
        4. Initialise all subsystems
        5. Boot-validate audit ledger
        6. Register authority handlers
        7. Ready
        
        Returns boot report.
        """
        report = {"phase": [], "status": "booting"}

        try:
            # Phase 0: Constitution
            self.constitution = Constitution(self._config_path)
            self.constitution.load()
            report["phase"].append({"name": "constitution_load", "status": "ok"})

            self.constitution.validate()
            report["phase"].append({"name": "constitution_validate", "status": "ok"})

            register_builtin_tests(self.constitution)
            invariants = self.constitution.run_invariant_tests()
            if not invariants.all_passed:
                raise EngineError(
                    f"Invariant tests failed: {invariants.failed}/{invariants.total}\n{invariants}"
                )
            report["phase"].append({
                "name": "invariant_tests",
                "status": "ok",
                "passed": invariants.passed,
                "total": invariants.total,
            })

            # Phase 1: Signals
            self.factory = SignalFactory(self.constitution)
            self.bus = SignalBus(self.factory, self.constitution)
            report["phase"].append({"name": "signal_substrate", "status": "ok"})

            # Phase 2: Router
            self.router = Router(self.constitution)
            report["phase"].append({"name": "router_kernel", "status": "ok"})

            # Phase 3: Legality
            self.gate = LegalityGate(self.constitution, self.factory)
            report["phase"].append({"name": "legality_gate", "status": "ok"})

            # Phase 4: Audit
            self.ledger = AuditLedger(self.constitution)
            boot_v = self.ledger.boot_validation()
            report["phase"].append({
                "name": "audit_ledger",
                "status": "ok",
                "boot_valid": boot_v["boot_valid"],
            })

            # Phase 5: Timing & Halt
            self.timing = TimingEnforcer(self.constitution)
            self.watchdog = Watchdog(self.constitution)
            self.halt_ctrl = HaltController()
            report["phase"].append({"name": "timing_halt", "status": "ok"})

            # Phase 6: Failure
            self.failure_matrix = FailureMatrix(self.constitution, self.halt_ctrl)
            self.health = HealthMonitor(self.failure_matrix)
            for comp in ["router", "legality", "audit", "bus"]:
                self.health.register(comp)
                self.watchdog.register(comp)
            report["phase"].append({"name": "failure_matrix", "status": "ok"})

            # Phase 7: Configurator
            self.configurator = ConstitutionalConfigurator(self.constitution)
            report["phase"].append({"name": "configurator", "status": "ok"})

            # Register handlers
            self._register_handlers(handlers or {})
            report["phase"].append({"name": "handlers_registered", "status": "ok"})

            # Write boot event to ledger
            self.ledger.write({
                "signal_type": "system",
                "route": "boot",
                "handler": "engine",
                "outcome": "boot_complete",
                "signal_id": "boot",
                "signal_domain": "constitutional",
            })

            self._booted = True
            report["status"] = "ready"
            return report

        except Exception as e:
            report["status"] = "failed"
            report["error"] = str(e)
            raise EngineError(f"Boot failed: {e}") from e

    def _register_handlers(self, handler_fns: dict[str, Callable]):
        """Register authority handlers. Uses defaults if not provided."""
        levels = self.constitution.authority_levels

        # Domain jurisdiction mapping
        jurisdictions = {
            "operator": {"operational"},
            "innovator": {"governance", "operational"},
            "steward": {"constitutional", "emergency", "governance", "operational"},
        }

        for level in levels:
            handler = AuthorityHandler(level, jurisdictions.get(level, set()))

            if level in handler_fns:
                handler.set_handler(handler_fns[level])
            else:
                # Default handler: acknowledge and pass
                handler.set_handler(lambda sig, _lvl=level: {
                    "outcome": "processed",
                    "data": {"handler": _lvl, "signal_type": sig.type},
                })

            self.router.register_handler(level, handler)

    # ──────────────────────────────────────────────
    # PROCESS PIPELINE
    # ──────────────────────────────────────────────

    def process(self, signal: Signal, context: Optional[dict] = None) -> dict:
        """
        Full signal processing pipeline:
        1. Legality check
        2. Route to handler
        3. Audit the result
        
        INVARIANT: Every signal has an audit entry.
        INVARIANT: Illegal signals never reach routing.
        """
        if not self._booted:
            raise EngineError("Engine not booted")

        if self.halt_ctrl.is_halted:
            if signal.type != "halt":
                return {"processed": False, "reason": "Engine halted"}

        self._signals_processed += 1
        ctx = context or {}

        # Step 1: Legality gate
        legality = self.gate.check(signal, ctx)
        if not legality.legal:
            self._signals_terminated += 1
            self.ledger.write_containment(legality.containment)
            self.health.report_healthy("legality")
            return {
                "processed": False,
                "stage": "legality",
                "violations": [{"rule": v.rule, "reason": v.reason}
                               for v in legality.violations],
            }

        # Step 2: Route
        decision = self.router.route(signal)
        self.health.report_healthy("router")

        # Step 3: Audit
        self.ledger.write_routing_decision(signal, decision)
        self.health.report_healthy("audit")

        # Handle halt decisions
        if decision.action in ("halt", "system_halt"):
            self.halt_ctrl.halt(
                reason=decision.reason or "routing halt",
                source="router",
            )

        self._signals_routed += 1

        return {
            "processed": True,
            "action": decision.action,
            "target": decision.target,
            "reason": decision.reason,
            "handler_result": decision.handler_result,
        }

    # ──────────────────────────────────────────────
    # CONVENIENCE
    # ──────────────────────────────────────────────

    def create_signal(self, type: str, domain: str, authority: str,
                      payload: Any, **kwargs) -> Signal:
        """Create a validated signal via the factory."""
        return self.factory.create(
            type=type, domain=domain, authority=authority,
            payload=payload, **kwargs,
        )

    def submit_and_process(self, type: str, domain: str, authority: str,
                           payload: Any, context: Optional[dict] = None,
                           **kwargs) -> dict:
        """Create, submit to bus, and process in one call."""
        signal = self.create_signal(type, domain, authority, payload, **kwargs)
        return self.process(signal, context)

    @property
    def is_booted(self) -> bool:
        return self._booted

    @property
    def is_halted(self) -> bool:
        return self.halt_ctrl.is_halted if self.halt_ctrl else False

    @property
    def engine_stats(self) -> dict:
        return {
            "signals_processed": self._signals_processed,
            "signals_terminated": self._signals_terminated,
            "signals_routed": self._signals_routed,
            "ledger_entries": self.ledger.length if self.ledger else 0,
            "halted": self.is_halted,
        }
