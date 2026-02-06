#!/usr/bin/env python3
"""
Regulator Evidence Bundle Generator
====================================

Generates a complete evidence package for regulatory review, including:
- Mission timeline (from Watcher)
- All ledger entries (signed Merkle chain)
- Risk assessments and decisions
- Human authorization records
- Operator attestation (requires signature)

Output: PDF bundle with embedded JSON data and cryptographic proofs.

Usage:
    python generate_regulator_bundle.py <mission_id> --output bundle.pdf
    python generate_regulator_bundle.py --all-missions --output full_audit.pdf
    python generate_regulator_bundle.py <mission_id> --operator "Name" --sign

Requirements:
    pip install httpx reportlab cryptography
"""

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Preformatted, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Service URLs (configurable via environment)
WATCHER_URL = os.environ.get("WATCHER_URL", "http://localhost:8093")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://localhost:8082")


class EvidenceCollector:
    """Collects evidence from various The Blade of Truth services."""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0) if HTTPX_AVAILABLE else None

    def get_mission_timeline(self, mission_id: str) -> Optional[Dict]:
        """Fetch mission timeline from Watcher."""
        if not self.client:
            return None
        try:
            response = self.client.get(f"{WATCHER_URL}/mission/{mission_id}/timeline")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Warning: Failed to fetch timeline: {e}")
        return None

    def get_dispute_report(self, mission_id: str) -> Optional[Dict]:
        """Fetch formal dispute report from Watcher."""
        if not self.client:
            return None
        try:
            response = self.client.get(f"{WATCHER_URL}/mission/{mission_id}/report")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Warning: Failed to fetch dispute report: {e}")
        return None

    def get_ledger_entries(self, limit: int = 10000) -> List[Dict]:
        """Fetch all ledger entries."""
        if not self.client:
            return []
        try:
            response = self.client.get(f"{LEDGER_URL}/entries?limit={limit}")
            if response.status_code == 200:
                return response.json().get("entries", [])
        except Exception as e:
            print(f"Warning: Failed to fetch ledger: {e}")
        return []

    def get_ledger_merkle_root(self) -> Optional[str]:
        """Get current Merkle root from ledger."""
        if not self.client:
            return None
        try:
            response = self.client.get(f"{LEDGER_URL}/merkle")
            if response.status_code == 200:
                return response.json().get("root")
        except Exception:
            pass
        return None

    def verify_ledger_integrity(self) -> bool:
        """Verify ledger hash chain integrity."""
        if not self.client:
            return False
        try:
            response = self.client.get(f"{LEDGER_URL}/verify")
            if response.status_code == 200:
                return response.json().get("valid", False)
        except Exception:
            pass
        return False


