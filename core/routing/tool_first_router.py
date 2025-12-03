# =============================================================================
# TOOL-FIRST ROUTER
# =============================================================================
# Purpose: Route queries to deterministic tools BEFORE LLM speculation
#
# Key Principle:
#   Math queries → Calculator/Solver (NOT LLM arithmetic)
#   Law queries → Rules DB (NOT LLM hallucination)
#   Date queries → System clock (NOT LLM guess)
#   Lookup queries → Database (NOT LLM memory)
#
# LLM only handles synthesis AFTER tool results are anchored.
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Pattern
import re


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class ToolType(Enum):
    """Types of deterministic tools available."""
    CALCULATOR = "calculator"
    DATE_TIME = "date_time"
    RULES_DATABASE = "rules_database"
    ENTITY_LOOKUP = "entity_lookup"
    DOCUMENT_SEARCH = "document_search"
    REGULATION_LOOKUP = "regulation_lookup"
    RATE_LOOKUP = "rate_lookup"
    CONVERSION = "conversion"
    VALIDATION = "validation"
    LLM_SYNTHESIS = "llm_synthesis"  # Fallback only


class RoutingConfidence(Enum):
    """Confidence in routing decision."""
    DEFINITE = "definite"      # Pattern match is unambiguous
    LIKELY = "likely"          # High probability but not certain
    POSSIBLE = "possible"      # Could go either way
    FALLBACK = "fallback"      # No pattern match, use LLM


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RoutingDecision:
    """Result of routing decision."""
    tool_type: ToolType
    confidence: RoutingConfidence
    matched_patterns: List[str]
    extracted_params: Dict[str, Any]
    reasoning: str
    requires_llm_post_process: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return {
            "tool_type": self.tool_type.value,
            "confidence": self.confidence.value,
            "matched_patterns": self.matched_patterns,
            "extracted_params": self.extracted_params,
            "reasoning": self.reasoning,
            "requires_llm_post_process": self.requires_llm_post_process,
            "timestamp": self.timestamp,
        }


@dataclass
class ToolResult:
    """Result from a deterministic tool."""
    tool_type: ToolType
    success: bool
    result: Any
    source: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PATTERN DEFINITIONS
# =============================================================================

# Math/Calculator patterns
MATH_PATTERNS = [
    r'\b(\d+[\+\-\*\/\^]\d+)\b',                    # Basic arithmetic: 5+3
    r'\b(calculate|compute|sum|total|add|subtract|multiply|divide)\b',
    r'\bwhat\s+is\s+\d+\s*[\+\-\*\/]\s*\d+\b',     # "what is 5 + 3"
    r'\b(percentage|percent|%)\s+of\b',
    r'\b(average|mean|median|mode|std|variance)\b',
    r'\b(compound|simple)\s+interest\b',
    r'\b(amortization|annuity|npv|irr)\b',
]

# Date/Time patterns
DATE_PATTERNS = [
    r'\b(today|tomorrow|yesterday|now|current\s+time)\b',
    r'\b(what\s+day|what\s+date|what\s+time)\b',
    r'\b(\d+)\s+(days?|weeks?|months?|years?)\s+(from|ago|before|after)\b',
    r'\b(deadline|due\s+date|expiry|expires?)\b',
    r'\b(business\s+days?|working\s+days?)\b',
]

# Rules/Regulation patterns
RULES_PATTERNS = [
    r'\b(FCA|PRA|SEC|ESMA|Basel|MiFID|GDPR|DORA)\b',
    r'\b(regulation|regulatory|compliance|requirement)\b',
    r'\b(SYSC|COBS|PRIN|SUP|ICOBS)\b',           # FCA handbook sections
    r'\b(article|section|clause|paragraph)\s+\d+',
    r'\b(capital\s+requirement|liquidity\s+ratio|leverage\s+ratio)\b',
    r'\b(must|shall|required\s+to|prohibited|forbidden)\b',
    r'\b(threshold|limit|ceiling|floor)\b',
]

# Entity/Lookup patterns
ENTITY_PATTERNS = [
    r'\b(LEI|ISIN|CUSIP|SEDOL|BIC|SWIFT)\b',
    r'\b(company|firm|entity|counterparty)\s+(named?|called?|known\s+as)\b',
    r'\b(registered|incorporated|headquartered)\s+in\b',
    r'\b(FRN|firm\s+reference\s+number)\s*:?\s*\d+',
]

# Rate/Conversion patterns
RATE_PATTERNS = [
    r'\b(SONIA|SOFR|EURIBOR|LIBOR|ESTR)\b',
    r'\b(exchange\s+rate|fx\s+rate|currency\s+rate)\b',
    r'\b(GBP|USD|EUR|JPY|CHF)\s*(to|\/)\s*(GBP|USD|EUR|JPY|CHF)\b',
    r'\b(convert|conversion)\s+\d+\s*(GBP|USD|EUR|JPY|CHF)\b',
]


