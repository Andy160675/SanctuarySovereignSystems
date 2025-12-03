# =============================================================================
# DUAL-MODEL CROSS-CHECK GATE
# =============================================================================
# Purpose: Cognitive risk reduction via dissimilar model verification
# Target: Move raw reasoning from 8.5 → 9.2 without adding autonomy risk
#
# Applied to high-stakes lanes:
#   - Regulatory interpretation
#   - Financial risk math
#   - Clinical/medico-legal reasoning
#
# Rejection criteria:
#   - Material conclusion differs between models
#   - Citation overlap below threshold
# =============================================================================

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class ReasoningLane(Enum):
    """High-stakes reasoning lanes requiring cross-check."""
    REGULATORY = "regulatory"
    FINANCIAL = "financial"
    CLINICAL = "clinical"
    LEGAL = "legal"
    GENERAL = "general"  # No cross-check required


class CrossCheckVerdict(Enum):
    """Result of cross-model verification."""
    ALIGNED = "aligned"           # Models agree, safe to proceed
    DIVERGENT = "divergent"       # Material disagreement, reject
    INSUFFICIENT = "insufficient"  # Not enough evidence to compare
    BYPASSED = "bypassed"         # Lane doesn't require cross-check


@dataclass
class ModelResponse:
    """Response from a single model."""
    model_id: str
    conclusion: str
    confidence: float
    citations: List[str]
    reasoning_chain: List[str]
    raw_output: str
    latency_ms: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class CrossCheckResult:
    """Result of cross-model verification."""
    verdict: CrossCheckVerdict
    primary: ModelResponse
    secondary: Optional[ModelResponse]
    conclusion_similarity: float
    citation_overlap: float
    disagreement_details: List[str]
    recommendation: str
    trace_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return {
            "verdict": self.verdict.value,
            "conclusion_similarity": self.conclusion_similarity,
            "citation_overlap": self.citation_overlap,
            "disagreement_details": self.disagreement_details,
            "recommendation": self.recommendation,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "primary_model": self.primary.model_id,
            "secondary_model": self.secondary.model_id if self.secondary else None,
        }


# =============================================================================
# MODEL ADAPTER INTERFACE
# =============================================================================