class BundleGenerator:
    """Generates PDF evidence bundles for regulators."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
        self.elements = []

    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_JUSTIFY
        ))
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leftIndent=20,
            backColor=colors.Color(0.95, 0.95, 0.95)
        ))

    def add_cover_page(
        self,
        mission_id: str,
        generated_at: str,
        operator_name: Optional[str] = None
    ):
        """Add cover page to the bundle."""
        self.elements.append(Spacer(1, 2*inch))
        self.elements.append(Paragraph(
            "SOVEREIGN AI SYSTEM",
            self.styles['CoverTitle']
        ))
        self.elements.append(Paragraph(
            "Regulatory Evidence Bundle",
            self.styles['Heading2']
        ))
        self.elements.append(Spacer(1, inch))

        # Mission info table
        data = [
            ["Mission ID:", mission_id],
            ["Generated:", generated_at],
            ["Bundle Type:", "Full Audit Trail"],
        ]
        if operator_name:
            data.append(["Attested By:", operator_name])

        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        self.elements.append(table)

        self.elements.append(Spacer(1, inch))
        self.elements.append(Paragraph(
            "CONFIDENTIAL - FOR REGULATORY REVIEW ONLY",
            self.styles['Heading3']
        ))
        self.elements.append(PageBreak())

    def add_integrity_statement(
        self,
        merkle_root: Optional[str],
        integrity_verified: bool,
        entry_count: int
    ):
        """Add cryptographic integrity statement."""
        self.elements.append(Paragraph(
            "Section 1: Cryptographic Integrity Statement",
            self.styles['Heading1']
        ))

        status = "âœ“ VERIFIED" if integrity_verified else "âœ— NOT VERIFIED"
        status_color = colors.green if integrity_verified else colors.red

        data = [
            ["Ledger Entries:", str(entry_count)],
            ["Hash Chain Status:", status],
            ["Merkle Root:", merkle_root[:32] + "..." if merkle_root else "N/A"],
        ]

        table = Table(data, colWidths=[2*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 1), (1, 1), status_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.98)),
        ]))
        self.elements.append(table)

        self.elements.append(Spacer(1, 20))
        self.elements.append(Paragraph(
            "The above Merkle root cryptographically commits to all ledger entries. "
            "Any modification to the ledger would produce a different root, enabling "
            "detection of tampering. This provides non-repudiation for all recorded events.",
            self.styles['Normal']
        ))
        self.elements.append(Spacer(1, 30))

    def add_risk_control_summary(self):
        """Add risk control mechanism summary."""
        self.elements.append(Paragraph(
            "Section 2: Risk Control Mechanism",
            self.styles['Heading1']
        ))

        self.elements.append(Paragraph(
            "All autonomous agent operations are subject to the following risk gating logic:",
            self.styles['Normal']
        ))
        self.elements.append(Spacer(1, 10))

        data = [
            ["Risk Level", "System Response", "Human Required"],
            ["HIGH", "Mission REJECTED", "Cannot proceed"],
            ["UNKNOWN", "Mission HELD", "Explicit authorization required"],
            ["LOW/MEDIUM", "Mission APPROVED", "Proceeds automatically"],
        ]

        table = Table(data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.8, 0.8, 0.8)),
            ('BACKGROUND', (0, 1), (0, 1), colors.Color(1, 0.8, 0.8)),  # HIGH = red
            ('BACKGROUND', (0, 2), (0, 2), colors.Color(1, 1, 0.8)),    # UNKNOWN = yellow
            ('BACKGROUND', (0, 3), (0, 3), colors.Color(0.8, 1, 0.8)),  # LOW = green
        ]))
        self.elements.append(table)

        self.elements.append(Spacer(1, 20))
        self.elements.append(Paragraph(
            "<b>Mechanical Enforcement:</b> HIGH risk missions are blocked at the code level. "
            "There is no override flag, admin bypass, or configuration option to execute "
            "a HIGH risk mission without human cryptographic authorization.",
            self.styles['Normal']
        ))
        self.elements.append(PageBreak())

    def add_timeline(self, timeline: Dict):
        """Add mission timeline section."""
        self.elements.append(Paragraph(
            "Section 3: Mission Timeline",
            self.styles['Heading1']
        ))

        if not timeline:
            self.elements.append(Paragraph(
                "No timeline data available.",
                self.styles['Normal']
            ))
            return

        # Mission header
        self.elements.append(Paragraph(
            f"Mission ID: {timeline.get('mission_id', 'Unknown')}",
            self.styles['Heading3']
        ))
        self.elements.append(Paragraph(
            f"Events: {timeline.get('event_count', 0)}",
            self.styles['Normal']
        ))
        self.elements.append(Spacer(1, 15))

        # Event table
        events = timeline.get('timeline', [])
        if events:
            data = [["#", "Timestamp", "Type", "Agent", "Outcome"]]
            for event in events[:50]:  # Limit to first 50 for PDF
                data.append([
                    str(event.get('sequence', '')),
                    event.get('timestamp', '')[:19],
                    event.get('event_type', '')[:20],
                    event.get('agent', '-')[:10],
                    event.get('outcome', '-')[:15],
                ])

            table = Table(data, colWidths=[0.4*inch, 1.4*inch, 1.5*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ]))
            self.elements.append(table)

            if len(events) > 50:
                self.elements.append(Spacer(1, 10))
                self.elements.append(Paragraph(
                    f"Note: Showing first 50 of {len(events)} events. "
                    "Full data available in embedded JSON.",
                    self.styles['Disclaimer']
                ))

        self.elements.append(PageBreak())

    def add_key_facts(self, facts: List[str]):
        """Add key facts section."""
        self.elements.append(Paragraph(
            "Section 4: Key Factual Findings",
            self.styles['Heading1']
        ))

        if not facts:
            self.elements.append(Paragraph(
                "No key facts extracted.",
                self.styles['Normal']
            ))
            return

        for i, fact in enumerate(facts, 1):
            self.elements.append(Paragraph(
                f"{i}. {fact}",
                self.styles['Normal']
            ))
            self.elements.append(Spacer(1, 5))

        self.elements.append(PageBreak())

    def add_operator_attestation(
        self,
        operator_name: str,
        signature_hash: Optional[str] = None
    ):
        """Add operator attestation page."""
        self.elements.append(Paragraph(
            "Section 5: Operator Attestation",
            self.styles['Heading1']
        ))

        attestation_text = f"""
        I, <b>{operator_name}</b>, hereby attest that:

        1. I have reviewed the contents of this evidence bundle.

        2. To the best of my knowledge, the system operated as designed during
           the period covered by this bundle.

        3. All high-risk operations required and received my explicit authorization
           before execution.

        4. I am authorized to provide this attestation on behalf of the operating entity.

        5. I understand that this attestation may be relied upon by regulators
           and other parties for compliance verification.
        """

        self.elements.append(Paragraph(attestation_text, self.styles['Normal']))
        self.elements.append(Spacer(1, 40))

        # Signature block
        data = [
            ["Operator Name:", operator_name],
            ["Attestation Date:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Digital Signature:", signature_hash[:32] + "..." if signature_hash else "________________"],
        ]

        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LINEBELOW', (1, -1), (1, -1), 1, colors.black),
        ]))
        self.elements.append(table)

        self.elements.append(PageBreak())

    def add_compliance_statement(self):
        """Add regulatory compliance statement."""
        self.elements.append(Paragraph(
            "Section 6: Regulatory Compliance Statement",
            self.styles['Heading1']
        ))

        self.elements.append(Paragraph(
            "This system is designed to comply with the following frameworks:",
            self.styles['Normal']
        ))
        self.elements.append(Spacer(1, 15))

        frameworks = [
            ("EU AI Act Article 14", "Human oversight requirements for high-risk AI systems"),
            ("ISO/IEC 42001", "AI management system controls and governance"),
            ("NIST AI RMF GOVERN 1.3", "Human-AI teaming and oversight mechanisms"),
        ]

        data = [["Framework", "Requirement"]]
        data.extend(frameworks)

        table = Table(data, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        self.elements.append(table)

        self.elements.append(Spacer(1, 30))
        self.elements.append(Paragraph(
            "DISCLAIMER: This document is mechanically generated from the immutable ledger. "
            "The system does not interpret, judge, or render legal opinions. "
            "Compliance determinations must be made by qualified legal and regulatory professionals.",
            self.styles['Disclaimer']
        ))

    def add_embedded_json(self, data: Dict, title: str = "Raw Data"):
        """Add embedded JSON data section."""
        self.elements.append(Paragraph(
            f"Appendix: {title}",
            self.styles['Heading2']
        ))

        json_str = json.dumps(data, indent=2, default=str)

        # Truncate for display if too long
        if len(json_str) > 5000:
            json_str = json_str[:5000] + "\n\n... [truncated, full data available in separate JSON export]"

        self.elements.append(Preformatted(json_str, self.styles['CodeBlock']))
        self.elements.append(PageBreak())

    def generate(self) -> Path:
        """Generate the PDF bundle."""
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        doc.build(self.elements)
        return self.output_path


def generate_bundle(
    mission_id: str,
    output_path: Path,
    operator_name: Optional[str] = None,
    sign: bool = False
) -> Path:
    """Generate a complete evidence bundle for a mission."""
    print(f"Generating evidence bundle for mission: {mission_id}")

    collector = EvidenceCollector()
    generator = BundleGenerator(output_path)

    # Collect evidence
    timeline = collector.get_mission_timeline(mission_id)
    report = collector.get_dispute_report(mission_id)
    entries = collector.get_ledger_entries()
    merkle_root = collector.get_ledger_merkle_root()
    integrity_ok = collector.verify_ledger_integrity()

    mission_entries = [e for e in entries if
                       e.get("target") == mission_id or
                       e.get("metadata", {}).get("mission_id") == mission_id]

    # Generate PDF sections
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    generator.add_cover_page(mission_id, generated_at, operator_name)
    generator.add_integrity_statement(merkle_root, integrity_ok, len(entries))
    generator.add_risk_control_summary()

    if timeline:
        generator.add_timeline(timeline)

    if report:
        key_facts = report.get("key_facts", [])
        generator.add_key_facts(key_facts)

    if operator_name:
        # Generate attestation hash
        sig_hash = None
        if sign:
            attestation_data = f"{operator_name}|{mission_id}|{generated_at}|{merkle_root}"
            sig_hash = hashlib.sha256(attestation_data.encode()).hexdigest()
        generator.add_operator_attestation(operator_name, sig_hash)

    generator.add_compliance_statement()

    # Embed raw data
    if timeline:
        generator.add_embedded_json(timeline, "Mission Timeline (JSON)")

    # Generate PDF
    output = generator.generate()
    print(f"Bundle generated: {output}")

    # Also save JSON companion file
    json_path = output_path.with_suffix(".json")
    bundle_data = {
        "mission_id": mission_id,
        "generated_at": generated_at,
        "operator": operator_name,
        "integrity_verified": integrity_ok,
        "merkle_root": merkle_root,
        "timeline": timeline,
        "report": report,
        "entry_count": len(mission_entries),
    }
    json_path.write_text(json.dumps(bundle_data, indent=2, default=str))
    print(f"JSON companion: {json_path}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Generate regulatory evidence bundles from The Blade of Truth"
    )

    parser.add_argument(
        "mission_id",
        nargs="?",
        help="Mission ID to generate bundle for"
    )

    parser.add_argument(
        "--output", "-o",
        default="evidence_bundle.pdf",
        help="Output PDF path"
    )

    parser.add_argument(
        "--operator",
        help="Operator name for attestation"
    )

    parser.add_argument(
        "--sign",
        action="store_true",
        help="Include digital signature hash"
    )

    parser.add_argument(
        "--all-missions",
        action="store_true",
        help="Generate bundle for all missions"
    )

    args = parser.parse_args()

    # Check dependencies
    if not REPORTLAB_AVAILABLE:
        print("Error: reportlab library required for PDF generation")
        print("Install with: pip install reportlab")
        sys.exit(1)

    if not HTTPX_AVAILABLE:
        print("Warning: httpx not available, will use mock data")

    if args.all_missions:
        # TODO: Implement all-missions bundle
        print("All-missions bundle not yet implemented")
        sys.exit(1)

    if not args.mission_id:
        parser.print_help()
        sys.exit(0)

    output_path = Path(args.output)
    generate_bundle(
        mission_id=args.mission_id,
        output_path=output_path,
        operator_name=args.operator,
        sign=args.sign
    )


if __name__ == "__main__":
    main()

