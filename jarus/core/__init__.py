"""
JARUS Core Module
=================
Constitutional governance engine for sovereign AI operations.

Components:
- ConstitutionalRuntime: Evaluates actions against constitution
- EvidenceLedger: Cryptographic audit trail

Usage:
    from jarus.core import ConstitutionalRuntime, EvidenceLedger
    
    runtime = ConstitutionalRuntime()
    ledger = EvidenceLedger()
    
    decision = runtime.evaluate({'action': 'read_file'})
    if decision.decision_type == DecisionType.PERMIT:
        # Proceed
        ledger.record_decision(decision.to_dict())
"""

from .constitutional_runtime import (
    ConstitutionalRuntime,
    ConstitutionalClause,
    Decision,
    DecisionType,
    Severity,
    Violation
)

from .evidence_ledger import (
    EvidenceLedger,
    EvidenceEntry,
    EvidenceReceipt,
    EvidenceType,
    ChainStatus,
    VerificationResult
)

__version__ = "1.0.0"
__author__ = "Codex Sovereign Systems"

__all__ = [
    # Constitutional Runtime
    'ConstitutionalRuntime',
    'ConstitutionalClause', 
    'Decision',
    'DecisionType',
    'Severity',
    'Violation',
    # Evidence Ledger
    'EvidenceLedger',
    'EvidenceEntry',
    'EvidenceReceipt',
    'EvidenceType',
    'ChainStatus',
    'VerificationResult',
]
