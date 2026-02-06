#!/usr/bin/env python3
"""
JARUS Tool Base
===============
Base classes and specifications for all tools.

Author: Codex Sovereign Systems
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time
import hashlib
import json
from datetime import datetime, timezone

class ToolCategory(Enum):
    DETECTION = "DETECTION"
    VERIFICATION = "VERIFICATION"
    ENFORCEMENT = "ENFORCEMENT"
    REMEDIATION = "REMEDIATION"
    EVIDENCE = "EVIDENCE"
    INTELLIGENCE = "INTELLIGENCE"
    COORDINATION = "COORDINATION"

class ToolStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    TIMEOUT = "TIMEOUT"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"

@dataclass
class ToolSpec:
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Dict]
    requires_approval: bool = False
    timeout_seconds: int = 30

@dataclass
class ToolResult:
    tool_name: str
    status: ToolStatus
    output: Any
    evidence_hash: str
    execution_time_ms: float
    error: Optional[str] = None
    
    @property
    def succeeded(self) -> bool:
        return self.status in (ToolStatus.SUCCESS, ToolStatus.PARTIAL)

class Tool(ABC):
    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        pass

    @abstractmethod
    def _execute(self, params: Dict) -> Any:
        pass

    def execute(self, params: Dict) -> ToolResult:
        start_time = time.time()
        
        if self.spec.requires_approval and not params.get('approved', False):
            return ToolResult(
                tool_name=self.spec.name,
                status=ToolStatus.REQUIRES_APPROVAL,
                output=None,
                evidence_hash="",
                execution_time_ms=0,
                error="Approval required"
            )

        try:
            output = self._execute(params)
            elapsed = (time.time() - start_time) * 1000
            
            evidence = {
                'tool': self.spec.name,
                'params': params,
                'output': output,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True, default=str).encode()).hexdigest()
            
            return ToolResult(
                tool_name=self.spec.name,
                status=ToolStatus.SUCCESS,
                output=output,
                evidence_hash=evidence_hash,
                execution_time_ms=elapsed
            )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.spec.name,
                status=ToolStatus.FAILURE,
                output=None,
                evidence_hash="",
                execution_time_ms=elapsed,
                error=str(e)
            )
