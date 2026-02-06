from __future__ import annotations

from datetime import datetime
from enum import Enum
import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

import yaml


REGISTRY_PATH = Path("evidence_store/rnd_registry.json")
REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


class RDPPhase(Enum):
    RESEARCH = "research"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    ARCHIVED = "archived"


class RDProject:
    def __init__(self, project_id: str, title: str, description: str):
        self.project_id = project_id
        self.title = title
        self.description = description
        self.created = datetime.utcnow().isoformat()
        self.current_phase = RDPPhase.RESEARCH
        self.evidence_chain: List[Dict] = []
        self.attestations: List[Dict] = []
        self.red_line_checks: List[Dict] = []

    # --- Evidence & Red lines ---
    def advance_phase(self, phase: RDPPhase, evidence: Dict) -> str:
        if not self.check_red_lines(phase):
            raise RuntimeError("Red line violation - cannot advance phase")

        transition_hash = self.generate_transition_hash(phase, evidence)

        self.evidence_chain.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from_phase": self.current_phase.value,
            "to_phase": phase.value,
            "evidence": evidence,
            "hash": transition_hash,
            "verified_by": None,
        })

        self.current_phase = phase
        # queue attestation placeholder
        self.attestations.append({
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase.value,
            "status": "PENDING",
        })
        return transition_hash

    def check_red_lines(self, target_phase: RDPPhase) -> bool:
        constitution = load_constitution()
        red_lines = constitution.get("red_lines", [])
        for line in red_lines:
            check_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "red_line": line,
                "phase": target_phase.value,
                "passed": True,  # placeholder for real checks
            }
            self.red_line_checks.append(check_result)
            if not check_result["passed"]:
                return False
        return True

    def generate_transition_hash(self, phase: RDPPhase, evidence: Dict) -> str:
        payload = {
            "project_id": self.project_id,
            "from_phase": self.current_phase.value,
            "to_phase": phase.value,
            "timestamp": datetime.utcnow().isoformat(),
            "evidence": evidence,
        }
        if self.evidence_chain:
            payload["previous_hash"] = self.evidence_chain[-1]["hash"]
        text = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(text).hexdigest()


class RDPipelineOrchestrator:
    def __init__(self):
        self.state = self._load_registry()

    # --- Registry persistence ---
    def _load_registry(self) -> Dict:
        if REGISTRY_PATH.exists():
            return json.loads(REGISTRY_PATH.read_text())
        return {"projects": {}, "active": [], "completed": []}

    def _save_registry(self) -> None:
        REGISTRY_PATH.write_text(json.dumps(self.state, indent=2))

    # --- Constitution ---
    @property
    def constitution(self) -> Dict:
        return load_constitution()

    # --- Project lifecycle ---
    def generate_project_id(self, title: str, category: str) -> str:
        base = f"{title}:{category}:{datetime.utcnow().isoformat()}"
        return hashlib.sha1(base.encode()).hexdigest()[:12]

    def create_project(self, title: str, description: str, category: str) -> RDProject:
        pid = self.generate_project_id(title, category)
        project = RDProject(pid, title, description)

        initial_evidence = {
            "action": "project_creation",
            "constitution_version": self.constitution.get("version", "unknown"),
            "category": category,
        }
        project.evidence_chain.append({
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "creation",
            "evidence": initial_evidence,
            "hash": project.generate_transition_hash(RDPPhase.RESEARCH, initial_evidence),
        })

        self.state["projects"][pid] = project.__dict__
        self.state["active"].append(pid)
        self._save_registry()
        return project

    def validate_phase_sequence(self, current: RDPPhase, target: RDPPhase) -> bool:
        order = [RDPPhase.RESEARCH, RDPPhase.DESIGN, RDPPhase.IMPLEMENTATION, RDPPhase.VERIFICATION]
        try:
            return order.index(target) == order.index(current) + 1
        except ValueError:
            return False

    def execute_phase(self, project_id: str, target_phase: RDPPhase, evidence: Dict) -> str:
        proj_data = self.state["projects"].get(project_id)
        if not proj_data:
            raise KeyError(f"Project {project_id} not found")
        project = RDProject(**{k: v for k, v in proj_data.items() if k in {"project_id", "title", "description"}})
        project.created = proj_data["created"]
        project.current_phase = RDPPhase(proj_data["current_phase"]["value"] if isinstance(proj_data["current_phase"], dict) else proj_data["current_phase"]) if "current_phase" in proj_data else RDPPhase.RESEARCH
        project.evidence_chain = proj_data.get("evidence_chain", [])
        project.attestations = proj_data.get("attestations", [])
        project.red_line_checks = proj_data.get("red_line_checks", [])

        # validate sequence
        if not self.validate_phase_sequence(project.current_phase, target_phase):
            raise RuntimeError(f"Invalid phase transition {project.current_phase.value} -> {target_phase.value}")

        h = project.advance_phase(target_phase, evidence)

        # persist back
        self.state["projects"][project_id] = project.__dict__
        if target_phase == RDPPhase.VERIFICATION:
            if project_id in self.state["active"]:
                self.state["active"].remove(project_id)
            self.state["completed"].append(project_id)
        self._save_registry()
        return h

    def list_active(self) -> List[str]:
        return list(self.state.get("active", []))

    def get_state(self, project_id: str) -> str:
        proj = self.state["projects"].get(project_id)
        if not proj:
            return "not_found"
        phase = proj.get("current_phase")
        if isinstance(phase, dict):
            phase = phase.get("value")
        return f"{phase or 'research'}"


# --- Utilities ---

def load_constitution() -> Dict:
    cfg_path = Path("core/governance/rnd_constitution.yaml")
    if cfg_path.exists():
        return yaml.safe_load(cfg_path.read_text()) or {}
    return {}


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="R&D Pipeline Orchestrator")
    sub = parser.add_subparsers(dest="cmd")

    p_create = sub.add_parser("create-project")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--description", required=True)
    p_create.add_argument("--category", required=True)

    p_execute = sub.add_parser("execute-phase")
    p_execute.add_argument("--project", required=True)
    p_execute.add_argument("--phase", required=True, choices=[p.value for p in RDPPhase])
    p_execute.add_argument("--evidence", required=False, default="{}")

    sub.add_parser("list-active")

    p_state = sub.add_parser("get-state")
    p_state.add_argument("--project", required=True)

    args = parser.parse_args()
    orch = RDPipelineOrchestrator()

    if args.cmd == "create-project":
        proj = orch.create_project(args.title, args.description, args.category)
        print(json.dumps({"project_id": proj.project_id, "title": proj.title}, indent=2))
    elif args.cmd == "execute-phase":
        target = RDPPhase(args.phase)
        evidence = json.loads(args.evidence)
        h = orch.execute_phase(args.project, target, evidence)
        print(json.dumps({"project_id": args.project, "phase": target.value, "hash": h}, indent=2))
    elif args.cmd == "list-active":
        print("\n".join(orch.list_active()))
    elif args.cmd == "get-state":
        print(orch.get_state(args.project))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
