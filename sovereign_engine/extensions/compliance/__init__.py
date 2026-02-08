"""
Compliance Pack - Configurable controls mapped to customer policy sets.
S3-EXT-016: Regulatory compliance bolt-on.
"""

import json
from typing import Dict, List, Optional
from enum import Enum

class ControlStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "n/a"

class ComplianceControl:
    def __init__(self, control_id: str, name: str, description: str,
                 standard: str, requirement: str, check_function=None):
        self.id = control_id
        self.name = name
        self.description = description
        self.standard = standard  # e.g., "SOC2", "ISO27001", "GDPR"
        self.requirement = requirement
        self.check_function = check_function
    
    def check(self, context: Optional[Dict] = None) -> Dict:
        """Execute compliance check."""
        context = context or {}
        
        try:
            if self.check_function:
                result = self.check_function(context)
                if isinstance(result, bool):
                    status = ControlStatus.PASS if result else ControlStatus.FAIL
                    details = "Check completed"
                else:
                    status, details = result
            else:
                status = ControlStatus.WARNING
                details = "No check function defined"
        except Exception as e:
            status = ControlStatus.FAIL
            details = f"Check failed: {str(e)}"
        
        return {
            "control_id": self.id,
            "name": self.name,
            "status": status.value,
            "details": details,
            "standard": self.standard,
            "requirement": self.requirement,
            "timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

class CompliancePack:
    def __init__(self, pack_name: str = "default"):
        self.pack_name = pack_name
        self.controls = self._load_controls()
    
    def add_control(self, control: ComplianceControl):
        """Add a control to the pack."""
        self.controls[control.id] = control
    
    def run_audit(self, context: Optional[Dict] = None) -> Dict:
        """Run all controls in the pack."""
        results = {
            "pack": self.pack_name,
            "timestamp": self._get_timestamp(),
            "controls": {},
            "summary": {}
        }
        
        for control_id, control in self.controls.items():
            result = control.check(context)
            results["controls"][control_id] = result
        
        # Calculate summary
        status_counts = {}
        for result in results["controls"].values():
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        results["summary"] = {
            "total_controls": len(self.controls),
            "status_counts": status_counts,
            "compliance_score": self._calculate_score(status_counts)
        }
        
        return results
    
    def _calculate_score(self, status_counts: Dict) -> float:
        """Calculate compliance score (0-100)."""
        total = sum(status_counts.values())
        if total == 0:
            return 0.0
        
        weights = {
            "pass": 1.0,
            "warning": 0.5,
            "n/a": 0.0,
            "fail": 0.0
        }
        
        score = 0
        for status, count in status_counts.items():
            score += weights.get(status, 0) * count
        
        return (score / total) * 100
    
    def export_report(self, audit_results: Dict, format: str = "json") -> str:
        """Export compliance report."""
        if format == "json":
            return json.dumps(audit_results, indent=2)
        elif format == "markdown":
            return self._export_markdown(audit_results)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_markdown(self, audit_results: Dict) -> str:
        """Export to markdown format."""
        lines = []
        lines.append(f"# Compliance Audit Report: {self.pack_name}")
        lines.append(f"**Date:** {audit_results['timestamp']}")
        lines.append(f"**Controls:** {audit_results['summary']['total_controls']}")
        lines.append(f"**Score:** {audit_results['summary']['compliance_score']:.1f}%")
        lines.append("")
        
        # Status summary
        lines.append("## Summary")
        for status, count in audit_results['summary']['status_counts'].items():
            lines.append(f"- {status.upper()}: {count}")
        lines.append("")
        
        # Detailed findings
        lines.append("## Detailed Findings")
        for control_id, result in audit_results['controls'].items():
            status_emoji = {
                "pass": "✅",
                "fail": "❌",
                "warning": "⚠️",
                "n/a": "➖"
            }.get(result['status'], "❓")
            
            lines.append(f"### {status_emoji} {result['name']}")
            lines.append(f"**ID:** {control_id}")
            lines.append(f"**Standard:** {result['standard']}")
            lines.append(f"**Requirement:** {result['requirement']}")
            lines.append(f"**Status:** {result['status'].upper()}")
            lines.append(f"**Details:** {result['details']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _load_controls(self) -> Dict:
        """Load controls for this pack."""
        # Default SOC2 controls
        return {
            "soc2-cc1.1": ComplianceControl(
                "soc2-cc1.1",
                "Commitment to Integrity and Ethical Values",
                "The entity demonstrates commitment to integrity and ethical values.",
                "SOC2",
                "CC1.1",
                lambda ctx: True  # Placeholder
            ),
            "soc2-cc2.1": ComplianceControl(
                "soc2-cc2.1",
                "Risk Assessment",
                "The entity identifies risks to the achievement of its objectives.",
                "SOC2",
                "CC2.1",
                lambda ctx: "risk_assessment" in ctx
            ),
            # Add more controls as needed
        }
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

# Factory for common compliance packs
def get_compliance_pack(pack_name: str) -> CompliancePack:
    """Get a pre-configured compliance pack."""
    packs = {
        "soc2": CompliancePack("SOC2"),
        "iso27001": CompliancePack("ISO27001"),
        "gdpr": CompliancePack("GDPR"),
        "hipaa": CompliancePack("HIPAA")
    }
    
    if pack_name not in packs:
        raise ValueError(f"Unknown pack: {pack_name}. Available: {list(packs.keys())}")
    
    return packs[pack_name]
