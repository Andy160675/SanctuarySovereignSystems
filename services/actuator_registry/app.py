"""
Actuator Registry - Central Discovery Service
==============================================

Provides service discovery for actuators in the Sovereign System.
Actuators register their capabilities and endpoints on startup,
enabling the orchestrator to route missions to appropriate handlers.

v1.0.0 - Initial release
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, Dict, List

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Actuator Registry", version="1.0.0")

# In-memory registry (production would use Redis/etcd)
REGISTRY: Dict[str, dict] = {}

# Health check interval
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))


# =============================================================================
# Models
# =============================================================================

class ActuatorRegistration(BaseModel):
    name: str
    sector: str
    capabilities: List[str]
    endpoint: str
    health_endpoint: str


class ActuatorInfo(BaseModel):
    name: str
    sector: str
    capabilities: List[str]
    endpoint: str
    health_endpoint: str
    status: str  # "healthy" | "unhealthy" | "unknown"
    registered_at: str
    last_health_check: Optional[str] = None


# =============================================================================
# Registry Operations
# =============================================================================

@app.post("/register", status_code=201)
async def register_actuator(registration: ActuatorRegistration):
    """Register a new actuator or update existing registration."""
    now = datetime.now(timezone.utc).isoformat()

    REGISTRY[registration.name] = {
        "name": registration.name,
        "sector": registration.sector,
        "capabilities": registration.capabilities,
        "endpoint": registration.endpoint,
        "health_endpoint": registration.health_endpoint,
        "status": "unknown",
        "registered_at": now,
        "last_health_check": None
    }

    print(f"[registry] Registered actuator: {registration.name} "
          f"(sector={registration.sector}, capabilities={registration.capabilities})")

    return {"status": "registered", "actuator": registration.name}


@app.delete("/deregister/{name}")
async def deregister_actuator(name: str):
    """Remove an actuator from the registry."""
    if name in REGISTRY:
        del REGISTRY[name]
        print(f"[registry] Deregistered actuator: {name}")
        return {"status": "deregistered", "actuator": name}
    raise HTTPException(status_code=404, detail=f"Actuator {name} not found")


@app.get("/actuators", response_model=List[ActuatorInfo])
async def list_actuators():
    """List all registered actuators."""
    return [ActuatorInfo(**info) for info in REGISTRY.values()]


@app.get("/actuators/{name}", response_model=ActuatorInfo)
async def get_actuator(name: str):
    """Get details of a specific actuator."""
    if name in REGISTRY:
        return ActuatorInfo(**REGISTRY[name])
    raise HTTPException(status_code=404, detail=f"Actuator {name} not found")


@app.get("/actuators/sector/{sector}", response_model=List[ActuatorInfo])
async def get_actuators_by_sector(sector: str):
    """Get all actuators in a specific sector."""
    return [
        ActuatorInfo(**info)
        for info in REGISTRY.values()
        if info["sector"] == sector
    ]


@app.get("/actuators/capability/{capability}", response_model=List[ActuatorInfo])
async def get_actuators_by_capability(capability: str):
    """Get all actuators with a specific capability."""
    return [
        ActuatorInfo(**info)
        for info in REGISTRY.values()
        if capability in info["capabilities"]
    ]


@app.get("/resolve/{sector}/{capability}")
async def resolve_actuator(sector: str, capability: str):
    """
    Resolve the best actuator for a given sector and capability.
    Returns the first healthy actuator that matches.
    """
    for info in REGISTRY.values():
        if (info["sector"] == sector and
            capability in info["capabilities"] and
            info["status"] == "healthy"):
            return {
                "actuator": info["name"],
                "endpoint": info["endpoint"],
                "status": "resolved"
            }

    # Fallback to any matching actuator regardless of health
    for info in REGISTRY.values():
        if info["sector"] == sector and capability in info["capabilities"]:
            return {
                "actuator": info["name"],
                "endpoint": info["endpoint"],
                "status": "resolved_unhealthy",
                "warning": "No healthy actuator found, using available one"
            }

    raise HTTPException(
        status_code=404,
        detail=f"No actuator found for sector={sector}, capability={capability}"
    )


# =============================================================================
# Health Checking
# =============================================================================

async def check_actuator_health(name: str, info: dict):
    """Check health of a single actuator."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(info["health_endpoint"])
            if response.status_code == 200:
                REGISTRY[name]["status"] = "healthy"
            else:
                REGISTRY[name]["status"] = "unhealthy"
    except Exception:
        REGISTRY[name]["status"] = "unhealthy"

    REGISTRY[name]["last_health_check"] = datetime.now(timezone.utc).isoformat()


async def health_check_loop():
    """Periodically check health of all registered actuators."""
    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        for name, info in list(REGISTRY.items()):
            await check_actuator_health(name, info)


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "actuator_registry",
        "registered_count": len(REGISTRY)
    }


@app.get("/stats")
async def stats():
    """Get registry statistics."""
    sectors = {}
    capabilities = {}
    healthy_count = 0

    for info in REGISTRY.values():
        sector = info["sector"]
        sectors[sector] = sectors.get(sector, 0) + 1

        for cap in info["capabilities"]:
            capabilities[cap] = capabilities.get(cap, 0) + 1

        if info["status"] == "healthy":
            healthy_count += 1

    return {
        "total_actuators": len(REGISTRY),
        "healthy_actuators": healthy_count,
        "by_sector": sectors,
        "by_capability": capabilities
    }


# =============================================================================
# Lifecycle
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Start the health check loop."""
    print("[registry] Actuator Registry starting up...")
    asyncio.create_task(health_check_loop())
    print(f"[registry] Health check interval: {HEALTH_CHECK_INTERVAL}s")
    print("[registry] Ready to accept registrations")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown."""
    print("[registry] Shutting down...")
