import re
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

class ModelCapability(Enum):
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"
    BULK = "bulk"
    VISION = "vision"

class ModelTier(Enum):
    SUPREME = "supreme"   # Gemini 3: "See & Do"
    ELITE = "elite"       # Claude 4.5: "Write & Talk"
    ADVANCED = "advanced" # ChatGPT 5.1: Reasoning/Conversation
    FLASH = "flash"       # Flash Models: Bulk work
    LOCAL = "local"       # Local models (Llama 3/4)

@dataclass
class ModelAssignment:
    model_id: str
    tier: ModelTier
    reason: str

class ModelSelector:
    """
    Selects the optimal model based on task characteristics,
    following the Nate's Model Routing Framework.
    """
    
    # Framework mapping from Gemini3-Routing-Analysis.ipynb
    # Gemini 3 -> "See & Do" (visual, UI, video, large mixed context)
    # Claude Sonnet 4.5 -> "Write & Talk" (text generation, high reasoning)
    # ChatGPT 5.1 -> "Reason & Act" (agent coordination, conversation)
    # Flash Models -> "Cheap bulk work" (summarization, simple tasks)

    REASONING_KEYWORDS = [
        "analyze", "interpret", "reason", "constitutional", "policy", 
        "regulatory", "compliance", "legal", "contradiction", "verify",
        "governance", "ethics", "alignment"
    ]
    
    MULTIMODAL_KEYWORDS = [
        "image", "video", "visual", "ui", "dashboard", "screenshot", 
        "mixed", "multimodal", "pdf", "chart", "diagram", "see", "do",
        "vision", "camera", "display"
    ]

    AGENT_KEYWORDS = [
        "coordinate", "orchestrate", "talk", "chat", "interact",
        "system", "status", "report", "assistant"
    ]
    
    BULK_KEYWORDS = [
        "summarize", "list", "extract", "format", "simple", "bulk",
        "translate", "clean", "parse", "log", "search"
    ]

    def __init__(self, default_model: str = "llama3:8b"):
        self.default_model = default_model
        # Pre-compile combined regexes for efficiency
        self._reasoning_re = re.compile(rf'\b(?:{"|".join(re.escape(k) for k in self.REASONING_KEYWORDS)})\b', re.IGNORECASE)
        self._multimodal_re = re.compile(rf'\b(?:{"|".join(re.escape(k) for k in self.MULTIMODAL_KEYWORDS)})\b', re.IGNORECASE)
        self._agent_re = re.compile(rf'\b(?:{"|".join(re.escape(k) for k in self.AGENT_KEYWORDS)})\b', re.IGNORECASE)
        self._bulk_re = re.compile(rf'\b(?:{"|".join(re.escape(k) for k in self.BULK_KEYWORDS)})\b', re.IGNORECASE)

    def select_model(self, task_description: str, has_attachments: bool = False) -> ModelAssignment:
        task_lower = task_description.lower()
        
        # 1. Check for Multimodal/Visual (Gemini 3 / Supreme Tier)
        if has_attachments or self._multimodal_re.search(task_lower):
            return ModelAssignment(
                model_id="gemini-3",
                tier=ModelTier.SUPREME,
                reason="Handles visual/multimodal context and 'See & Do' tasks."
            )
            
        # 2. Check for High Reasoning (Claude / Elite Tier)
        if self._reasoning_re.search(task_lower):
            return ModelAssignment(
                model_id="claude-4.5-sonnet",
                tier=ModelTier.ELITE,
                reason="Optimal for constitutional reasoning and policy interpretation."
            )

        # 3. Check for Agent/Conversation (ChatGPT / Advanced Tier)
        if self._agent_re.search(task_lower):
            return ModelAssignment(
                model_id="chatgpt-5.1",
                tier=ModelTier.ADVANCED,
                reason="Optimal for agent coordination and complex conversation."
            )
            
        # 4. Check for Bulk/Simple (Flash Tier)
        if self._bulk_re.search(task_lower):
            return ModelAssignment(
                model_id="flash-model",
                tier=ModelTier.FLASH,
                reason="Cost-effective for bulk processing and simple tasks."
            )
            
        # Default to Local or General Advanced
        return ModelAssignment(
            model_id=self.default_model,
            tier=ModelTier.LOCAL,
            reason="General task, defaulting to local model."
        )

if __name__ == "__main__":
    selector = ModelSelector()
    test_cases = [
        ("Analyze this regulatory requirement for compliance", False),
        ("Summarize these 100 documents", False),
        ("Interpret the data in this dashboard screenshot", True),
        ("What is the capital of France?", False)
    ]
    
    for task, attach in test_cases:
        assignment = selector.select_model(task, attach)
        print(f"Task: {task}")
        print(f"  Model: {assignment.model_id} ({assignment.tier.value})")
        print(f"  Reason: {assignment.reason}\n")
