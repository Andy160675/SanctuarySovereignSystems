"""
Advocate Agent - Primary task executor (v2.0.0)
Charter-aligned agent that works through governed proxies

Now with REAL tool execution:
- Filesystem proxy for file operations
- API gateway proxy for external API calls
- Database proxy for data operations
- LLM-based tool selection and parameter extraction
"""

import os
import json
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Advocate Agent", version="2.0.0")

# Configuration
AGENT_NAME = os.environ.get("AGENT_NAME", "advocate")
FILESYSTEM_URL = os.environ.get("FILESYSTEM_URL", "http://filesystem-proxy:8080")
API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL", "http://api-gateway-proxy:8084")
DB_PROXY_URL = os.environ.get("DB_PROXY_URL", "http://db-proxy:8085")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080/log")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
PLANNER_URL = os.environ.get("PLANNER_URL", "http://planner-agent:8000")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://ledger_service:8082")
POLICY_URL = os.environ.get("POLICY_URL", "http://policy_gate:8181/v1/data/mission/authz")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3.2")


class ToolType(str, Enum):
    """Available tool proxies for task execution."""
    FILESYSTEM = "filesystem"
    API_GATEWAY = "api_gateway"
    DATABASE = "database"
    LLM_ONLY = "llm_only"  # Pure reasoning, no external tool

# Task tracking
active_tasks: Dict[str, "TaskExecution"] = {}


class TaskRequest(BaseModel):
    task_id: str
    mission_id: str
    description: str
    sequence: int


class TaskExecution(BaseModel):
    task_id: str
    mission_id: str
    description: str
    status: str = "received"
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class ToolCall(BaseModel):
    """Represents a tool invocation decision."""
    tool: ToolType
    action: str
    parameters: Dict[str, Any]
    reasoning: str


# =============================================================================
# TOOL PROXY CLIENTS
# =============================================================================

