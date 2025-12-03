"""
Sovereign System Authentication Middleware
==========================================

Provides API key authentication for FastAPI services.
Supports both header-based and query parameter authentication.

Usage:
    from shared.auth import get_api_key, require_auth, AuthConfig

    # Configure auth
    auth_config = AuthConfig()

    # Dependency injection in routes
    @app.get("/protected")
    async def protected_route(api_key: str = Depends(get_api_key)):
        return {"message": "Authenticated"}

    # Or use the middleware for all routes
    app.add_middleware(AuthMiddleware, config=auth_config)

v1.0.0 - Basic API key authentication
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone
from typing import Optional, List, Callable

from fastapi import HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# =============================================================================
# Configuration
# =============================================================================

class AuthConfig:
    """Authentication configuration from environment variables."""

    def __init__(self):
        # Primary API key (required for protected endpoints)
        self.api_key = os.getenv("SOVEREIGN_API_KEY", "")

        # Enable/disable auth (useful for development)
        self.auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() == "true"

        # Paths that don't require authentication
        self.public_paths: List[str] = [
            "/health",
            "/info",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

        # Header name for API key
        self.header_name = os.getenv("AUTH_HEADER_NAME", "X-API-Key")

        # Query param name for API key (fallback)
        self.query_param_name = "api_key"

        # Rate limiting (requests per minute per key)
        self.rate_limit = int(os.getenv("AUTH_RATE_LIMIT", "60"))

    def is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)."""
        return any(path.startswith(p) for p in self.public_paths)


# Global config instance
_config = AuthConfig()


# =============================================================================
# Security Schemes
# =============================================================================

api_key_header = APIKeyHeader(name=_config.header_name, auto_error=False)
api_key_query = APIKeyQuery(name=_config.query_param_name, auto_error=False)


# =============================================================================
# Validation
# =============================================================================

def _validate_api_key(provided_key: Optional[str]) -> bool:
    """
    Validate API key using constant-time comparison.
    Returns True if valid, False otherwise.
    """
    if not _config.api_key:
        # No API key configured = all keys rejected (fail closed)
        return False

    if not provided_key:
        return False

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(provided_key, _config.api_key)


async def get_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query),
) -> str:
    """
    FastAPI dependency to extract and validate API key.

    Checks header first, then query parameter.
    Raises HTTPException if invalid.
    """
    if not _config.auth_enabled:
        return "auth-disabled"

    # Try header first, then query param
    provided_key = api_key_header or api_key_query

    if _validate_api_key(provided_key):
        return provided_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication on a route.

    Usage:
        @app.get("/protected")
        @require_auth
        async def protected():
            return {"message": "OK"}
    """
    async def wrapper(*args, **kwargs):
        # This is a simple marker decorator
        # Actual auth is handled by middleware or dependency
        return await func(*args, **kwargs)
    return wrapper


# =============================================================================
# Middleware
# =============================================================================

class AuthMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for API key authentication.

    Validates all non-public requests have valid API key.
    """

    def __init__(self, app, config: Optional[AuthConfig] = None):
        super().__init__(app)
        self.config = config or _config

    async def dispatch(self, request: Request, call_next):
        # Skip if auth disabled
        if not self.config.auth_enabled:
            return await call_next(request)

        # Skip public paths
        if self.config.is_public_path(request.url.path):
            return await call_next(request)

        # Extract API key
        api_key = request.headers.get(self.config.header_name)
        if not api_key:
            api_key = request.query_params.get(self.config.query_param_name)

        # Validate
        if not _validate_api_key(api_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "unauthorized",
                    "message": "Invalid or missing API key",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                headers={"WWW-Authenticate": "ApiKey"}
            )

        # Add auth info to request state
        request.state.authenticated = True
        request.state.api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        return await call_next(request)


# =============================================================================
# Utilities
# =============================================================================

def generate_api_key(length: int = 32) -> str:
    """Generate a cryptographically secure API key."""
    return secrets.token_urlsafe(length)


def hash_api_key(key: str) -> str:
    """Generate a hash of an API key for logging/storage."""
    return hashlib.sha256(key.encode()).hexdigest()


# =============================================================================
# Service-to-Service Auth
# =============================================================================

class ServiceAuth:
    """
    Service-to-service authentication for internal calls.

    Uses a separate key for internal service communication.
    """

    def __init__(self):
        self.service_key = os.getenv("SOVEREIGN_SERVICE_KEY", "")

    def get_auth_headers(self) -> dict:
        """Get headers for authenticated internal requests."""
        return {
            "X-Service-Key": self.service_key,
            "X-Service-Auth": "internal"
        }

    def validate_service_key(self, provided_key: str) -> bool:
        """Validate an internal service key."""
        if not self.service_key:
            return False
        return hmac.compare_digest(provided_key, self.service_key)


# Global service auth instance
service_auth = ServiceAuth()
