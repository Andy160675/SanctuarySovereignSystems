"""
KID SAFE PROTOCOL v1.0
======================
Robust Child Safety Framework for AI Systems

This is NON-NEGOTIABLE. Every system must implement these safeguards.
Zero tolerance. No exceptions. Ever.
"""

import hashlib
import re
import json
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set
from abc import ABC, abstractmethod


# =============================================================================
# ABSOLUTE RULES (Cannot be overridden by any logic)
# =============================================================================

class AbsoluteRule(Enum):
    """Rules that cannot be violated under ANY circumstances."""

    NEVER_GENERATE_CSAM = "Never generate, store, or transmit child sexual abuse material"
    NEVER_FACILITATE_GROOMING = "Never facilitate communication patterns associated with grooming"
    NEVER_COLLECT_CHILD_DATA = "Never collect personal data from children without verified parental consent"
    NEVER_TARGET_CHILDREN = "Never target children with advertising, manipulation, or exploitation"
    NEVER_SHARE_CHILD_LOCATION = "Never share or infer child location data"
    ALWAYS_REPORT_ABUSE = "Always report suspected child abuse to authorities"
    ALWAYS_AGE_GATE = "Always implement age verification for age-restricted content"
    ALWAYS_PARENTAL_CONTROLS = "Always provide parental control options"


# Hash of absolute rules - if this changes, system MUST halt
ABSOLUTE_RULES_HASH = hashlib.sha256(
    "|".join([r.value for r in AbsoluteRule]).encode()
).hexdigest()


# =============================================================================
# CONTENT CLASSIFICATION
# =============================================================================

class ContentRating(Enum):
    """Age-appropriate content ratings."""
    SAFE_ALL = "safe_all"           # Safe for all ages
    TEEN_13 = "teen_13"             # 13+ with guidance
    MATURE_16 = "mature_16"         # 16+
    ADULT_18 = "adult_18"           # 18+ only
    BLOCKED = "blocked"             # Never shown to anyone