async def call_filesystem_proxy(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute filesystem operations through the governed proxy."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "read":
                response = await client.get(
                    f"{FILESYSTEM_URL}/read",
                    params={"path": params.get("path", "")}
                )
            elif action == "write":
                response = await client.post(
                    f"{FILESYSTEM_URL}/write",
                    json={"path": params.get("path", ""), "content": params.get("content", "")}
                )
            elif action == "list":
                response = await client.get(
                    f"{FILESYSTEM_URL}/list",
                    params={"path": params.get("path", "/")}
                )
            elif action == "exists":
                response = await client.get(
                    f"{FILESYSTEM_URL}/exists",
                    params={"path": params.get("path", "")}
                )
            else:
                return {"success": False, "error": f"Unknown filesystem action: {action}"}

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 403:
                return {"success": False, "error": "Policy denied", "details": response.text}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def call_api_gateway_proxy(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute external API calls through the governed proxy."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_GATEWAY_URL}/request",
                json={
                    "method": params.get("method", "GET"),
                    "url": params.get("url", ""),
                    "headers": params.get("headers", {}),
                    "body": params.get("body")
                }
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 403:
                return {"success": False, "error": "Policy denied - host not in allowlist"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def call_db_proxy(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute database operations through the governed proxy."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "query":
                response = await client.post(
                    f"{DB_PROXY_URL}/query",
                    json={"sql": params.get("sql", ""), "params": params.get("params", [])}
                )
            elif action == "execute":
                response = await client.post(
                    f"{DB_PROXY_URL}/execute",
                    json={"sql": params.get("sql", ""), "params": params.get("params", [])}
                )
            else:
                return {"success": False, "error": f"Unknown database action: {action}"}

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 403:
                return {"success": False, "error": "Policy denied", "details": response.text}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# TOOL SELECTION (LLM-based)
# =============================================================================

TOOL_SELECTION_PROMPT = """You are a task analyzer for an AI agent system. Given a task description, determine which tool(s) are needed and extract parameters.

Available tools:
1. FILESYSTEM - Read, write, list, or check files
   - Actions: read, write, list, exists
   - Parameters: path (required), content (for write)

2. API_GATEWAY - Make external API calls (only to allowed hosts)
   - Actions: request
   - Parameters: method, url, headers, body

3. DATABASE - Query or modify database
   - Actions: query, execute
   - Parameters: sql, params

4. LLM_ONLY - Pure reasoning/analysis, no external tool needed

Respond with ONLY valid JSON in this format:
{
  "tool": "FILESYSTEM" | "API_GATEWAY" | "DATABASE" | "LLM_ONLY",
  "action": "the specific action",
  "parameters": {"param1": "value1"},
  "reasoning": "brief explanation"
}

Task: """


async def determine_tool_call(task_description: str) -> ToolCall:
    """Use LLM to determine which tool to call for a task."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": TOOL_SELECTION_PROMPT + task_description,
                    "stream": False,
                    "format": "json"
                }
            )

            if response.status_code == 200:
                llm_response = response.json().get("response", "").strip()
                # Parse JSON from LLM response
                try:
                    parsed = json.loads(llm_response)
                    return ToolCall(
                        tool=ToolType(parsed.get("tool", "llm_only").lower()),
                        action=parsed.get("action", ""),
                        parameters=parsed.get("parameters", {}),
                        reasoning=parsed.get("reasoning", "")
                    )
                except (json.JSONDecodeError, ValueError):
                    # Fallback: try to extract JSON from response
                    match = re.search(r'\{[^{}]*\}', llm_response, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group())
                        return ToolCall(
                            tool=ToolType(parsed.get("tool", "llm_only").lower()),
                            action=parsed.get("action", ""),
                            parameters=parsed.get("parameters", {}),
                            reasoning=parsed.get("reasoning", "")
                        )
    except Exception as e:
        print(f"[{AGENT_NAME}] Tool selection error: {e}")

    # Default to LLM-only if tool selection fails
    return ToolCall(
        tool=ToolType.LLM_ONLY,
        action="reason",
        parameters={},
        reasoning="Tool selection failed, falling back to pure reasoning"
    )


async def execute_tool_call(tool_call: ToolCall) -> Dict[str, Any]:
    """Execute the determined tool call through the appropriate proxy."""
    if tool_call.tool == ToolType.FILESYSTEM:
        return await call_filesystem_proxy(tool_call.action, tool_call.parameters)
    elif tool_call.tool == ToolType.API_GATEWAY:
        return await call_api_gateway_proxy(tool_call.action, tool_call.parameters)
    elif tool_call.tool == ToolType.DATABASE:
        return await call_db_proxy(tool_call.action, tool_call.parameters)
    else:
        return {"success": True, "data": None, "note": "LLM-only task, no tool execution needed"}


# =============================================================================
# LLM Integration
# =============================================================================
async def call_ollama(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Call local Ollama instance for task execution reasoning."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            }
            if system_prompt:
                payload["system"] = system_prompt

            response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)

            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return ""
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return ""


# Evidence Logging
async def log_to_evidence(event_type: str, data: dict):
    """Log task events to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                EVIDENCE_URL,
                json={
                    "event_type": event_type,
                    "agent": AGENT_NAME,
                    "action": event_type,
                    "target": data.get("task_id", "unknown"),
                    "outcome": data.get("status", "unknown"),
                    "jurisdiction": "UK",
                    "data": data
                }
            )
    except Exception as e:
        print(f"Failed to log to evidence: {e}")


# Planner Callback
async def report_to_planner(task_id: str, mission_id: str, success: bool,
                            result: Optional[str] = None, error: Optional[str] = None):
    """Report task completion back to the Planner."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{PLANNER_URL}/task_complete",
                json={
                    "task_id": task_id,
                    "mission_id": mission_id,
                    "success": success,
                    "result": result,
                    "error": error
                }
            )
    except Exception as e:
        print(f"Failed to report to planner: {e}")


# =============================================================================
# LEDGER LOGGING (P0 requirement - task_executed events)
# =============================================================================

async def log_to_ledger(event_type: str, data: dict) -> Optional[str]:
    """
    Log task execution events to the append-only ledger.

    This is critical for:
    - EU AI Act Article 14 compliance (human oversight)
    - Mission timeline reconstruction
    - Audit trail for tool executions
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{LEDGER_URL}/append",
                json={
                    "event_type": event_type,
                    "agent": AGENT_NAME,
                    "action": data.get("action", event_type),
                    "target": data.get("mission_id", "unknown"),
                    "outcome": data.get("outcome", "unknown"),
                    "metadata": {
                        "task_id": data.get("task_id"),
                        "mission_id": data.get("mission_id"),
                        "tool_plan": data.get("tool_plan"),
                        "tool_result": data.get("tool_result"),
                        "duration_sec": data.get("duration_sec"),
                        "description": data.get("description")
                    }
                }
            )
            if response.status_code == 200:
                entry_id = response.json().get("entry_id")
                print(f"[{AGENT_NAME}] Logged {event_type} to ledger: {entry_id}")
                return entry_id
    except Exception as e:
        print(f"[{AGENT_NAME}] Failed to log to ledger: {e}")
    return None


# =============================================================================
# Task Execution Logic (v2.0 - with real tool execution + ledger logging)
# =============================================================================

async def execute_task(task: TaskExecution):
    """
    Execute a task using LLM reasoning AND real tool calls through proxies.

    Flow:
    1. LLM determines which tool to use (filesystem/api/database/llm_only)
    2. Execute the tool call through governed proxy
    3. LLM interprets results
    4. Log task_executed event to ledger (P0 requirement)
    5. Report back to Planner
    """
    task.status = "executing"
    task.started_at = datetime.now(timezone.utc).isoformat()
    started_at_ts = datetime.now(timezone.utc).timestamp()

    await log_to_evidence("task_execution_started", {
        "task_id": task.task_id,
        "mission_id": task.mission_id,
        "description": task.description,
        "status": "executing"
    })

    tool_call = None
    tool_result = None

    try:
        # Step 1: Determine which tool to use
        print(f"[{AGENT_NAME}] Determining tool for task: {task.description[:60]}...")
        tool_call = await determine_tool_call(task.description)

        print(f"[{AGENT_NAME}] Tool selected: {tool_call.tool.value}/{tool_call.action}")

        await log_to_evidence("tool_selection", {
            "task_id": task.task_id,
            "mission_id": task.mission_id,
            "tool": tool_call.tool.value,
            "action": tool_call.action,
            "reasoning": tool_call.reasoning
        })

        # Step 2: Execute the tool call through governed proxy
        tool_result = await execute_tool_call(tool_call)

        await log_to_evidence("tool_execution", {
            "task_id": task.task_id,
            "mission_id": task.mission_id,
            "tool": tool_call.tool.value,
            "success": tool_result.get("success", False),
            "error": tool_result.get("error")
        })

        # Step 3: Use LLM to interpret results and generate final response
        if tool_call.tool == ToolType.LLM_ONLY or not tool_result.get("success"):
            # Pure reasoning or tool failed - use LLM directly
            system_prompt = """You are an AI agent executing tasks for a sovereign AI system.
Execute the given task and provide a clear, concise result.
Be specific and actionable in your response."""

            if not tool_result.get("success") and tool_result.get("error"):
                prompt = f"""Task: {task.description}

Tool execution failed with error: {tool_result.get('error')}
Please provide an alternative approach or acknowledge the limitation."""
            else:
                prompt = f"Execute this task and provide the result:\n\nTask: {task.description}"

            result = await call_ollama(prompt, system_prompt)
        else:
            # Tool succeeded - interpret results
            system_prompt = """You are an AI agent summarizing task execution results.
Given the tool output, provide a clear summary of what was accomplished."""

            prompt = f"""Task: {task.description}

Tool used: {tool_call.tool.value} ({tool_call.action})
Tool output: {json.dumps(tool_result.get('data', {}), indent=2)[:2000]}

Summarize what was accomplished."""

            result = await call_ollama(prompt, system_prompt)

            # Append raw tool result for transparency
            if result:
                result = f"{result}\n\n[Tool: {tool_call.tool.value}/{tool_call.action}]"

        if result:
            task.status = "completed"
            task.result = result
        else:
            task.status = "completed"
            if tool_result.get("success"):
                task.result = f"Task completed via {tool_call.tool.value}/{tool_call.action}. Data: {str(tool_result.get('data', {}))[:500]}"
            else:
                task.result = f"Task acknowledged: {task.description}. (Tool: {tool_result.get('error', 'unavailable')})"

        task.completed_at = datetime.now(timezone.utc).isoformat()
        finished_at_ts = datetime.now(timezone.utc).timestamp()
        duration_sec = round(finished_at_ts - started_at_ts, 2)

        # Step 4: Log task_executed to ledger (P0 CRITICAL)
        # This creates the audit trail for mission timeline reconstruction
        await log_to_ledger("task_executed", {
            "task_id": task.task_id,
            "mission_id": task.mission_id,
            "description": task.description,
            "action": f"{tool_call.tool.value}:{tool_call.action}",
            "outcome": "success" if tool_result.get("success", False) else "tool_failed",
            "tool_plan": {
                "tool": tool_call.tool.value,
                "action": tool_call.action,
                "parameters": tool_call.parameters,
                "reasoning": tool_call.reasoning
            },
            "tool_result": {
                "success": tool_result.get("success", False),
                "data_preview": str(tool_result.get("data", ""))[:500] if tool_result.get("data") else None,
                "error": tool_result.get("error")
            },
            "duration_sec": duration_sec
        })

        await log_to_evidence("task_execution_completed", {
            "task_id": task.task_id,
            "mission_id": task.mission_id,
            "status": task.status,
            "tool_used": tool_call.tool.value,
            "tool_success": tool_result.get("success", False),
            "duration_sec": duration_sec,
            "result_preview": task.result[:200] if task.result else None
        })

        # Step 5: Report back to Planner
        await report_to_planner(task.task_id, task.mission_id, success=True, result=task.result)

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.now(timezone.utc).isoformat()
        finished_at_ts = datetime.now(timezone.utc).timestamp()
        duration_sec = round(finished_at_ts - started_at_ts, 2)

        # Log task_failed to ledger
        await log_to_ledger("task_failed", {
            "task_id": task.task_id,
            "mission_id": task.mission_id,
            "description": task.description,
            "action": f"{tool_call.tool.value}:{tool_call.action}" if tool_call else "unknown",
            "outcome": "failed",
            "error": task.error,
            "tool_plan": {
                "tool": tool_call.tool.value if tool_call else None,
                "action": tool_call.action if tool_call else None,
                "parameters": tool_call.parameters if tool_call else None,
                "reasoning": tool_call.reasoning if tool_call else None
            } if tool_call else None,
            "duration_sec": duration_sec
        })

        await log_to_evidence("task_execution_failed", {
            "task_id": task.task_id,
            "mission_id": task.mission_id,
            "status": task.status,
            "error": task.error,
            "duration_sec": duration_sec
        })

        await report_to_planner(task.task_id, task.mission_id, success=False, error=task.error)


# API Endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "advocate", "agent_name": AGENT_NAME}


@app.post("/task", response_model=TaskResponse)
async def receive_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Receive a task from the Planner and execute it."""
    task = TaskExecution(
        task_id=request.task_id,
        mission_id=request.mission_id,
        description=request.description,
        status="received"
    )
    active_tasks[request.task_id] = task

    await log_to_evidence("task_received", {
        "task_id": request.task_id,
        "mission_id": request.mission_id,
        "description": request.description
    })

    background_tasks.add_task(execute_task, task)

    return TaskResponse(task_id=request.task_id, status="accepted", message="Task accepted")


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    task = active_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.dict()


@app.get("/tasks")
async def list_tasks():
    """List all active tasks."""
    return {"tasks": [t.dict() for t in active_tasks.values()]}


@app.get("/capabilities")
async def get_capabilities():
    """Return available tools and their status."""
    capabilities = {
        "version": "2.0.0",
        "tools": {
            "filesystem": {"url": FILESYSTEM_URL, "status": "unknown"},
            "api_gateway": {"url": API_GATEWAY_URL, "status": "unknown"},
            "database": {"url": DB_PROXY_URL, "status": "unknown"},
            "llm": {"url": OLLAMA_URL, "model": MODEL_NAME, "status": "unknown"}
        }
    }

    # Check each tool's health
    async with httpx.AsyncClient(timeout=5.0) as client:
        for tool_name, tool_info in capabilities["tools"].items():
            try:
                if tool_name == "llm":
                    resp = await client.get(f"{tool_info['url']}/api/tags")
                else:
                    resp = await client.get(f"{tool_info['url']}/health")
                tool_info["status"] = "healthy" if resp.status_code == 200 else "unhealthy"
            except Exception:
                tool_info["status"] = "unreachable"

    return capabilities


@app.post("/test_tool")
async def test_tool_selection(description: str):
    """Test tool selection for a given task description."""
    tool_call = await determine_tool_call(description)
    return {
        "task": description,
        "selected_tool": tool_call.tool.value,
        "action": tool_call.action,
        "parameters": tool_call.parameters,
        "reasoning": tool_call.reasoning
    }


class AmendmentVoteRequest(BaseModel):
    amendment_id: str
    proposal_id: str
    target_file: str
    new_content: str
    justification: str
    proposer: Optional[str] = None


class AmendmentVoteResponse(BaseModel):
    vote: str  # "AGREE", "DISAGREE", "ABSTAIN"
    reasoning: str


@app.post("/vote_on_amendment", response_model=AmendmentVoteResponse)
async def vote_on_amendment(request: AmendmentVoteRequest):
    """
    Vote on a proposed constitutional amendment.

    The Advocate evaluates amendments from an OPERATIONAL perspective:
    - Does this change enhance the system's ability to execute tasks effectively?
    - Does it maintain or improve ethical operation?
    - Are the tools and proxies still appropriately governed?
    """
    print(f"[{AGENT_NAME}] Voting on amendment {request.amendment_id}")

    vote_prompt = f"""You are the Advocate agent in a governed AI system.
You must vote on a proposed constitutional amendment.

Your role is to assess OPERATIONAL EFFECTIVENESS - evaluate whether this change:
- Enhances the system's ability to execute tasks effectively
- Maintains or improves ethical operation
- Keeps tools and proxies appropriately governed
- Preserves audit trails and transparency

Amendment Details:
- Target file: {request.target_file}
- Justification: {request.justification}
- Proposer: {request.proposer or 'unknown'}

Proposed new content (excerpt):
{request.new_content[:500]}

Respond in JSON format:
{{"vote": "AGREE" or "DISAGREE" or "ABSTAIN", "reasoning": "brief explanation"}}

Only respond with the JSON object."""

    response_text = await call_ollama(vote_prompt)

    # Parse response
    try:
        if "```" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]

        result = json.loads(response_text)
        vote = result.get("vote", "ABSTAIN").upper()
        reasoning = result.get("reasoning", "No reasoning provided")

        if vote not in ["AGREE", "DISAGREE", "ABSTAIN"]:
            vote = "ABSTAIN"

    except json.JSONDecodeError:
        # Fallback: extract vote from text
        response_upper = response_text.upper()
        if "AGREE" in response_upper and "DISAGREE" not in response_upper:
            vote = "AGREE"
        elif "DISAGREE" in response_upper:
            vote = "DISAGREE"
        else:
            vote = "ABSTAIN"
        reasoning = f"Extracted from response: {response_text[:200]}"

    # Log the vote to ledger
    await log_to_ledger("amendment_vote", {
        "task_id": f"vote-{request.amendment_id}",
        "mission_id": request.amendment_id,
        "description": "Amendment vote",
        "action": "vote_on_amendment",
        "outcome": vote,
        "tool_plan": None,
        "tool_result": None,
        "duration_sec": 0
    })

    print(f"[{AGENT_NAME}] Vote on {request.amendment_id}: {vote}")

    return AmendmentVoteResponse(vote=vote, reasoning=reasoning)


@app.on_event("startup")
async def startup_event():
    """Log agent startup."""
    print(f"[{AGENT_NAME}] Starting up (v2.0.0 - with tool execution)...")
    await log_to_evidence("agent_lifecycle", {
        "agent": AGENT_NAME,
        "action": "startup",
        "version": "2.0.0",
        "capabilities": ["filesystem", "api_gateway", "database", "llm_reasoning"],
        "status": "success"
    })
    print(f"[{AGENT_NAME}] Agent ready. Tool proxies: filesystem, api_gateway, database")
