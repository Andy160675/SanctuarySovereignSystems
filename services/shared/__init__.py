"""
Shared utilities for Sovereign System services.

Modules:
- auth: API key authentication middleware
- freeze_guard: Emergency freeze state enforcement
"""

from .freeze_guard import (
    emergency_freeze_active,
    check_freeze,
    get_freeze_status,
    freeze_guard_dependency,
    freeze_guard_middleware_check,
    require_no_freeze,
    FreezeActiveError,
)

from .auth import (
    AuthConfig,
    AuthMiddleware,
    get_api_key,
    require_auth,
    generate_api_key,
    hash_api_key,
    ServiceAuth,
    service_auth,
)

__all__ = [
    # Freeze guard
    "emergency_freeze_active",
    "check_freeze",
    "get_freeze_status",
    "freeze_guard_dependency",
    "freeze_guard_middleware_check",
    "require_no_freeze",
    "FreezeActiveError",
    # Auth
    "AuthConfig",
    "AuthMiddleware",
    "get_api_key",
    "require_auth",
    "generate_api_key",
    "hash_api_key",
    "ServiceAuth",
    "service_auth",
]