# =============================================================================
# TOOL-FIRST ROUTER
# =============================================================================

class ToolFirstRouter:
    """
    Routes queries to deterministic tools before LLM.

    Usage:
        router = ToolFirstRouter()
        decision = router.route("What is 15% of 250?")
        if decision.tool_type != ToolType.LLM_SYNTHESIS:
            result = router.execute(decision)
            # Use result as grounded context for LLM
    """

    def __init__(
        self,
        tools: Optional[Dict[ToolType, Callable]] = None,
        strict_mode: bool = True,
    ):
        """
        Initialize router.

        Args:
            tools: Dict mapping ToolType to callable implementations
            strict_mode: If True, prefer tools over LLM even for ambiguous cases
        """
        self.tools = tools or {}
        self.strict_mode = strict_mode
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.patterns = {
            ToolType.CALCULATOR: [re.compile(p, re.IGNORECASE) for p in MATH_PATTERNS],
            ToolType.DATE_TIME: [re.compile(p, re.IGNORECASE) for p in DATE_PATTERNS],
            ToolType.RULES_DATABASE: [re.compile(p, re.IGNORECASE) for p in RULES_PATTERNS],
            ToolType.ENTITY_LOOKUP: [re.compile(p, re.IGNORECASE) for p in ENTITY_PATTERNS],
            ToolType.RATE_LOOKUP: [re.compile(p, re.IGNORECASE) for p in RATE_PATTERNS],
        }

    def route(self, query: str) -> RoutingDecision:
        """
        Determine which tool should handle this query.

        Args:
            query: The user's query string

        Returns:
            RoutingDecision indicating tool and confidence
        """
        matches: Dict[ToolType, List[str]] = {}
        extracted: Dict[str, Any] = {}

        # Check each tool type's patterns
        for tool_type, patterns in self.patterns.items():
            tool_matches = []
            for pattern in patterns:
                match = pattern.search(query)
                if match:
                    tool_matches.append(match.group())
                    # Extract numeric values for calculator
                    if tool_type == ToolType.CALCULATOR:
                        nums = re.findall(r'\d+\.?\d*', query)
                        if nums:
                            extracted["numbers"] = [float(n) for n in nums]
                    # Extract regulation references
                    if tool_type == ToolType.RULES_DATABASE:
                        reg_refs = re.findall(r'(FCA|PRA|SEC|ESMA)\s+\w+\s+\d+', query, re.IGNORECASE)
                        if reg_refs:
                            extracted["regulation_refs"] = reg_refs

            if tool_matches:
                matches[tool_type] = tool_matches

        # Determine best match
        if not matches:
            return RoutingDecision(
                tool_type=ToolType.LLM_SYNTHESIS,
                confidence=RoutingConfidence.FALLBACK,
                matched_patterns=[],
                extracted_params={},
                reasoning="No deterministic tool patterns matched",
                requires_llm_post_process=True,
            )

        # Score matches by count and specificity
        scores = {}
        for tool_type, tool_matches in matches.items():
            # More matches = higher score
            # Specific patterns (longer matches) score higher
            score = len(tool_matches) + sum(len(m) / 10 for m in tool_matches)
            scores[tool_type] = score

        best_tool = max(scores, key=scores.get)
        best_score = scores[best_tool]

        # Determine confidence
        if best_score >= 3:
            confidence = RoutingConfidence.DEFINITE
        elif best_score >= 1.5:
            confidence = RoutingConfidence.LIKELY
        else:
            confidence = RoutingConfidence.POSSIBLE

        # In strict mode, downgrade possible to likely
        if self.strict_mode and confidence == RoutingConfidence.POSSIBLE:
            confidence = RoutingConfidence.LIKELY

        return RoutingDecision(
            tool_type=best_tool,
            confidence=confidence,
            matched_patterns=matches[best_tool],
            extracted_params=extracted,
            reasoning=f"Matched {len(matches[best_tool])} patterns for {best_tool.value}",
            requires_llm_post_process=(confidence != RoutingConfidence.DEFINITE),
        )

    def execute(self, decision: RoutingDecision, query: str) -> ToolResult:
        """
        Execute the routed tool.

        Args:
            decision: The routing decision
            query: Original query for context

        Returns:
            ToolResult from the tool execution
        """
        tool_type = decision.tool_type

        if tool_type == ToolType.LLM_SYNTHESIS:
            return ToolResult(
                tool_type=tool_type,
                success=True,
                result=None,
                source="llm",
                confidence=0.0,
                metadata={"note": "Requires LLM processing"},
            )

        if tool_type not in self.tools:
            return ToolResult(
                tool_type=tool_type,
                success=False,
                result=None,
                source="router",
                confidence=0.0,
                metadata={"error": f"No implementation for {tool_type.value}"},
            )

        try:
            tool_fn = self.tools[tool_type]
            result = tool_fn(query, decision.extracted_params)
            return ToolResult(
                tool_type=tool_type,
                success=True,
                result=result,
                source=tool_type.value,
                confidence=1.0 if decision.confidence == RoutingConfidence.DEFINITE else 0.8,
                metadata={"params": decision.extracted_params},
            )
        except Exception as e:
            return ToolResult(
                tool_type=tool_type,
                success=False,
                result=None,
                source=tool_type.value,
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def register_tool(self, tool_type: ToolType, implementation: Callable):
        """Register a tool implementation."""
        self.tools[tool_type] = implementation


# =============================================================================
# BUILT-IN TOOL IMPLEMENTATIONS
# =============================================================================

def calculator_tool(query: str, params: Dict) -> Dict:
    """Simple calculator for basic arithmetic."""
    numbers = params.get("numbers", [])

    # Try to evaluate simple expressions
    # Extract expression from query
    expr_match = re.search(r'(\d+\.?\d*)\s*([\+\-\*\/\^])\s*(\d+\.?\d*)', query)
    if expr_match:
        a, op, b = expr_match.groups()
        a, b = float(a), float(b)

        ops = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y if y != 0 else float('inf'),
            '^': lambda x, y: x ** y,
        }

        if op in ops:
            result = ops[op](a, b)
            return {
                "expression": f"{a} {op} {b}",
                "result": result,
                "type": "arithmetic",
            }

    # Percentage calculation
    pct_match = re.search(r'(\d+\.?\d*)\s*%\s*of\s*(\d+\.?\d*)', query, re.IGNORECASE)
    if pct_match:
        pct, base = float(pct_match.group(1)), float(pct_match.group(2))
        result = (pct / 100) * base
        return {
            "expression": f"{pct}% of {base}",
            "result": result,
            "type": "percentage",
        }

    return {"error": "Could not parse expression", "numbers_found": numbers}


