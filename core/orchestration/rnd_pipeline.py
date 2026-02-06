# rnd_pipeline.py
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
import yaml

class RDPPhase(Enum):
    RESEARCH = "research"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    ARCHIVED = "archived"

class RedLineViolation(Exception):
    pass

class InvalidPhaseSequence(Exception):
    pass

class RDProject:
    def __init__(self, project_id: str, title: str, description: str):
        self.project_id = project_id
        self.title = title
        self.description = description
        self.created = datetime.utcnow()
        self.current_phase = RDPPhase.RESEARCH
        self.evidence_chain = []
        self.attestations = []
        self.red_line_checks = []
        
    def advance_phase(self, phase: RDPPhase, evidence: Dict):
        """Advance to next phase with evidence"""
        # 1. Check red lines
        if not self.check_red_lines(phase):
            raise RedLineViolation("Cannot advance - red line violation")
            
        # 2. Generate phase transition evidence
        transition_hash = self.generate_transition_hash(phase, evidence)
        
        # 3. Store evidence
        self.evidence_chain.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from_phase": self.current_phase.value,
            "to_phase": phase.value,
            "evidence": evidence,
            "hash": transition_hash,
            "verified_by": None  # Will be filled after attestation
        })
        
        # 4. Update phase
        self.current_phase = phase
        
        # 5. Queue for attestation (stubbed)
        # self.queue_attestation(phase)
        
        return transition_hash
        
    def check_red_lines(self, target_phase: RDPPhase) -> bool:
        """Check all red lines for the phase transition"""
        # Mocking for now - in production this would load from rnd_constitution.yaml
        red_lines = ["No external dependencies without isolation", "No data sovereignty violations"]
        
        for line in red_lines:
            # Placeholder check logic
            check_result = {"passed": True, "detail": "Automatic check passed"}
            self.red_line_checks.append({
                "timestamp": datetime.utcnow().isoformat(),
                "red_line": line,
                "result": check_result,
                "phase": target_phase.value
            })
            
            if not check_result["passed"]:
                return False
                
        return True
        
    def generate_transition_hash(self, phase: RDPPhase, evidence: Dict) -> str:
        """Create cryptographic hash of phase transition"""
        data = {
            "project_id": self.project_id,
            "from_phase": self.current_phase.value,
            "to_phase": phase.value,
            "timestamp": datetime.utcnow().isoformat(),
            "evidence": evidence
        }
        
        # Include previous hash for chain integrity
        if self.evidence_chain:
            data["previous_hash"] = self.evidence_chain[-1]["hash"]
            
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

class RDPipelineOrchestrator:
    """Main R&D pipeline orchestration engine"""
    
    def __init__(self, constitution_path: str):
        self.projects: Dict[str, RDProject] = {}
        self.active_projects: List[str] = []
        self.completed_projects: List[str] = []
        self.constitution_path = Path(constitution_path)
        
    def load_constitution(self) -> Dict:
        if self.constitution_path.exists():
            with open(self.constitution_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
        
    def generate_project_id(self, title: str, category: str) -> str:
        clean_title = "".join(filter(str.isalnum, title)).lower()[:10]
        stamp = datetime.utcnow().strftime("%Y%m%d")
        return f"{category}_{clean_title}_{stamp}"

    def create_project(self, title: str, description: str, category: str) -> RDProject:
        """Create new R&D project with constitutional constraints"""
        project_id = self.generate_project_id(title, category)
        
        project = RDProject(project_id, title, description)
        
        # Store in registry
        self.projects[project_id] = project
        self.active_projects.append(project_id)
        
        # Generate initial evidence
        constitution = self.load_constitution()
        initial_evidence = {
            "action": "project_creation",
            "constitution_version": constitution.get("version", "unknown"),
            "category": category
        }
        
        project.evidence_chain.append({
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "creation",
            "evidence": initial_evidence,
            "hash": project.generate_transition_hash(RDPPhase.RESEARCH, initial_evidence)
        })
        
        return project

    def validate_phase_sequence(self, current: RDPPhase, target: RDPPhase) -> bool:
        # Simplistic sequential validation
        flow = [RDPPhase.RESEARCH, RDPPhase.DESIGN, RDPPhase.IMPLEMENTATION, RDPPhase.VERIFICATION, RDPPhase.ARCHIVED]
        try:
            return flow.index(target) == flow.index(current) + 1
        except ValueError:
            return False

    def execute_phase(self, project_id: str, phase: RDPPhase, 
                     phase_data: Dict, operator_id: str) -> bool:
        """Execute a phase of R&D with full governance"""
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
            
        # 1. Check phase sequencing
        if not self.validate_phase_sequence(project.current_phase, phase):
            raise InvalidPhaseSequence(
                f"Cannot transition from {project.current_phase} to {phase}"
            )
            
        # 2. Advance phase with evidence
        evidence = {
            "operator": operator_id,
            "phase_data": phase_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        transition_hash = project.advance_phase(phase, evidence)
        
        # 3. Update project registry
        if phase == RDPPhase.VERIFICATION:
            self.active_projects.remove(project_id)
            self.completed_projects.append(project_id)
            
        return True
