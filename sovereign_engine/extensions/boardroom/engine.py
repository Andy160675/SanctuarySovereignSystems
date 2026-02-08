from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from typing import List

from .roles import ROLES, VETO_ROLES
from .models import Vote, AgentVerdict, FinalVerdict, DecisionBundle
from .kernel_guard import scan_decision_for_kernel_risk
from .claude_client import ClaudeBoardroomClient


class BoardroomEngine:
    SCORE = {
        Vote.APPROVE: 1.0,
        Vote.AMEND: 0.25,
        Vote.ABSTAIN: 0.0,
        Vote.REJECT: -1.0,
        Vote.HALT: -1.5,
    }

    def __init__(self, client: ClaudeBoardroomClient, max_workers: int = 13):
        self.client = client
        self.max_workers = max_workers

    def _aggregate(self, agents: List[AgentVerdict], kernel_flags: List[str]) -> FinalVerdict:
        vetoes = []
        for a in agents:
            if a.role in VETO_ROLES and a.vote in {Vote.HALT, Vote.REJECT} and a.confidence >= 0.70:
                vetoes.append(f"{a.role}:{a.vote.value}:{a.confidence:.2f}")

        if kernel_flags:
            return FinalVerdict(
                final=Vote.HALT,
                reason="Deterministic kernel guard triggered.",
                score=-1.0,
                distribution=dict(Counter([a.vote.value for a in agents])),
                vetoes=vetoes,
            )

        if vetoes:
            return FinalVerdict(
                final=Vote.HALT,
                reason="Veto role blocked decision.",
                score=-1.0,
                distribution=dict(Counter([a.vote.value for a in agents])),
                vetoes=vetoes,
            )

        weighted = []
        for a in agents:
            weighted.append(self.SCORE[a.vote] * a.confidence)
        score = sum(weighted) / max(1, len(weighted))

        if score >= 0.45:
            final = Vote.APPROVE
            reason = "Weighted approval exceeded threshold."
        elif score >= 0.10:
            final = Vote.AMEND
            reason = "Amendment required before approval."
        elif score <= -0.35:
            final = Vote.REJECT
            reason = "Weighted rejection exceeded threshold."
        else:
            final = Vote.ABSTAIN
            reason = "Insufficient consensus."

        return FinalVerdict(
            final=final,
            reason=reason,
            score=round(score, 4),
            distribution=dict(Counter([a.vote.value for a in agents])),
            vetoes=vetoes,
        )

    def deliberate(self, decision: str, context: str = "") -> DecisionBundle:
        kernel_flags = scan_decision_for_kernel_risk(decision)
        agents: List[AgentVerdict] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {
                ex.submit(self.client.deliberate_role, role, decision, context, kernel_flags): role
                for role in ROLES
            }
            for fut in as_completed(futures):
                agents.append(fut.result())

        agents = sorted(agents, key=lambda a: ROLES.index(a.role))
        final = self._aggregate(agents, kernel_flags)

        return DecisionBundle(
            decision=decision,
            context=context,
            model=self.client.model,
            final=final,
            agents=agents,
        )
