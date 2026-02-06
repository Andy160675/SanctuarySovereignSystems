#!/usr/bin/env python3
"""
JARUS Tool Framework
====================
Base classes and registry for sovereign system tools.

Every tool:
- Has a standardized interface
- Produces evidence of execution
- Respects constitutional constraints
- Can require approval for critical operations

Design Principles:
- Tools are stateless functions with context
- Results always include evidence hash
- Failures are explicit, never silent
- Critical tools require approval flag

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod

# Import core modules
from ..core.constitutional_runtime import ConstitutionalRuntime, DecisionType
from ..core.evidence_ledger import EvidenceLedger, EvidenceType
from ..core.surge_wrapper import SurgeWrapper


# =============================================================================
# ENUMS
# =============================================================================

class ToolCategory(Enum):
    """Categories of tools in the utility belt."""
    DETECTION = "DETECTION"         # Find and identify
    VERIFICATION = "VERIFICATION"   # Validate and check
    ENFORCEMENT = "ENFORCEMENT"     # Block and control
    REMEDIATION = "REMEDIATION"     # Fix and repair
    EVIDENCE = "EVIDENCE"           # Collect and record
    INTELLIGENCE = "INTELLIGENCE"   # Analyze and reason
    LOGGING = "LOGGING"             # Record and track
    COORDINATION = "COORDINATION"   # Orchestrate and manage


class ToolStatus(Enum):
    """Outcome status of tool execution."""
    SUCCESS = "SUCCESS"         # Completed successfully
    FAILURE = "FAILURE"         # Failed to complete
    PARTIAL = "PARTIAL"         # Partially completed
    BLOCKED = "BLOCKED"         # Blocked by constraint
    TIMEOUT = "TIMEOUT"         # Exceeded time limit
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"  # Needs human approval


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ToolResult:
    """
    Standard result from any tool execution.
    
    Every tool returns this structure, ensuring:
    - Consistent interface for callers
    - Evidence hash for audit trail
    - Clear success/failure indication
    - Metadata for debugging
    """
    tool_name: str
    status: ToolStatus
    data: Any
    evidence_hash: str
    execution_time_ms: float
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict:
        """Serialize for storage or transmission."""
        return {
            'tool_name': self.tool_name,
            'status': self.status.value,
            'data': self.data,
            'evidence_hash': self.evidence_hash,
            'execution_time_ms': self.execution_time_ms,
            'error': self.error,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
    
    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ToolStatus.SUCCESS


@dataclass
class ToolDefinition:
    """
    Definition of a tool in the registry.
    
    Contains metadata about the tool for:
    - Discovery and documentation
    - Permission checking
    - Approval requirements
    """
    name: str
    category: ToolCategory
    description: str
    handler: Callable
    requires_approval: bool = False
    timeout_seconds: int = 30
    parameters: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Serialize for documentation."""
        return {
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'requires_approval': self.requires_approval,
            'timeout_seconds': self.timeout_seconds,
            'parameters': self.parameters
        }


# =============================================================================
# TOOL BASE CLASS
# =============================================================================

class Tool(ABC):
    """
    Abstract base class for all JARUS tools.
    
    Subclass this to create new tools with:
    - Standardized execution flow
    - Automatic evidence generation
    - Error handling
    - Timing measurement
    
    Example:
        class ScanTool(Tool):
            @property
            def name(self) -> str:
                return "scan"
            
            @property
            def category(self) -> ToolCategory:
                return ToolCategory.DETECTION
            
            @property
            def description(self) -> str:
                return "Scan filesystem for patterns"
            
            def _execute(self, context: Dict) -> Any:
                # Implementation
                return {'files_found': 42}
    """
    
    def __init__(self):
        self._execution_count = 0
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool category."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass
    
    @property
    def requires_approval(self) -> bool:
        """Whether this tool requires operator approval."""
        return False
    
    @property
    def timeout_seconds(self) -> int:
        """Maximum execution time."""
        return 30
    
    @property
    def parameters(self) -> Dict:
        """Parameter definitions for documentation."""
        return {}
    
    @abstractmethod
    def _execute(self, context: Dict) -> Any:
        """
        Execute the tool logic.
        
        Override this in subclasses.
        
        Args:
            context: Execution context with parameters
            
        Returns:
            Tool-specific result data
        """
        pass
    
    def execute(self, context: Dict) -> ToolResult:
        """
        Execute the tool with standard wrapper.
        
        This method:
        1. Checks approval if required
        2. Times execution
        3. Catches errors
        4. Generates evidence hash
        5. Returns standardized result
        
        Args:
            context: Execution context
            
        Returns:
            ToolResult with status and data
        """
        import time
        start = time.time()
        
        # Check approval requirement
        if self.requires_approval and not context.get('approved', False):
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.APPROVAL_REQUIRED,
                data=None,
                evidence_hash=self._compute_hash({'context': context, 'status': 'approval_required'}),
                execution_time_ms=0,
                error="Tool requires operator approval",
                metadata={'requires_approval': True}
            )
        
        try:
            # Execute tool logic
            data = self._execute(context)
            elapsed = (time.time() - start) * 1000
            
            # Generate evidence hash
            evidence = {
                'tool': self.name,
                'context_hash': self._compute_hash(context),
                'data_hash': self._compute_hash(data),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            evidence_hash = self._compute_hash(evidence)
            
            self._execution_count += 1
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=data,
                evidence_hash=evidence_hash,
                execution_time_ms=elapsed,
                metadata={'execution_count': self._execution_count}
            )
            
        except TimeoutError as e:
            elapsed = (time.time() - start) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                data=None,
                evidence_hash=self._compute_hash({'error': str(e)}),
                execution_time_ms=elapsed,
                error=str(e)
            )
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                data=None,
                evidence_hash=self._compute_hash({'error': str(e)}),
                execution_time_ms=elapsed,
                error=str(e)
            )
    
    def _compute_hash(self, data: Any) -> str:
        """Compute SHA-256 hash of data."""
        if isinstance(data, bytes):
            return hashlib.sha256(data).hexdigest()
        else:
            content = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(content.encode()).hexdigest()
    
    def to_definition(self) -> ToolDefinition:
        """Convert to ToolDefinition for registry."""
        return ToolDefinition(
            name=self.name,
            category=self.category,
            description=self.description,
            handler=self.execute,
            requires_approval=self.requires_approval,
            timeout_seconds=self.timeout_seconds,
            parameters=self.parameters
        )


