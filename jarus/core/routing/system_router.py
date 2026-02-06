from typing import Dict, Any, Optional
from functools import lru_cache
from core.routing.tool_first_router import ToolFirstRouter, RoutingDecision, ToolType, ToolResult, create_default_router
from core.routing.model_selector import ModelSelector, ModelAssignment

class SystemRouter:
    """
    Unified entry point for routing queries to either deterministic tools
    or the optimal LLM.
    """
    
    def __init__(
        self, 
        tool_router: Optional[ToolFirstRouter] = None,
        model_selector: Optional[ModelSelector] = None,
        cache_size: int = 128
    ):
        self.tool_router = tool_router or create_default_router()
        self.model_selector = model_selector or ModelSelector()
        # Bind cached version of route_and_execute
        self.route_and_execute = lru_cache(maxsize=cache_size)(self._route_and_execute)

    def _route_and_execute(self, query: str, has_attachments: bool = False) -> Dict[str, Any]:
        # 1. Try deterministic tool routing first
        tool_decision = self.tool_router.route(query)
        
        # 2. Select optimal model (always do this to have it as secondary/fallback)
        model_assignment = self.model_selector.select_model(query, has_attachments)
        
        # 3. Determine if we can use a tool
        if tool_decision.tool_type != ToolType.LLM_SYNTHESIS:
            # Execute tool
            tool_result = self.tool_router.execute(tool_decision, query)
            
            if tool_result.success:
                return {
                    "routing_decision": "tool_primary",
                    "tool": tool_decision.to_dict(),
                    "tool_result": {
                        "success": tool_result.success,
                        "data": tool_result.result,
                        "source": tool_result.source,
                        "confidence": tool_result.confidence
                    },
                    "recommended_fallback_model": {
                        "model_id": model_assignment.model_id,
                        "tier": model_assignment.tier.value,
                        "reason": model_assignment.reason
                    },
                    "note": "Deterministic tool execution successful. Model assignment provided for synthesis.",
                    "cached": False
                }
        
        # 4. If no tool matched or tool failed, use selected model
        return {
            "routing_decision": "model_primary",
            "tool": tool_decision.to_dict() if tool_decision else None,
            "model_assignment": {
                "model_id": model_assignment.model_id,
                "tier": model_assignment.tier.value,
                "reason": model_assignment.reason
            },
            "note": "No deterministic tool match found or tool failed. Routed to optimal LLM.",
            "cached": False
        }

    def route_and_execute(self, query: str, has_attachments: bool = False) -> Dict[str, Any]:
        # This will be replaced by lru_cache in __init__
        pass

if __name__ == "__main__":
    router = SystemRouter()
    
    test_queries = [
        "What is 15% of 250?",
        "What day is today?",
        "Analyze this regulatory requirement for compliance",
        "Summarize this long document",
        "Interpret this dashboard screenshot",
        "Debug the UI rendering issues in the empathy panel",
        "Parse the latest error logs from the truth-engine",
        "Extract all LEI numbers from the transaction report"
    ]
    
    for query in test_queries:
        has_attach = "screenshot" in query or "dashboard" in query
        result = router.route_and_execute(query, has_attach)
        print(f"Query: {query}")
        print(f"  Routing Decision: {result['routing_decision']}")
        if result['routing_decision'] == 'tool_primary':
            print(f"  Tool: {result['tool']['tool_type']} (Conf: {result['tool']['confidence']})")
            print(f"  Tool Result: {result['tool_result']['data']}")
            print(f"  Recommended Model: {result['recommended_fallback_model']['model_id']}")
        else:
            print(f"  Selected Model: {result['model_assignment']['model_id']} ({result['model_assignment']['tier']})")
            print(f"  Reason: {result['model_assignment']['reason']}")
        print("-" * 60)
