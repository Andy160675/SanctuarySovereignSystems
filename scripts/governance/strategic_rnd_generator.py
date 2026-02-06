#!/usr/bin/env python3
import argparse
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Dict


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
    def __init__(self, strategy_document_path: str):
        self.strategy_path = strategy_document_path
        self.strategy = self.parse_strategy_document(strategy_document_path)
        self.initiatives = self.extract_initiatives()

    def parse_strategy_document(self, path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        parsed: Dict = {}
        # naive extraction of sections by headings
        sections = re.split(r"\n#+\s+", content)
        for section in sections:
            s = section.strip()
            if not s:
                continue
            lines = s.splitlines()
            title = lines[0].strip().lower()
            body = "\n".join(lines[1:])
            if "tactical roadmap" in title or "roadmap" in title:
                parsed["roadmap"] = self._parse_bullets(body)
            if "risk" in title:
                parsed["risks"] = {"mitigations": self._parse_list_items(body)}
            if "credit" in title:
                parsed["credits"] = {"notes": body}
        return parsed

    def _parse_bullets(self, body: str) -> Dict:
        buckets = {"immediate_actions": [], "mid_term": [], "long_term": []}
        section = None
        for line in body.splitlines():
            l = line.strip()
            if not l:
                continue
            if l.lower().startswith("immediate"):
                section = "immediate_actions"; continue
            if l.lower().startswith("mid"):
                section = "mid_term"; continue
            if l.lower().startswith("long"):
                section = "long_term"; continue
            if l.startswith("-") and section:
                buckets[section].append({"title": l.lstrip("- ")})
        return buckets

    def _parse_list_items(self, body: str) -> List[str]:
        items: List[str] = []
        for line in body.splitlines():
            l = line.strip()
            if l.startswith("-"):
                items.append(l.lstrip("- ").strip())
        return items

    def extract_initiatives(self) -> List[StrategicInitiative]:
        initiatives: List[StrategicInitiative] = []
        roadmap = self.strategy.get("roadmap", {})
        risks = self.strategy.get("risks", {}).get("mitigations", [])

        for item in roadmap.get("immediate_actions", []):
            initiatives.append(StrategicInitiative(
                title=item.get("title", "Immediate Initiative"),
                category="infrastructure",
                priority=1,
                timeframe="weeks 1-4",
                description=item.get("description", ""),
                success_criteria=item.get("success_criteria", []),
                red_lines=risks,
                estimated_credits=40,
            ))
        for item in roadmap.get("mid_term", []):
            initiatives.append(StrategicInitiative(
                title=item.get("title", "Mid-term Initiative"),
                category="governance",
                priority=2,
                timeframe="weeks 5-12",
                description=item.get("description", ""),
                success_criteria=item.get("success_criteria", []),
                red_lines=risks,
                estimated_credits=30,
            ))
        for item in roadmap.get("long_term", []):
            initiatives.append(StrategicInitiative(
                title=item.get("title", "Long-term Initiative"),
                category="intelligence",
                priority=3,
                timeframe="weeks 13+",
                description=item.get("description", ""),
                success_criteria=item.get("success_criteria", []),
                red_lines=risks,
                estimated_credits=30,
            ))
        return initiatives

    def generate_rd_projects(self) -> List[Dict]:
        projects: List[Dict] = []
        for i in self.initiatives:
            project = {
                "project_id": self._project_id(i.title),
                "title": i.title,
                "description": i.description,
                "category": i.category,
                "priority": i.priority,
                "timeframe": i.timeframe,
                "estimated_credits": i.estimated_credits,
                "phases": [
                    {"name": "research", "deliverables": ["Literature review", "Tech assessment", "Risk analysis"], "success_criteria": i.success_criteria[:2]},
                    {"name": "design", "deliverables": ["Architecture spec", "Security protocol", "Integration plan"], "success_criteria": i.success_criteria[2:4]},
                    {"name": "implementation", "deliverables": ["Prototype", "Tests", "Docs"], "success_criteria": i.success_criteria[4:6]},
                    {"name": "verification", "deliverables": ["Compliance report", "Benchmarks", "Security audit"], "success_criteria": i.success_criteria[6:]},
                ],
                "red_lines": i.red_lines,
                "evidence_requirements": [
                    "All code changes must be signed",
                    "All tests must pass",
                    "All documentation must be complete",
                    "All security checks must pass",
                ],
            }
            projects.append(project)
        return projects

    def _project_id(self, title: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", title.strip().lower())
        return base.strip("-")[:40] or "project"


def main():
    ap = argparse.ArgumentParser(description="Generate R&D projects from a strategic markdown document")
    ap.add_argument("--strategy", required=True, help="Path to strategic_rnd_recommendations.md")
    ap.add_argument("--output-json", action="store_true", help="Print projects JSON to stdout")
    args = ap.parse_args()

    gen = RDTaskGenerator(args.strategy)
    projects = gen.generate_rd_projects()

    if args.output_json:
        print(json.dumps(projects, indent=2))
    else:
        for p in projects:
            print(f"- {p['project_id']}: {p['title']} [{p['category']}] priority={p['priority']}")


if __name__ == "__main__":
    main()
