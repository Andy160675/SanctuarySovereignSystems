import json
import os
import re
from typing import Dict, Any

from .models import AgentVerdict, Vote
from .roles import ROLE_FOCUS

try:
    from anthropic import Anthropic
except Exception as e:
    Anthropic = None
    _import_error = e
else:
    _import_error = None


class ClaudeBoardroomClient:
    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-latest"):
        if Anthropic is None:
            raise RuntimeError(f"anthropic package missing: {_import_error}")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY missing (hard fail).")
        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            m = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not m:
                raise ValueError("No JSON object found in model response.")
            return json.loads(m.group(0))

    @staticmethod
    def _normalize_vote(v: str) -> Vote:
        v = (v or "").strip().upper()
        if v not in {x.value for x in Vote}:
            return Vote.HALT
        return Vote(v)

    @staticmethod
    def _safe_float(x, lo=0.0, hi=1.0):
        try:
            v = float(x)
        except Exception:
            v = 0.0
        return max(lo, min(hi, v))

    def deliberate_role(self, role: str, decision: str, context: str, kernel_flags: list[str]) -> AgentVerdict:
        system = (
            f"You are '{role}' in a constitutional governance boardroom.\n"
            f"Focus area: {ROLE_FOCUS[role]}.\n"
            "Return STRICT JSON only with keys:\n"
            "vote, confidence, reasoning, risks, actions, constitutional_flags\n"
            "Rules:\n"
            "- vote must be APPROVE/REJECT/AMEND/ABSTAIN/HALT\n"
            "- confidence in [0,1]\n"
            "- Use HALT if uncertainty could cause material governance/safety risk\n"
            "- Keep reasoning concise and concrete."
        )

        user = (
            f"Decision:\n{decision}\n\n"
            f"Context:\n{context}\n\n"
            f"Deterministic kernel guard flags:\n{kernel_flags}\n\n"
            "Evaluate from your role only."
        )

        resp = self.client.messages.create(
            model=self.model,
            max_tokens=700,
            temperature=0.1,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        text = "".join(getattr(b, "text", "") for b in resp.content)
        data = self._extract_json(text)

        return AgentVerdict(
            role=role,
            vote=self._normalize_vote(data.get("vote", "HALT")),
            confidence=self._safe_float(data.get("confidence", 0)),
            reasoning=str(data.get("reasoning", ""))[:3000],
            risks=[str(x) for x in (data.get("risks") or [])][:20],
            actions=[str(x) for x in (data.get("actions") or [])][:20],
            constitutional_flags=[str(x) for x in (data.get("constitutional_flags") or [])][:20],
        )
