# =============================================================================
# NO-ANSWER GATE
# =============================================================================
# Purpose: Prevent speculative answers when evidence is insufficient
#
# Key Rule:
#   If evidence density < threshold OR Confessor disagreement unresolved
#   System MUST return "Insufficient anchored evidence"
#   NEVER a speculative answer
#
# This alone removes most tail-risk hallucination exposure.
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import re


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class EvidenceQuality(Enum):
    """Quality assessment of evidence."""
    AUTHORITATIVE = "authoritative"  # Primary source, verified
    CORROBORATED = "corroborated"    # Multiple sources agree
    SINGLE_SOURCE = "single_source"  # One source only
    INFERRED = "inferred"            # Derived from other evidence
    SPECULATIVE = "speculative"      # Guess or assumption
    NONE = "none"                    # No evidence


class AnswerVerdict(Enum):
    """Verdict on whether an answer can be given."""
    PROCEED = "proceed"              # Sufficient evidence, answer allowed
    INSUFFICIENT = "insufficient"    # Not enough evidence, must decline
    CONFLICT = "conflict"            # Evidence conflicts, escalate
    SPECULATIVE = "speculative"      # Would require speculation, decline


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Evidence:
    """A piece of evidence supporting an answer."""
    source: str
    content: str
    quality: EvidenceQuality
    confidence: float
    citation: Optional[str] = None
    timestamp: Optional[str] = None
    corroborating_sources: List[str] = field(default_factory=list)


@dataclass
class EvidenceAssessment:
    """Assessment of evidence supporting an answer."""
    total_pieces: int
    authoritative_count: int
    corroborated_count: int
    single_source_count: int
    speculative_count: int
    density_score: float  # 0.0 to 1.0
    conflicts: List[str]
    gaps: List[str]
    meets_threshold: bool


@dataclass
class NoAnswerResult:
    """Result of no-answer gate evaluation."""
    verdict: AnswerVerdict
    can_answer: bool
    reason: str
    evidence_assessment: EvidenceAssessment
    recommended_response: str
    escalation_needed: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return {
            "verdict": self.verdict.value,
            "can_answer": self.can_answer,
            "reason": self.reason,
            "density_score": self.evidence_assessment.density_score,
            "meets_threshold": self.evidence_assessment.meets_threshold,
            "conflicts": self.evidence_assessment.conflicts,
            "gaps": self.evidence_assessment.gaps,
            "escalation_needed": self.escalation_needed,
            "timestamp": self.timestamp,
        }


# =============================================================================
# NO-ANSWER GATE
# =============================================================================

