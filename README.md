# Sanctuary Sovereign Systems

**Governance For AI — Constitutional Kernel Framework**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Codex](https://img.shields.io/badge/Codex-v1.0-green.svg)](#the-codex)
[![Tests](https://img.shields.io/badge/Tests-72%2F72%20Passed-brightgreen.svg)](#testing)

---

## What This Is

Sanctuary Sovereign Systems is an open-source constitutional governance framework for AI and autonomous systems. It enforces governance through **structural impossibility** rather than policy compliance — illegal states cannot be represented, not merely detected.

The framework implements the principle of **Subtractive Invariance**: a system achieves stability by eliminating impossibilities, not by accumulating features.

## Architecture

The system is organized into four layers, each enforcing the one above it.

| Layer | Name | Purpose |
|-------|------|---------|
| **Layer 0** | Axioms of Sovereignty | Three non-negotiable truths the kernel exists to enforce |
| **Layer 1** | Six Invariants of Governance | Industry-agnostic governance pillars |
| **Layer 2** | Constitutional Kernel | Nine articles of mechanical enforcement (this codebase) |
| **Layer 3** | Adaptive Interface | Controlled extension points for Season 3 bolt-ons |

### The Three Axioms

**Axiom I — Evidence is Immutable.** All state transitions are recorded in an append-only, hash-chained ledger. The past cannot be altered.

**Axiom II — Ambiguity Resolves to Containment.** Any undefined or ambiguous state resolves to halt. The system never guesses.

**Axiom III — Illegality is Unrepresentable.** The system cannot represent or execute a state that violates its constitutional laws.

### The Nine Articles

| Article | Component | Impossibility Eliminated |
|---------|-----------|--------------------------|
| I | Typed Signal Ontology | Implicit or untyped routing |
| II | Hierarchical Router | Jurisdictional leakage |
| III | Legality Lane | Downstream illegal states |
| IV | Authority Separation | Mode bleed between roles |
| V | Escalation Protocol | Arbitrary escalation |
| VI | Minimal Feedback Log | Un-auditable actions |
| VII | Pathology Detection | Systemic blindness |
| VIII | Jurisdiction Context | Cross-domain contamination |
| IX | Safe Failure State | Silent fall-through failures |

## Project Structure

```
SanctuarySovereignSystems/
├── kernel/                     # Constitutional Kernel (Layer 2)
│   ├── sovereign_kernel.py     # Main orchestrator
│   ├── router/                 # Article II: Hierarchical Router
│   ├── legality/               # Article III: Legality Lane
│   ├── escalation/             # Article V: Escalation Protocol
│   ├── context/                # Article VIII: Jurisdiction Context
│   └── failure/                # Article IX: Safe Failure State
├── engine/                     # Signal Processing Engine
│   ├── signals/                # Article I: Typed Signal Ontology
│   ├── handlers/               # Signal handlers
│   ├── feedback/               # Article VI: Feedback Log
│   └── pathology/              # Article VII: Pathology Detection
├── governance/                 # Governance Layer
│   └── authority/              # Trust-to-Action Interface
├── ops/                        # Operations Layer (G.I.y)
│   ├── audit/                  # Git Intelligence Audit
│   ├── sync/                   # Sovereign Sync
│   ├── deploy/                 # Deployment tooling
│   └── integrity/              # Integrity verification
├── tests/
│   ├── compliance/             # Constitutional compliance tests
│   ├── integration/            # End-to-end pipeline tests
│   └── unit/                   # Component unit tests
└── docs/                       # Documentation
```

## Quick Start

```python
from kernel.sovereign_kernel import SovereignKernel
from engine.signals.typed_signal import SignalType, AuthorityLevel, create_signal
from governance.authority.trust_classes import TrustClass

# Initialize the constitutional kernel
kernel = SovereignKernel()

# Register a handler
kernel.register_handler(
    AuthorityLevel.OPERATOR, "state_check",
    lambda signal: print(f"Handled: {signal.signal_id}")
)

# Create a typed signal
signal = create_signal(
    signal_type=SignalType.STATE_CHECK,
    authority=AuthorityLevel.OPERATOR,
    jurisdiction="audit",
    payload={"target": "system_health"},
    source="operator_console",
)

# Process through the full constitutional pipeline
result = kernel.process(signal, TrustClass.T1_CONDITIONAL)
print(f"Accepted: {result.accepted}")
print(f"Handler: {result.handler_name}")

# Check kernel status
status = kernel.status()
print(f"State: {status.system_state}")
print(f"Chain Integrity: {status.chain_integrity}")
```

## Testing

Run the full compliance and integration suites:

```bash
# Constitutional compliance (all 9 Articles)
python3 tests/compliance/test_constitutional_compliance.py

# End-to-end integration
python3 tests/integration/test_kernel_pipeline.py
```

## Trust Classes

The Trust-to-Action Interface provides graduated autonomy:

| Class | Name | Behaviour | Required Authority |
|-------|------|-----------|-------------------|
| T0 | ADVISORY | Manual only | Operator |
| T1 | CONDITIONAL | Auto-check, manual trigger | Operator |
| T2 | PRE_APPROVED | Automatic within bounds | Innovator |
| T3 | AUTO_EXECUTABLE | Immediate autonomous response | Steward |

## Enforcement

Violations trigger one of three non-negotiable responses:

| Response | Trigger | Effect |
|----------|---------|--------|
| `process_block` | Gate bypass attempt | Operation halted |
| `transaction_hold` | Authority violation | Held in escrow |
| `kernel_panic` | Axiom violation | System-wide halt |

## Origin

This framework was condensed from the BLADE2/VENICE Git Intelligence Suite (G.I.y) and elevated to constitutional production grade under the Season 2 Sovereign Codex. The original concept of authority-grade truth alignment has been preserved and hardened into structural law.

## License

Apache License 2.0 — See [LICENSE](LICENSE) for details.

## Auth Code

`CODEX-V1-SUBTRACTIVE-INVARIANCE`
