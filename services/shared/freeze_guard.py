"""
Emergency Freeze Guard - Shared module for freeze state enforcement
====================================================================

Import this module in any service that must respect emergency freeze.

Usage:
    from shared.freeze_guard import check_freeze, FreezeActiveError

    @app.post("/execute")
    async def execute_action(request: ActionRequest):
        check_freeze()  # Raises FreezeActiveError if frozen
        # ... proceed with execution

Or as a FastAPI dependency:
    from shared.freeze_guard import freeze_guard_dependency

    @app.post("/execute")
    async def execute_action(
        request: ActionRequest,
        _: None = Depends(freeze_guard_dependency)
    ):
        # ... proceeds only if not frozen

v1.0.0 - Initial release
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status


# =============================================================================
# Configuration
# =============================================================================

# State file location - can be overridden by environment variable
STATE_PATH = Path(os.getenv(
    "SOVEREIGN_STATE_FILE",
    Path(__file__).parent.parent.parent / "config" / "system_state.json"
))

# Cache TTL in seconds (avoid reading file on every request)
_CACHE_TTL = 1.0
_cache: dict = {"state": None, "timestamp": 0.0}


# =============================================================================
# Exceptions
# =============================================================================

class FreezeActiveError(Exception):
    """Raised when an operation is blocked due to emergency freeze."""

    def __init__(self, message: str = "System is in emergency freeze mode"):
        self.message = message
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(self.message)


# =============================================================================
# Core Functions
# =============================================================================

def _load_state() -> dict:
    """Load system state with caching."""
    now = datetime.now(timezone.utc).timestamp()

    # Return cached value if still valid
    if _cache["state"] is not None and (now - _cache["timestamp"]) < _CACHE_TTL:
        return _cache["state"]

    # Load from file
    if not STATE_PATH.exists():
        state = {
            "autobuild_enabled": False,
            "emergency_freeze": False,
            "last_autobuild_change_utc": None,
            "last_emergency_freeze_utc": None,
            "last_changed_by": None
        }
    else:
        try:
            with STATE_PATH.open() as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError):
            # Fail safe - treat as frozen if state file is corrupted
            state = {"emergency_freeze": True}

    # Update cache
    _cache["state"] = state
    _cache["timestamp"] = now

    return state


def emergency_freeze_active() -> bool:
    """
    Check if emergency freeze is currently active.

    Returns:
        True if system is frozen, False otherwise.
    """
    state = _load_state()
    return state.get("emergency_freeze", False)


def check_freeze() -> None:
    """
    Check freeze state and raise if frozen.

    Raises:
        FreezeActiveError: If emergency freeze is active.
    """
    if emergency_freeze_active():
        raise FreezeActiveError(
            "EMERGENCY FREEZE ACTIVE - All mutating operations are blocked. "
            "Use toggle_freeze.py off 7956 to disengage."
        )


def get_freeze_status() -> dict:
    """
    Get detailed freeze status for health/status endpoints.

    Returns:
        Dictionary with freeze state details.
    """
    state = _load_state()
    return {
        "emergency_freeze": state.get("emergency_freeze", False),
        "last_freeze_change": state.get("last_emergency_freeze_utc"),
        "autobuild_enabled": state.get("autobuild_enabled", False),
        "state_file": str(STATE_PATH),
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# FastAPI Integration
# =============================================================================

async def freeze_guard_dependency() -> None:
    """
    FastAPI dependency that blocks requests during emergency freeze.

    Usage:
        @app.post("/execute")
        async def execute(request: Request, _: None = Depends(freeze_guard_dependency)):
            # Only reaches here if not frozen
            ...

    Raises:
        HTTPException: 503 Service Unavailable if frozen.
    """
    if emergency_freeze_active():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "emergency_freeze_active",
                "message": "System is in emergency freeze mode. All mutating operations are blocked.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "Contact system administrator or use toggle_freeze.py off 7956"
            }
        )


def freeze_guard_middleware_check(request_path: str, request_method: str) -> Optional[dict]:
    """
    Check if a request should be blocked by freeze.

    This is for use in custom middleware. Returns None if allowed,
    or an error dict if blocked.

    Args:
        request_path: The request URL path
        request_method: HTTP method (GET, POST, etc.)

    Returns:
        None if request is allowed, error dict if blocked.
    """
    # Read-only methods are always allowed
    if request_method.upper() in ("GET", "HEAD", "OPTIONS"):
        return None

    # Health/status endpoints are always allowed
    safe_paths = ["/health", "/info", "/status", "/metrics", "/docs", "/openapi.json"]
    if any(request_path.startswith(p) for p in safe_paths):
        return None

    # Check freeze for mutating operations
    if emergency_freeze_active():
        return {
            "error": "emergency_freeze_active",
            "message": "System is in emergency freeze mode. Mutating operations are blocked.",
            "path": request_path,
            "method": request_method,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return None


# =============================================================================
# Decorator
# =============================================================================

def require_no_freeze(func):
    """
    Decorator to block function execution during freeze.

    Usage:
        @require_no_freeze
        async def execute_mission(mission_id: str):
            # Only runs if not frozen
            ...
    """
    import functools
    import asyncio

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        check_freeze()
        return await func(*args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        check_freeze()
        return func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