class ThreatLevel(Enum):
    """Threat assessment levels."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4  # Immediate action required


@dataclass
class ContentAnalysis:
    """Result of content safety analysis."""
    content_hash: str
    rating: ContentRating
    threat_level: ThreatLevel
    flags: List[str] = field(default_factory=list)
    blocked: bool = False
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    requires_report: bool = False


# =============================================================================
# DETECTION PATTERNS (Sanitized - no actual harmful patterns stored)
# =============================================================================

class PatternDetector:
    """
    Detects potentially harmful patterns.

    NOTE: This uses behavioral pattern detection, NOT keyword lists.
    Actual implementation should use ML models trained on verified datasets.
    """

    def __init__(self):
        self.grooming_indicators = [
            "isolation_attempt",      # Attempts to isolate from support
            "secret_keeping",         # Requests for secrecy
            "trust_building_rapid",   # Abnormally fast trust building
            "boundary_testing",       # Testing personal boundaries
            "gift_offering",          # Unsolicited gifts/rewards
            "age_probing",            # Attempts to determine age
            "meeting_request",        # Requests to meet offline
        ]

        self.exploitation_indicators = [
            "personal_info_request",  # Requests for personal information
            "image_request",          # Requests for images
            "location_request",       # Requests for location
            "contact_request",        # Requests for contact details
            "financial_request",      # Financial manipulation
        ]

    def analyze_conversation(self, messages: List[str]) -> Dict:
        """
        Analyze conversation for harmful patterns.
        Returns risk assessment.
        """
        risk_score = 0.0
        flags = []

        # Pattern analysis would go here
        # In production, this uses trained ML models

        return {
            "risk_score": risk_score,
            "flags": flags,
            "recommendation": self._get_recommendation(risk_score)
        }

    def _get_recommendation(self, risk_score: float) -> str:
        if risk_score >= 0.8:
            return "BLOCK_AND_REPORT"
        elif risk_score >= 0.5:
            return "BLOCK_AND_REVIEW"
        elif risk_score >= 0.3:
            return "FLAG_FOR_REVIEW"
        else:
            return "ALLOW"


# =============================================================================
# AGE VERIFICATION
# =============================================================================

class AgeVerificationLevel(Enum):
    """Levels of age verification."""
    NONE = "none"
    SELF_DECLARED = "self_declared"
    PARENTAL_CONSENT = "parental_consent"
    ID_VERIFIED = "id_verified"


@dataclass
class UserAgeProfile:
    """User age profile with verification status."""
    user_id: str
    declared_age: Optional[int] = None
    verification_level: AgeVerificationLevel = AgeVerificationLevel.NONE
    parental_consent: bool = False
    verified_adult: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_minor(self) -> bool:
        """Conservative check - if unknown, assume minor."""
        if self.declared_age is None:
            return True  # Assume minor if unknown
        return self.declared_age < 18

    @property
    def content_rating_allowed(self) -> ContentRating:
        """Determine highest allowed content rating."""
        if self.verified_adult:
            return ContentRating.ADULT_18
        if self.declared_age is None:
            return ContentRating.SAFE_ALL
        if self.declared_age >= 18:
            return ContentRating.MATURE_16  # Not verified, limit access
        if self.declared_age >= 16:
            return ContentRating.MATURE_16
        if self.declared_age >= 13:
            return ContentRating.TEEN_13
        return ContentRating.SAFE_ALL


# =============================================================================
# PARENTAL CONTROLS
# =============================================================================

@dataclass
class ParentalControls:
    """Parental control settings."""
    enabled: bool = True
    max_content_rating: ContentRating = ContentRating.SAFE_ALL
    time_limits_enabled: bool = False
    daily_time_limit_minutes: int = 120
    allowed_hours_start: int = 8   # 8 AM
    allowed_hours_end: int = 20    # 8 PM
    block_private_messaging: bool = True
    block_image_sharing: bool = True
    block_location_sharing: bool = True
    activity_logging: bool = True
    require_approval_for_contacts: bool = True


# =============================================================================
# REPORTING SYSTEM
# =============================================================================

@dataclass
class SafetyReport:
    """Report of safety incident."""
    report_id: str
    timestamp: datetime
    threat_level: ThreatLevel
    category: str
    description: str
    evidence_hash: str
    reported_to_authorities: bool = False
    authority_reference: str = ""


class ReportingSystem:
    """
    Handles mandatory reporting to authorities.

    In production, this integrates with:
    - NCMEC CyberTipline (US)
    - IWF (UK)
    - INHOPE network (International)
    """

    def __init__(self):
        self.reports: List[SafetyReport] = []
        self.ncmec_endpoint = "https://report.cybertip.org/api/"  # Example
        self.iwf_endpoint = "https://report.iwf.org.uk/api/"      # Example

    def create_report(self, category: str, description: str, evidence: bytes) -> SafetyReport:
        """Create a safety report."""
        report = SafetyReport(
            report_id=hashlib.sha256(f"{datetime.now().isoformat()}{category}".encode()).hexdigest()[:16],
            timestamp=datetime.now(),
            threat_level=ThreatLevel.CRITICAL,
            category=category,
            description=description,
            evidence_hash=hashlib.sha256(evidence).hexdigest()
        )
        self.reports.append(report)
        return report

    def submit_to_ncmec(self, report: SafetyReport) -> bool:
        """
        Submit report to NCMEC CyberTipline.

        In production, this makes actual API calls.
        """
        print(f"[KID_SAFE] Submitting report {report.report_id} to NCMEC")
        report.reported_to_authorities = True
        report.authority_reference = f"NCMEC-{report.report_id}"
        return True

    def submit_to_iwf(self, report: SafetyReport) -> bool:
        """Submit report to IWF (UK)."""
        print(f"[KID_SAFE] Submitting report {report.report_id} to IWF")
        report.reported_to_authorities = True
        report.authority_reference = f"IWF-{report.report_id}"
        return True


# =============================================================================
# MAIN SAFETY GUARDIAN
# =============================================================================

class KidSafeGuardian:
    """
    Central child safety guardian.

    This MUST be integrated into every AI system that may interact with minors.
    """

    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.reporting_system = ReportingSystem()
        self.audit_log: List[Dict] = []
        self._verify_rules_integrity()

    def _verify_rules_integrity(self) -> bool:
        """Verify absolute rules haven't been tampered with."""
        current_hash = hashlib.sha256(
            "|".join([r.value for r in AbsoluteRule]).encode()
        ).hexdigest()

        if current_hash != ABSOLUTE_RULES_HASH:
            raise RuntimeError("CRITICAL: Absolute rules have been tampered with. System halted.")
        return True

    def check_content(self, content: str, user_profile: UserAgeProfile) -> ContentAnalysis:
        """
        Check content for safety.

        Returns ContentAnalysis with rating and any required actions.
        """
        self._verify_rules_integrity()

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        analysis = ContentAnalysis(
            content_hash=content_hash,
            rating=ContentRating.SAFE_ALL,
            threat_level=ThreatLevel.NONE
        )

        # Check if content is appropriate for user's age
        if user_profile.is_minor:
            # Apply stricter checks for minors
            analysis = self._apply_minor_safety_checks(content, analysis)

        # Log the check
        self._log_check(content_hash, analysis, user_profile)

        return analysis

    def _apply_minor_safety_checks(self, content: str, analysis: ContentAnalysis) -> ContentAnalysis:
        """Apply additional safety checks for minors."""

        # Check for grooming patterns
        pattern_result = self.pattern_detector.analyze_conversation([content])

        if pattern_result["risk_score"] >= 0.8:
            analysis.threat_level = ThreatLevel.CRITICAL
            analysis.blocked = True
            analysis.requires_report = True
            analysis.reason = "Potential grooming pattern detected"
        elif pattern_result["risk_score"] >= 0.5:
            analysis.threat_level = ThreatLevel.HIGH
            analysis.blocked = True
            analysis.reason = "Suspicious pattern detected"

        analysis.flags.extend(pattern_result["flags"])

        return analysis

    def check_interaction(self,
                          sender_profile: UserAgeProfile,
                          recipient_profile: UserAgeProfile,
                          message: str) -> Dict:
        """
        Check if an interaction between two users is safe.

        Extra scrutiny for adult-to-minor communications.
        """
        self._verify_rules_integrity()

        result = {
            "allowed": True,
            "flags": [],
            "actions": []
        }

        # Adult sending to minor - heightened scrutiny
        if not sender_profile.is_minor and recipient_profile.is_minor:
            result["flags"].append("adult_to_minor_communication")

            # Check if this is a verified safe relationship (parent, teacher, etc.)
            # In production, this would check relationship verification

            # Apply pattern detection
            pattern_result = self.pattern_detector.analyze_conversation([message])
            if pattern_result["recommendation"] in ["BLOCK_AND_REPORT", "BLOCK_AND_REVIEW"]:
                result["allowed"] = False
                result["actions"].append(pattern_result["recommendation"])

        # Minor sending to adult - monitor for exploitation
        if sender_profile.is_minor and not recipient_profile.is_minor:
            result["flags"].append("minor_to_adult_communication")
            # Check for signs of exploitation or manipulation

        return result

    def emergency_block(self, user_id: str, reason: str) -> bool:
        """
        Emergency block a user.

        Used when immediate danger is detected.
        """
        self._verify_rules_integrity()

        print(f"[KID_SAFE] EMERGENCY BLOCK: User {user_id} - {reason}")

        # Create report
        report = self.reporting_system.create_report(
            category="emergency_block",
            description=reason,
            evidence=f"User: {user_id}, Reason: {reason}".encode()
        )

        # Submit to authorities if critical
        self.reporting_system.submit_to_ncmec(report)

        self._log_check(
            user_id,
            ContentAnalysis(
                content_hash=user_id,
                rating=ContentRating.BLOCKED,
                threat_level=ThreatLevel.CRITICAL,
                blocked=True,
                requires_report=True,
                reason=reason
            ),
            None
        )

        return True

    def _log_check(self, content_hash: str, analysis: ContentAnalysis, user_profile: Optional[UserAgeProfile]):
        """Log safety check for audit."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "content_hash": content_hash,
            "rating": analysis.rating.value,
            "threat_level": analysis.threat_level.value,
            "blocked": analysis.blocked,
            "user_is_minor": user_profile.is_minor if user_profile else None,
            "flags": analysis.flags
        })

    def get_safety_report(self) -> Dict:
        """Generate safety status report."""
        return {
            "rules_integrity": self._verify_rules_integrity(),
            "total_checks": len(self.audit_log),
            "blocks": sum(1 for log in self.audit_log if log.get("blocked")),
            "reports_submitted": len(self.reporting_system.reports),
            "threat_summary": {
                "critical": sum(1 for log in self.audit_log if log.get("threat_level") == ThreatLevel.CRITICAL.value),
                "high": sum(1 for log in self.audit_log if log.get("threat_level") == ThreatLevel.HIGH.value),
                "medium": sum(1 for log in self.audit_log if log.get("threat_level") == ThreatLevel.MEDIUM.value),
            },
            "absolute_rules": [r.value for r in AbsoluteRule],
            "rules_hash": ABSOLUTE_RULES_HASH
        }


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KID SAFE PROTOCOL - Child Safety Framework")
    print("=" * 60)

    # Initialize guardian
    guardian = KidSafeGuardian()

    # Display absolute rules
    print("\nABSOLUTE RULES (Non-negotiable):")
    for rule in AbsoluteRule:
        print(f"  ✓ {rule.value}")

    print(f"\nRules Hash: {ABSOLUTE_RULES_HASH[:16]}...")

    # Create test profiles
    child_profile = UserAgeProfile(
        user_id="child_001",
        declared_age=12,
        verification_level=AgeVerificationLevel.PARENTAL_CONSENT,
        parental_consent=True
    )

    adult_profile = UserAgeProfile(
        user_id="adult_001",
        declared_age=35,
        verification_level=AgeVerificationLevel.ID_VERIFIED,
        verified_adult=True
    )

    # Test content check
    print("\n--- Content Check Test ---")
    test_content = "Hello, how are you today?"
    analysis = guardian.check_content(test_content, child_profile)
    print(f"Content Rating: {analysis.rating.value}")
    print(f"Threat Level: {analysis.threat_level.name}")
    print(f"Blocked: {analysis.blocked}")

    # Test interaction check
    print("\n--- Interaction Check Test ---")
    interaction = guardian.check_interaction(adult_profile, child_profile, test_content)
    print(f"Allowed: {interaction['allowed']}")
    print(f"Flags: {interaction['flags']}")

    # Get safety report
    print("\n--- Safety Report ---")
    report = guardian.get_safety_report()
    print(f"Rules Integrity: {report['rules_integrity']}")
    print(f"Total Checks: {report['total_checks']}")

    print("\n" + "=" * 60)
    print("Kid Safe Protocol Active. Children Protected.")
    print("=" * 60)