def datetime_tool(query: str, params: Dict) -> Dict:
    """Date/time information tool."""
    now = datetime.utcnow()

    if re.search(r'\btoday\b', query, re.IGNORECASE):
        return {
            "query": "today",
            "date": now.strftime("%Y-%m-%d"),
            "day": now.strftime("%A"),
            "iso": now.isoformat() + "Z",
        }

    if re.search(r'\bnow\b|\bcurrent\s+time\b', query, re.IGNORECASE):
        return {
            "query": "now",
            "datetime": now.isoformat() + "Z",
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }

    # Days from/ago calculation
    days_match = re.search(r'(\d+)\s*days?\s*(from\s+now|ago)', query, re.IGNORECASE)
    if days_match:
        days = int(days_match.group(1))
        direction = days_match.group(2).lower()
        from datetime import timedelta

        if "ago" in direction:
            target = now - timedelta(days=days)
        else:
            target = now + timedelta(days=days)

        return {
            "query": f"{days} days {'ago' if 'ago' in direction else 'from now'}",
            "reference_date": now.strftime("%Y-%m-%d"),
            "target_date": target.strftime("%Y-%m-%d"),
            "target_day": target.strftime("%A"),
        }

    return {"current_utc": now.isoformat() + "Z"}


# =============================================================================
# FACTORY
# =============================================================================

def create_default_router() -> ToolFirstRouter:
    """Create router with built-in tools."""
    router = ToolFirstRouter(strict_mode=True)
    router.register_tool(ToolType.CALCULATOR, calculator_tool)
    router.register_tool(ToolType.DATE_TIME, datetime_tool)
    return router


# =============================================================================
# MAIN (TESTING)
# =============================================================================

if __name__ == "__main__":
    print("=== Tool-First Router Test ===\n")

    router = create_default_router()

    test_queries = [
        "What is 15% of 250?",
        "Calculate 1000 * 1.05 ^ 10",
        "What day is today?",
        "What is 30 days from now?",
        "What are the FCA SYSC 4.1 requirements?",
        "Find the entity with LEI 5493001KJTIIGC8Y1R12",
        "What is the current SONIA rate?",
        "Convert 100 GBP to USD",
        "Tell me about machine learning",  # Should fallback to LLM
    ]

    for query in test_queries:
        decision = router.route(query)
        print(f"Query: {query}")
        print(f"  Tool: {decision.tool_type.value}")
        print(f"  Confidence: {decision.confidence.value}")
        print(f"  Patterns: {decision.matched_patterns[:2]}...")

        if decision.tool_type in router.tools:
            result = router.execute(decision, query)
            print(f"  Result: {result.result}")
        print()
