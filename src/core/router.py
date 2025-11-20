import os
import json
import time
from pathlib import Path
from src.core.config import CONFIG

class SovereignRouter:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name.lower()
        self.track = CONFIG.get_agent_track(agent_name)  # insider / stable

        # Define Jurisdictions (Docker Volume Paths)
        # Adjusted for Windows local environment compatibility
        if os.path.exists("/data/evidence") and self.agent_name == "evidence":
             self.base_root = Path("/data/evidence")
        elif os.path.exists("/data/property") and self.agent_name == "property":
             self.base_root = Path("/data/property")
        elif self.agent_name == "evidence":
            self.base_root = Path("Evidence")
        elif self.agent_name == "property":
            self.base_root = Path("Property")
        else:
            raise ValueError(f"Unknown agent_name for router: {agent_name}")

        if self.agent_name == "evidence":
            self.output_dirs = {
                "insider": self.base_root / "Analysis" / "_drafts",
                "stable": self.base_root / "Analysis" / "_verified",
            }
        elif self.agent_name == "property":
            self.output_dirs = {
                "insider": self.base_root / "Scored" / "_drafts",
                "stable": self.base_root / "Scored" / "_production",
            }
        else:
            raise ValueError(f"Unknown agent_name for router: {agent_name}")

        # Resolve Target
        self.target_dir = self.output_dirs.get(self.track)
        if self.target_dir is None:
            self.track = "insider" # Safety Fallback
            self.target_dir = self.output_dirs["insider"]

        self.target_dir.mkdir(parents=True, exist_ok=True)

    def get_execution_mode(self) -> str:
        return "SANDBOX" if self.track == "insider" else "LIVE"

    def save_result(self, filename: str, data: dict) -> str:
        data["_governance"] = {
            "track": self.track,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "agent_name": self.agent_name,
            "status": "PENDING_REVIEW" if self.track == "insider" else "AUTO_VERIFIED",
        }

        safe_filename = Path(filename).name
        output_path = self.target_dir / safe_filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"[{self.agent_name.upper()} | {self.track.upper()}] Saved -> {output_path}")
        return str(output_path)