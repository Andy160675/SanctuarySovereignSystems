import os
from dataclasses import dataclass

@dataclass(frozen=True)
class GovernanceConfig:
    GLOBAL_MAX_DAILY_COST: float = float(os.getenv("GLOBAL_MAX_DAILY_COST", "50.0"))
    MAX_UNCERTAINTY: float = float(os.getenv("MAX_UNCERTAINTY", "0.4"))
    DATA_DIR: str = os.getenv("DATA_DIR", ".")

    # Global default (fallback)
    DEFAULT_TRACK: str = os.getenv("TRACK", "insider").lower()

    @classmethod
    def load(cls) -> "GovernanceConfig":
        return cls()

    def get_agent_track(self, agent_name: str) -> str:
        """
        Resolve track for an agent.
        Priority:
          1. {AGENT_NAME}_TRACK (e.g. EVIDENCE_TRACK)
          2. TRACK
          3. 'insider'
        """
        env_var = f"{agent_name.upper()}_TRACK"
        return os.getenv(env_var, self.DEFAULT_TRACK).lower()

CONFIG = GovernanceConfig.load()