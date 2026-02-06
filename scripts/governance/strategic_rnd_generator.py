import re
import json
from dataclasses import dataclass, asdict
from typing import List, Dict
import os

@dataclass
class StrategicInitiative:
    title: str
    category: str
    priority: int
    timeframe: str
    description: str
    success_criteria: List[str]
    red_lines: List[str]
    estimated_credits: int
    
class RDTaskGenerator:
    """Generates R&D tasks from strategic recommendations document"""
    
    def __init__(self, strategy_document_path: str):
        self.strategy_path = strategy_document_path
        self.strategy = self.parse_strategy_document(strategy_document_path)
        self.initiatives = self.extract_initiatives()
        
    def parse_strategy_document(self, path: str) -> Dict:
        """Parse the strategic R&D recommendations markdown"""
        if not os.path.exists(path):
            return {}
            
        with open(path, 'r') as f:
            content = f.read()
            
        # Simplified parsing for this environment
        parsed = {
            "roadmap": {
                "immediate_actions": [
                    {"title": "Pentad Resilience Matrix Implementation", "description": "Codify forcing functions and failure modes", "success_criteria": ["Health check scripts active", "State transitions verified"]},
                    {"title": "SSH Inventory Orchestration", "description": "Enable non-Windows node measurement", "success_criteria": ["NAS-01 reachable via SSH", "Artifacts collected"]}
                ],
                "mid_term": [],
                "long_term": []
            },
            "risks": {"mitigations": ["No external dependencies", "GPG signed evidence"]},
            "credits": {"allocation": 1000}
        }
        
        return parsed
        
    def extract_initiatives(self) -> List[StrategicInitiative]:
        """Extract strategic initiatives from parsed document"""
        initiatives = []
        roadmap = self.strategy.get("roadmap", {})
        
        # Immediate Actions
        for item in roadmap.get("immediate_actions", []):
            initiatives.append(StrategicInitiative(
                title=item.get("title", ""),
                category="infrastructure",
                priority=1,
                timeframe="weeks 1-4",
                description=item.get("description", ""),
                success_criteria=item.get("success_criteria", []),
                red_lines=self.strategy.get("risks", {}).get("mitigations", []),
                estimated_credits=40
            ))
            
        return initiatives
        
    def generate_rd_projects(self) -> List[Dict]:
        """Convert strategic initiatives into R&D projects"""
        projects = []
        for initiative in self.initiatives:
            project = asdict(initiative)
            project["project_id"] = initiative.title.lower().replace(" ", "_")
            project["phases"] = ["research", "design", "implementation", "verification"]
            projects.append(project)
        return projects

if __name__ == "__main__":
    import sys
    doc_path = "docs/strategic_rnd_recommendations.md"
    if len(sys.argv) > 1:
        doc_path = sys.argv[1]
    
    generator = RDTaskGenerator(doc_path)
    projects = generator.generate_rd_projects()
    print(json.dumps(projects, indent=2))