class NoAnswerGate:
    """
    Gate that prevents speculative answers.

    Usage:
        gate = NoAnswerGate(evidence_threshold=0.6)
        result = gate.evaluate(question, evidence_list)
        if result.can_answer:
            # Proceed with answer
        else:
            # Return result.recommended_response
    """

    # Response templates
    INSUFFICIENT_EVIDENCE_RESPONSE = (
        "I cannot provide a definitive answer to this question. "
        "The available evidence is insufficient to support a reliable conclusion. "
        "Specifically: {gaps}"
    )

    CONFLICTING_EVIDENCE_RESPONSE = (
        "I cannot provide a definitive answer due to conflicting evidence. "
        "The following conflicts need resolution: {conflicts}"
    )

    SPECULATIVE_RESPONSE = (
        "Answering this question would require speculation beyond the available evidence. "
        "I can only provide answers grounded in verified information."
    )

    def __init__(
        self,
        evidence_threshold: float = 0.6,
        min_authoritative_sources: int = 1,
        max_speculative_ratio: float = 0.2,
        require_corroboration_for_high_stakes: bool = True,
    ):
        """
        Initialize the no-answer gate.

        Args:
            evidence_threshold: Minimum density score to proceed (0.0-1.0)
            min_authoritative_sources: Minimum authoritative sources required
            max_speculative_ratio: Maximum ratio of speculative evidence allowed
            require_corroboration_for_high_stakes: Require corroboration for important questions
        """
        self.evidence_threshold = evidence_threshold
        self.min_authoritative_sources = min_authoritative_sources
        self.max_speculative_ratio = max_speculative_ratio
        self.require_corroboration = require_corroboration_for_high_stakes

    def evaluate(
        self,
        question: str,
        evidence: List[Evidence],
        confessor_assessment: Optional[Dict] = None,
    ) -> NoAnswerResult:
        """
        Evaluate whether an answer can be given.

        Args:
            question: The question being answered
            evidence: List of evidence pieces
            confessor_assessment: Optional Confessor risk assessment

        Returns:
            NoAnswerResult with verdict and recommended response
        """
        # Assess evidence
        assessment = self._assess_evidence(evidence)

        # Check for Confessor disagreement
        confessor_conflict = self._check_confessor_conflict(confessor_assessment)

        # Determine if question is high-stakes
        is_high_stakes = self._is_high_stakes_question(question)

        # Make verdict
        verdict, reason = self._make_verdict(
            assessment,
            confessor_conflict,
            is_high_stakes,
        )

        # Generate recommended response
        recommended = self._generate_response(verdict, assessment)

        return NoAnswerResult(
            verdict=verdict,
            can_answer=(verdict == AnswerVerdict.PROCEED),
            reason=reason,
            evidence_assessment=assessment,
            recommended_response=recommended,
            escalation_needed=(verdict in {AnswerVerdict.CONFLICT, AnswerVerdict.INSUFFICIENT}),
        )

    def _assess_evidence(self, evidence: List[Evidence]) -> EvidenceAssessment:
        """Assess the quality and density of evidence."""
        if not evidence:
            return EvidenceAssessment(
                total_pieces=0,
                authoritative_count=0,
                corroborated_count=0,
                single_source_count=0,
                speculative_count=0,
                density_score=0.0,
                conflicts=[],
                gaps=["No evidence provided"],
                meets_threshold=False,
            )

        # Count by quality
        authoritative = sum(1 for e in evidence if e.quality == EvidenceQuality.AUTHORITATIVE)
        corroborated = sum(1 for e in evidence if e.quality == EvidenceQuality.CORROBORATED)
        single_source = sum(1 for e in evidence if e.quality == EvidenceQuality.SINGLE_SOURCE)
        speculative = sum(1 for e in evidence if e.quality == EvidenceQuality.SPECULATIVE)

        # Calculate density score
        # Weighted: authoritative=1.0, corroborated=0.8, single=0.5, speculative=0.1
        weights = {
            EvidenceQuality.AUTHORITATIVE: 1.0,
            EvidenceQuality.CORROBORATED: 0.8,
            EvidenceQuality.SINGLE_SOURCE: 0.5,
            EvidenceQuality.INFERRED: 0.3,
            EvidenceQuality.SPECULATIVE: 0.1,
            EvidenceQuality.NONE: 0.0,
        }

        total_weight = sum(weights.get(e.quality, 0) * e.confidence for e in evidence)
        max_possible = len(evidence) * 1.0  # If all authoritative with confidence 1.0
        density_score = total_weight / max_possible if max_possible > 0 else 0.0

        # Detect conflicts
        conflicts = self._detect_conflicts(evidence)

        # Detect gaps
        gaps = self._detect_gaps(evidence)

        # Check threshold
        meets_threshold = (
            density_score >= self.evidence_threshold
            and authoritative >= self.min_authoritative_sources
            and (speculative / len(evidence) if evidence else 0) <= self.max_speculative_ratio
            and len(conflicts) == 0
        )

        return EvidenceAssessment(
            total_pieces=len(evidence),
            authoritative_count=authoritative,
            corroborated_count=corroborated,
            single_source_count=single_source,
            speculative_count=speculative,
            density_score=density_score,
            conflicts=conflicts,
            gaps=gaps,
            meets_threshold=meets_threshold,
        )

    def _detect_conflicts(self, evidence: List[Evidence]) -> List[str]:
        """Detect conflicting evidence."""
        conflicts = []

        # Simple heuristic: check for contradictory keywords
        contradiction_pairs = [
            ("increase", "decrease"),
            ("approve", "reject"),
            ("allow", "prohibit"),
            ("required", "optional"),
            ("must", "may not"),
            ("compliant", "non-compliant"),
        ]

        contents = [e.content.lower() for e in evidence]
        all_content = " ".join(contents)

        for word1, word2 in contradiction_pairs:
            if word1 in all_content and word2 in all_content:
                conflicts.append(f"Evidence contains both '{word1}' and '{word2}'")

        return conflicts

    def _detect_gaps(self, evidence: List[Evidence]) -> List[str]:
        """Detect evidence gaps."""
        gaps = []

        if not evidence:
            gaps.append("No evidence provided")
            return gaps

        # Check for authoritative sources
        authoritative = [e for e in evidence if e.quality == EvidenceQuality.AUTHORITATIVE]
        if not authoritative:
            gaps.append("No authoritative sources")

        # Check for recent evidence
        recent = [e for e in evidence if e.timestamp and "2024" in e.timestamp]
        if not recent and any(e.timestamp for e in evidence):
            gaps.append("No recent evidence (2024+)")

        # Check for citations
        uncited = [e for e in evidence if not e.citation]
        if len(uncited) == len(evidence):
            gaps.append("No citations provided")

        # Check confidence
        low_confidence = [e for e in evidence if e.confidence < 0.5]
        if len(low_confidence) > len(evidence) / 2:
            gaps.append("Majority of evidence has low confidence")

        return gaps

    def _check_confessor_conflict(self, assessment: Optional[Dict]) -> bool:
        """Check if Confessor flagged unresolved conflict."""
        if not assessment:
            return False

        return assessment.get("unresolved_conflict", False)

    def _is_high_stakes_question(self, question: str) -> bool:
        """Determine if question is high-stakes."""
        high_stakes_indicators = [
            "regulatory", "compliance", "legal", "liability",
            "financial", "risk", "medical", "clinical",
            "must", "required", "mandatory", "prohibited",
            "penalty", "fine", "lawsuit", "audit",
        ]

        question_lower = question.lower()
        return any(indicator in question_lower for indicator in high_stakes_indicators)

    def _make_verdict(
        self,
        assessment: EvidenceAssessment,
        confessor_conflict: bool,
        is_high_stakes: bool,
    ) -> Tuple[AnswerVerdict, str]:
        """Make the verdict decision."""

        # Confessor conflict = always escalate
        if confessor_conflict:
            return (
                AnswerVerdict.CONFLICT,
                "Confessor flagged unresolved conflict"
            )

        # Evidence conflicts = cannot answer
        if assessment.conflicts:
            return (
                AnswerVerdict.CONFLICT,
                f"Evidence conflicts detected: {assessment.conflicts[0]}"
            )

        # Below threshold = insufficient
        if not assessment.meets_threshold:
            reasons = []
            if assessment.density_score < self.evidence_threshold:
                reasons.append(f"density {assessment.density_score:.2f} < {self.evidence_threshold}")
            if assessment.authoritative_count < self.min_authoritative_sources:
                reasons.append(f"only {assessment.authoritative_count} authoritative sources")
            if assessment.speculative_count / max(assessment.total_pieces, 1) > self.max_speculative_ratio:
                reasons.append("too much speculative evidence")

            return (
                AnswerVerdict.INSUFFICIENT,
                f"Insufficient evidence: {', '.join(reasons)}"
            )

        # High-stakes without corroboration = insufficient
        if is_high_stakes and self.require_corroboration:
            if assessment.corroborated_count == 0 and assessment.authoritative_count < 2:
                return (
                    AnswerVerdict.INSUFFICIENT,
                    "High-stakes question requires corroborated evidence"
                )

        # All checks passed
        return (
            AnswerVerdict.PROCEED,
            "Evidence sufficient to proceed"
        )

    def _generate_response(
        self,
        verdict: AnswerVerdict,
        assessment: EvidenceAssessment,
    ) -> str:
        """Generate the recommended response."""

        if verdict == AnswerVerdict.PROCEED:
            return ""  # No special response needed

        if verdict == AnswerVerdict.CONFLICT:
            return self.CONFLICTING_EVIDENCE_RESPONSE.format(
                conflicts="; ".join(assessment.conflicts) or "Unresolved Confessor disagreement"
            )

        if verdict == AnswerVerdict.INSUFFICIENT:
            return self.INSUFFICIENT_EVIDENCE_RESPONSE.format(
                gaps="; ".join(assessment.gaps) or "Evidence below quality threshold"
            )

        if verdict == AnswerVerdict.SPECULATIVE:
            return self.SPECULATIVE_RESPONSE

        return "Unable to provide a reliable answer."


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def check_can_answer(
    question: str,
    evidence: List[Dict[str, Any]],
    threshold: float = 0.6,
) -> NoAnswerResult:
    """
    Convenience function to check if a question can be answered.

    Args:
        question: The question being answered
        evidence: List of evidence dicts with keys: source, content, quality, confidence
        threshold: Evidence density threshold

    Returns:
        NoAnswerResult
    """
    # Convert dicts to Evidence objects
    evidence_objects = []
    for e in evidence:
        quality = EvidenceQuality(e.get("quality", "single_source"))
        evidence_objects.append(Evidence(
            source=e.get("source", "unknown"),
            content=e.get("content", ""),
            quality=quality,
            confidence=e.get("confidence", 0.5),
            citation=e.get("citation"),
            timestamp=e.get("timestamp"),
        ))

    gate = NoAnswerGate(evidence_threshold=threshold)
    return gate.evaluate(question, evidence_objects)