# =============================================================================
# TOOL REGISTRY
# =============================================================================

class ToolRegistry:
    """
    Registry and orchestrator for JARUS tools.
    
    Manages:
    - Tool registration and discovery
    - Execution with evidence recording
    - Category-based organization
    - Tool documentation generation
    
    Usage:
        registry = ToolRegistry()
        registry.register(ScanTool())
        result = registry.execute("scan", {'path': '/data'})
    """
    
    def __init__(self, 
                 runtime: Optional[ConstitutionalRuntime] = None, 
                 ledger: Optional[EvidenceLedger] = None):
        self._tools: Dict[str, Tool] = {}
        self._definitions: Dict[str, ToolDefinition] = {}
        self._runtime = runtime or ConstitutionalRuntime()
        self._ledger = ledger or EvidenceLedger(auto_persist=False)
        self._surge = SurgeWrapper(self._runtime, self._ledger)
    
    def register(self, tool: Tool) -> str:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
            
        Returns:
            Tool name
        """
        self._tools[tool.name] = tool
        self._definitions[tool.name] = tool.to_definition()
        return tool.name
    
    def register_function(self,
                          name: str,
                          category: ToolCategory,
                          description: str,
                          handler: Callable,
                          requires_approval: bool = False,
                          timeout_seconds: int = 30,
                          parameters: Optional[Dict] = None) -> str:
        """
        Register a function as a tool.
        
        For simple tools that don't need a class.
        
        Args:
            name: Tool name
            category: Tool category
            description: Description
            handler: Function to call
            requires_approval: Whether approval needed
            timeout_seconds: Timeout
            parameters: Parameter definitions
            
        Returns:
            Tool name
        """
        definition = ToolDefinition(
            name=name,
            category=category,
            description=description,
            handler=handler,
            requires_approval=requires_approval,
            timeout_seconds=timeout_seconds,
            parameters=parameters or {}
        )
        self._definitions[name] = definition
        return name
    
    def execute(self, tool_name: str, context: Dict) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            context: Execution context
            
        Returns:
            ToolResult
        """
        # Check if tool exists
        if tool_name not in self._tools and tool_name not in self._definitions:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILURE,
                data=None,
                evidence_hash=hashlib.sha256(f"unknown:{tool_name}".encode()).hexdigest(),
                execution_time_ms=0,
                error=f"Unknown tool: {tool_name}"
            )

        # Build Surge context
        surge_context = {
            'action': tool_name,
            'type': 'tool',
            **context
        }

        # Check for approval flag in Surge context
        if context.get('approved'):
            surge_context['operator_approved'] = True

        try:
            def handler():
                if tool_name in self._tools:
                    return self._tools[tool_name].execute(context).data
                else:
                    return self._definitions[tool_name].handler(context)

            surge_result = self._surge.execute_sovereign_action(
                action_name=tool_name,
                context=surge_context,
                handler=handler
            )

            if surge_result.get("status") == "ESCALATED":
                return ToolResult(
                    tool_name=tool_name,
                    status=ToolStatus.APPROVAL_REQUIRED,
                    data=None,
                    evidence_hash=surge_result["decision"]["hash"],
                    execution_time_ms=0,
                    error="Tool requires operator approval"
                )

            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.SUCCESS,
                data=surge_result["result"],
                evidence_hash=surge_result["receipt"]["entry_hash"],
                execution_time_ms=0 # Duration handled inside surge if needed, but registry returns success
            )

        except PermissionError as e:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.BLOCKED,
                data=None,
                evidence_hash=hashlib.sha256(str(e).encode()).hexdigest(),
                execution_time_ms=0,
                error=str(e)
            )
        except SystemExit as e:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILURE,
                data=None,
                evidence_hash=hashlib.sha256(str(e).encode()).hexdigest(),
                execution_time_ms=0,
                error=f"System HALTED: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILURE,
                data=None,
                evidence_hash=hashlib.sha256(str(e).encode()).hexdigest(),
                execution_time_ms=0,
                error=str(e)
            )
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self._definitions.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """
        List registered tools.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of tool definitions
        """
        if category:
            return [d for d in self._definitions.values() if d.category == category]
        return list(self._definitions.values())
    
    def list_categories(self) -> Dict[str, int]:
        """Get count of tools per category."""
        counts = {}
        for definition in self._definitions.values():
            cat = definition.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    @property
    def tool_count(self) -> int:
        """Total number of registered tools."""
        return len(self._definitions)
    
    def generate_documentation(self) -> Dict:
        """Generate documentation for all tools."""
        by_category = {}
        
        for definition in self._definitions.values():
            cat = definition.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(definition.to_dict())
        
        return {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_tools': self.tool_count,
            'categories': by_category
        }


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Tool Framework.
    
    Tests:
    1. Tool base class
    2. Tool registry
    3. Function-based tool registration
    4. Execution and results
    5. Approval requirement
    """
    print("=" * 60)
    print("JARUS Tool Framework - Self Test")
    print("=" * 60)
    
    # Test 1: Create a simple tool
    print("\n[1] Create tool subclass...")
    
    class EchoTool(Tool):
        @property
        def name(self) -> str:
            return "echo"
        
        @property
        def category(self) -> ToolCategory:
            return ToolCategory.DETECTION
        
        @property
        def description(self) -> str:
            return "Echo back the input"
        
        @property
        def parameters(self) -> Dict:
            return {'message': 'string - message to echo'}
        
        def _execute(self, context: Dict) -> Any:
            return {'echoed': context.get('message', 'no message')}
    
    echo = EchoTool()
    print(f"    Tool name: {echo.name}")
    print(f"    Category: {echo.category.value}")
    assert echo.name == "echo"
    print("    ✓ PASS")
    
    # Test 2: Execute tool directly
    print("\n[2] Execute tool directly...")
    result = echo.execute({'message': 'hello world'})
    print(f"    Status: {result.status.value}")
    print(f"    Data: {result.data}")
    print(f"    Evidence hash: {result.evidence_hash[:16]}...")
    assert result.success
    assert result.data['echoed'] == 'hello world'
    print("    ✓ PASS")
    
    # Test 3: Tool registry
    print("\n[3] Register tool in registry...")
    registry = ToolRegistry()
    registry.register(echo)
    print(f"    Tools registered: {registry.tool_count}")
    assert registry.tool_count == 1
    print("    ✓ PASS")
    
    # Test 4: Execute via registry
    print("\n[4] Execute via registry...")
    result = registry.execute("echo", {'message': 'via registry'})
    print(f"    Status: {result.status.value}")
    print(f"    Data: {result.data}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 5: Register function-based tool
    print("\n[5] Register function-based tool...")
    
    def double_handler(context: Dict) -> Dict:
        value = context.get('value', 0)
        return {'result': value * 2}
    
    registry.register_function(
        name="double",
        category=ToolCategory.INTELLIGENCE,
        description="Double a number",
        handler=double_handler,
        parameters={'value': 'int - number to double'}
    )
    
    result = registry.execute("double", {'value': 21})
    print(f"    Result: {result.data}")
    assert result.data['result'] == 42
    print("    ✓ PASS")
    
    # Test 6: Approval requirement
    print("\n[6] Test approval requirement...")
    
    class CriticalTool(Tool):
        @property
        def name(self) -> str:
            return "critical_action"
        
        @property
        def category(self) -> ToolCategory:
            return ToolCategory.ENFORCEMENT
        
        @property
        def description(self) -> str:
            return "A critical action requiring approval"
        
        @property
        def requires_approval(self) -> bool:
            return True
        
        def _execute(self, context: Dict) -> Any:
            return {'executed': True}
    
    critical = CriticalTool()
    
    # Without approval
    result = critical.execute({})
    print(f"    Without approval: {result.status.value}")
    assert result.status == ToolStatus.APPROVAL_REQUIRED
    
    # With approval
    result = critical.execute({'approved': True})
    print(f"    With approval: {result.status.value}")
    assert result.status == ToolStatus.SUCCESS
    print("    ✓ PASS")
    
    # Test 7: List tools by category
    print("\n[7] List tools by category...")
    registry.register(CriticalTool())
    
    categories = registry.list_categories()
    print(f"    Categories: {categories}")
    assert 'DETECTION' in categories
    assert 'ENFORCEMENT' in categories
    print("    ✓ PASS")
    
    # Test 8: Generate documentation
    print("\n[8] Generate documentation...")
    docs = registry.generate_documentation()
    print(f"    Total tools: {docs['total_tools']}")
    print(f"    Categories documented: {list(docs['categories'].keys())}")
    assert docs['total_tools'] == 3
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Tools tested: 3")
    print(f"Registry functional: Yes")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