class ModelAdapter(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def query(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        """Query the model and return structured response."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return model identifier."""
        pass


class OllamaAdapter(ModelAdapter):
    """Adapter for local Ollama models."""

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self._model_name = model_name
        self._base_url = base_url

    @property
    def model_id(self) -> str:
        return f"ollama:{self._model_name}"

    def query(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        """Query Ollama model."""
        import time
        start = time.time()

        try:
            import requests
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model_name,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            raw_output = data.get("response", "")
        except Exception as e:
            raw_output = f"[ERROR] {str(e)}"

        latency = (time.time() - start) * 1000

        # Parse structured output
        conclusion, citations, reasoning = self._parse_output(raw_output)

        return ModelResponse(
            model_id=self.model_id,
            conclusion=conclusion,
            confidence=self._estimate_confidence(raw_output),
            citations=citations,
            reasoning_chain=reasoning,
            raw_output=raw_output,
            latency_ms=latency,
        )

    def _parse_output(self, output: str) -> Tuple[str, List[str], List[str]]:
        """Parse model output into structured components."""
        # Simple extraction - in production, use structured output formats
        lines = output.strip().split("\n")
        conclusion = lines[0] if lines else ""
        citations = [l for l in lines if l.startswith("[") or "§" in l or "Art." in l]
        reasoning = [l for l in lines if l and not l.startswith("[")]
        return conclusion, citations, reasoning

    def _estimate_confidence(self, output: str) -> float:
        """Estimate confidence from output hedging language."""
        hedges = ["may", "might", "possibly", "uncertain", "unclear", "perhaps"]
        output_lower = output.lower()
        hedge_count = sum(1 for h in hedges if h in output_lower)
        return max(0.5, 1.0 - (hedge_count * 0.1))


class MockAdapter(ModelAdapter):
    """Mock adapter for testing."""

    def __init__(self, model_id: str, responses: Dict[str, str] = None):
        self._model_id = model_id
        self._responses = responses or {}

    @property
    def model_id(self) -> str:
        return self._model_id

    def query(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        # Return canned response or generate mock
        raw = self._responses.get(prompt, f"Mock response for: {prompt[:50]}...")
        return ModelResponse(
            model_id=self._model_id,
            conclusion=raw.split(".")[0] if raw else "No conclusion",
            confidence=0.85,
            citations=["[Mock Citation 1]", "[Mock Citation 2]"],
            reasoning_chain=["Step 1", "Step 2"],
            raw_output=raw,
            latency_ms=100.0,
        )


# =============================================================================
# CROSS-MODEL GATE
# =============================================================================

class CrossModelGate:
    """
    Dual-model cross-check gate for high-stakes reasoning.

    Usage:
        gate = CrossModelGate(
            primary=OllamaAdapter("llama3:8b"),
            secondary=OllamaAdapter("mistral:7b"),
        )
        result = gate.verify("What are the FCA requirements for...", lane=ReasoningLane.REGULATORY)
        if result.verdict == CrossCheckVerdict.ALIGNED:
            # Safe to use primary conclusion
        else:
            # Reject or escalate
    """

    # Lanes requiring cross-check
    CROSS_CHECK_LANES = {
        ReasoningLane.REGULATORY,
        ReasoningLane.FINANCIAL,
        ReasoningLane.CLINICAL,
        ReasoningLane.LEGAL,
    }

    # Thresholds
    CONCLUSION_SIMILARITY_THRESHOLD = 0.7
    CITATION_OVERLAP_THRESHOLD = 0.5

    def __init__(
        self,
        primary: ModelAdapter,
        secondary: ModelAdapter,
        similarity_threshold: float = None,
        citation_threshold: float = None,
    ):
        self.primary = primary
        self.secondary = secondary
        self.similarity_threshold = similarity_threshold or self.CONCLUSION_SIMILARITY_THRESHOLD
        self.citation_threshold = citation_threshold or self.CITATION_OVERLAP_THRESHOLD

    def verify(
        self,
        prompt: str,
        lane: ReasoningLane,
        context: Dict[str, Any] = None,
    ) -> CrossCheckResult:
        """
        Run cross-model verification.

        Args:
            prompt: The reasoning prompt
            lane: The reasoning lane (determines if cross-check required)
            context: Additional context for the models

        Returns:
            CrossCheckResult with verdict and details
        """
        context = context or {}
        trace_id = self._generate_trace_id(prompt)

        # Check if lane requires cross-check
        if lane not in self.CROSS_CHECK_LANES:
            primary_response = self.primary.query(prompt, context)
            return CrossCheckResult(
                verdict=CrossCheckVerdict.BYPASSED,
                primary=primary_response,
                secondary=None,
                conclusion_similarity=1.0,
                citation_overlap=1.0,
                disagreement_details=[],
                recommendation="Lane does not require cross-check",
                trace_id=trace_id,
            )

        # Query both models
        primary_response = self.primary.query(prompt, context)
        secondary_response = self.secondary.query(prompt, context)

        # Compare conclusions
        similarity = self._compute_similarity(
            primary_response.conclusion,
            secondary_response.conclusion,
        )

        # Compare citations
        citation_overlap = self._compute_citation_overlap(
            primary_response.citations,
            secondary_response.citations,
        )

        # Determine verdict
        disagreements = []
        if similarity < self.similarity_threshold:
            disagreements.append(
                f"Conclusion similarity {similarity:.2f} below threshold {self.similarity_threshold}"
            )
        if citation_overlap < self.citation_threshold:
            disagreements.append(
                f"Citation overlap {citation_overlap:.2f} below threshold {self.citation_threshold}"
            )

        if disagreements:
            verdict = CrossCheckVerdict.DIVERGENT
            recommendation = "REJECT: Material disagreement between models. Escalate to human review."
        else:
            verdict = CrossCheckVerdict.ALIGNED
            recommendation = "ACCEPT: Models aligned. Safe to proceed with primary conclusion."

        return CrossCheckResult(
            verdict=verdict,
            primary=primary_response,
            secondary=secondary_response,
            conclusion_similarity=similarity,
            citation_overlap=citation_overlap,
            disagreement_details=disagreements,
            recommendation=recommendation,
            trace_id=trace_id,
        )

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts."""
        # Simple word overlap for now - replace with embedding similarity in production
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _compute_citation_overlap(self, cites1: List[str], cites2: List[str]) -> float:
        """Compute overlap between citation lists."""
        if not cites1 and not cites2:
            return 1.0  # Both empty = agreement
        if not cites1 or not cites2:
            return 0.0  # One empty = disagreement

        # Normalize citations for comparison
        norm1 = {self._normalize_citation(c) for c in cites1}
        norm2 = {self._normalize_citation(c) for c in cites2}

        intersection = norm1 & norm2
        union = norm1 | norm2

        return len(intersection) / len(union) if union else 0.0

    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison."""
        # Remove whitespace, lowercase, extract key identifiers
        import re
        normalized = citation.lower().strip()
        # Extract article/section numbers
        numbers = re.findall(r'\d+', normalized)
        return "".join(numbers) if numbers else normalized[:20]

    def _generate_trace_id(self, prompt: str) -> str:
        """Generate unique trace ID for this verification."""
        content = f"{datetime.utcnow().isoformat()}{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# =============================================================================
# LANE DETECTOR
# =============================================================================

class LaneDetector:
    """Detect reasoning lane from prompt content."""

    LANE_KEYWORDS = {
        ReasoningLane.REGULATORY: [
            "fca", "regulation", "compliance", "regulatory", "rule", "guideline",
            "mifid", "gdpr", "basel", "solvency", "directive", "act"
        ],
        ReasoningLane.FINANCIAL: [
            "financial", "risk", "capital", "exposure", "var", "stress test",
            "portfolio", "derivative", "hedge", "valuation", "npv", "irr"
        ],
        ReasoningLane.CLINICAL: [
            "clinical", "patient", "diagnosis", "treatment", "medical",
            "nice", "mhra", "drug", "therapy", "symptom", "condition"
        ],
        ReasoningLane.LEGAL: [
            "legal", "contract", "liability", "tort", "statute", "court",
            "precedent", "jurisdiction", "plaintiff", "defendant"
        ],
    }

    @classmethod
    def detect(cls, prompt: str) -> ReasoningLane:
        """Detect the reasoning lane from prompt content."""
        prompt_lower = prompt.lower()

        scores = {}
        for lane, keywords in cls.LANE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            scores[lane] = score

        # Return highest scoring lane, or GENERAL if no matches
        if max(scores.values()) == 0:
            return ReasoningLane.GENERAL

        return max(scores, key=scores.get)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def cross_check(
    prompt: str,
    primary_model: str = "llama3:8b",
    secondary_model: str = "mistral:7b",
    lane: ReasoningLane = None,
) -> CrossCheckResult:
    """
    Convenience function for cross-model verification.

    Args:
        prompt: The reasoning prompt
        primary_model: Primary Ollama model name
        secondary_model: Secondary Ollama model name
        lane: Reasoning lane (auto-detected if None)

    Returns:
        CrossCheckResult
    """
    # Auto-detect lane if not provided
    if lane is None:
        lane = LaneDetector.detect(prompt)

    gate = CrossModelGate(
        primary=OllamaAdapter(primary_model),
        secondary=OllamaAdapter(secondary_model),
    )

    return gate.verify(prompt, lane)


# =============================================================================
# MAIN (TESTING)
# =============================================================================

if __name__ == "__main__":
    # Test with mock adapters
    print("=== Cross-Model Gate Test ===\n")

    gate = CrossModelGate(
        primary=MockAdapter("mock-primary", {
            "test": "The FCA requires firms to maintain adequate capital. [FCA SYSC 4.1]"
        }),
        secondary=MockAdapter("mock-secondary", {
            "test": "Firms must hold sufficient capital per FCA rules. [FCA SYSC 4.1]"
        }),
    )

    # Test regulatory lane (requires cross-check)
    result = gate.verify(
        "test",
        lane=ReasoningLane.REGULATORY,
    )

    print(f"Lane: REGULATORY")
    print(f"Verdict: {result.verdict.value}")
    print(f"Similarity: {result.conclusion_similarity:.2f}")
    print(f"Citation Overlap: {result.citation_overlap:.2f}")
    print(f"Recommendation: {result.recommendation}")
    print()

    # Test general lane (bypass)
    result2 = gate.verify(
        "What is the weather?",
        lane=ReasoningLane.GENERAL,
    )

    print(f"Lane: GENERAL")
    print(f"Verdict: {result2.verdict.value}")
    print(f"Recommendation: {result2.recommendation}")