# =============================================================================
# MAIN (TESTING)
# =============================================================================

if __name__ == "__main__":
    print("=== No-Answer Gate Test ===\n")

    gate = NoAnswerGate(evidence_threshold=0.6)

    # Test 1: Sufficient evidence
    print("Test 1: Sufficient evidence")
    evidence1 = [
        Evidence(
            source="FCA Handbook",
            content="Firms must maintain capital ratios of at least 8%",
            quality=EvidenceQuality.AUTHORITATIVE,
            confidence=0.95,
            citation="FCA SYSC 4.1",
        ),
        Evidence(
            source="Internal Policy",
            content="Capital requirements align with FCA guidance",
            quality=EvidenceQuality.CORROBORATED,
            confidence=0.85,
        ),
    ]
    result1 = gate.evaluate("What are the capital requirements?", evidence1)
    print(f"  Verdict: {result1.verdict.value}")
    print(f"  Can answer: {result1.can_answer}")
    print(f"  Density: {result1.evidence_assessment.density_score:.2f}")
    print()

    # Test 2: Insufficient evidence
    print("Test 2: Insufficient evidence")
    evidence2 = [
        Evidence(
            source="Hearsay",
            content="I heard the rate might be around 5%",
            quality=EvidenceQuality.SPECULATIVE,
            confidence=0.3,
        ),
    ]
    result2 = gate.evaluate("What is the exact interest rate?", evidence2)
    print(f"  Verdict: {result2.verdict.value}")
    print(f"  Can answer: {result2.can_answer}")
    print(f"  Reason: {result2.reason}")
    print(f"  Response: {result2.recommended_response[:80]}...")
    print()

    # Test 3: Conflicting evidence
    print("Test 3: Conflicting evidence")
    evidence3 = [
        Evidence(
            source="Report A",
            content="The transaction was approved by compliance",
            quality=EvidenceQuality.SINGLE_SOURCE,
            confidence=0.7,
        ),
        Evidence(
            source="Report B",
            content="Compliance rejected the transaction",
            quality=EvidenceQuality.SINGLE_SOURCE,
            confidence=0.7,
        ),
    ]
    result3 = gate.evaluate("Was the transaction approved?", evidence3)
    print(f"  Verdict: {result3.verdict.value}")
    print(f"  Can answer: {result3.can_answer}")
    print(f"  Conflicts: {result3.evidence_assessment.conflicts}")
