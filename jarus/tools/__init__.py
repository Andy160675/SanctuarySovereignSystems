"""
JARUS Tools Package
===================
Utility belt for sovereign system operations.

Tool Categories:
- Detection: scan, classify, detect, recognize
- Verification: verify, validate, check, attest
- Enforcement: block, enforce, quarantine, halt
- Evidence: collect, receipt, custody, export

Usage:
    from jarus.tools import ToolRegistry, DetectionToolkit, VerificationToolkit
    
    # Use individual toolkits
    detection = DetectionToolkit()
    result = detection.scan.execute({'path': '/data', 'pattern': '*.log'})
    
    # Or use the unified registry
    registry = ToolRegistry()
    # Register tools from toolkits
"""

from .tool_framework import (
    Tool,
    ToolCategory,
    ToolStatus,
    ToolResult,
    ToolDefinition,
    ToolRegistry
)

from .detection_tools import (
    DetectionToolkit,
    ScanTool,
    ClassifyTool,
    DetectTool,
    RecognizeTool
)

from .verification_tools import (
    VerificationToolkit,
    VerifyTool,
    ValidateTool,
    CheckTool,
    AttestTool
)

from .enforcement_tools import (
    EnforcementToolkit,
    BlockTool,
    EnforceTool,
    QuarantineTool,
    HaltTool
)

from .evidence_tools import (
    EvidenceToolkit,
    CollectTool,
    ReceiptTool,
    CustodyTool,
    ExportTool
)

__version__ = "1.0.0"
__author__ = "Codex Sovereign Systems"

__all__ = [
    # Framework
    'Tool', 'ToolCategory', 'ToolStatus', 'ToolResult', 
    'ToolDefinition', 'ToolRegistry',
    # Toolkits
    'DetectionToolkit', 'VerificationToolkit', 
    'EnforcementToolkit', 'EvidenceToolkit',
    # Detection Tools
    'ScanTool', 'ClassifyTool', 'DetectTool', 'RecognizeTool',
    # Verification Tools
    'VerifyTool', 'ValidateTool', 'CheckTool', 'AttestTool',
    # Enforcement Tools
    'BlockTool', 'EnforceTool', 'QuarantineTool', 'HaltTool',
    # Evidence Tools
    'CollectTool', 'ReceiptTool', 'CustodyTool', 'ExportTool',
]
