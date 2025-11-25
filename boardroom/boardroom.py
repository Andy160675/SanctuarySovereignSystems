# boardroom/boardroom.py

from typing import Tuple, List

from core.governance import (
    TrialAuditBundle,
    ConstitutionalViolationFlag,
    boardroom_decision,
    EventType,
    build_ledger_entry,
    append_ledger_entry,
)


class Boardroom:
    def __init__(self, ledger_path: str = "boardroom_ledger.jsonl"):
        self.ledger_path = ledger_path
        self.last_hash: str | None = None  # you can hydrate this from file at startup

    def decide(
        self,
        trial: TrialAuditBundle,
        cvfs: List[ConstitutionalViolationFlag],
    ) -> Tuple[str, List[ConstitutionalViolationFlag]]:
        decision, extra_cvfs = boardroom_decision(
            trial=trial,
            cvfs=cvfs,
            prior_history=None,   # wire in later
        )

        # Build ledger entry
        payload = {
            "trial": trial.to_dict(),
            "cvfs": [c.__dict__ for c in cvfs + extra_cvfs],
            "decision": decision,
        }

        event = EventType.TRIAL_APPROVED if decision in ("auto_approve", "vote") else EventType.TRIAL_REJECTED
        entry = build_ledger_entry(
            event_type=event,
            payload=payload,
            previous_entry_hash=self.last_hash,
            signer="BOARDROOM-13",
        )
        append_ledger_entry(entry, self.ledger_path)
        self.last_hash = entry.entry_id

        return decision, extra_cvfs
