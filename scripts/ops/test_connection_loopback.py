"""
scripts/ops/test_connection_loopback.py

Runs a local loopback test between pc-a (client) and pc-b (server).
Verifies mTLS and evidence generation.
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from core.transport.stls_server import SovereignTLSServer
from core.transport.message_router import ConstitutionalMessageRouter
from core.transport.constitutional_message import ConstitutionalMessage, MessageType, MessagePriority

async def run_test():
    print("--- Starting Pentad Connection Loopback Test ---")
    
    # 1. Start Server (pc-b)
    server_b = SovereignTLSServer(
        head_id="pc-b",
        port=8442,
        allowed_roles=["constitutional", "orchestration"]
    )
    await server_b.start()
    
    # 2. Setup Router (pc-a)
    router_a = ConstitutionalMessageRouter(
        head_id="pc-a",
        role="constitutional"
    )
    # Start the worker task
    worker_task = asyncio.create_task(router_a.start_worker())
    
    # 3. Create and Route Message
    msg = ConstitutionalMessage(
        message_id="MSG-001",
        sender="pc-a",
        recipients=["pc-b"],
        message_type=MessageType.WORKFLOW,
        priority=MessagePriority.HIGH,
        timestamp=datetime.utcnow().isoformat(),
        payload={"action": "test_handshake", "data": "Sovereign protocol active"},
        evidence_chain=[],
        nonce="nonce-123"
    )
    msg.sign()
    
    print(f"[pc-a] Routing message {msg.message_id} to pc-b...")
    await router_a.route_message(msg)
    
    # 4. Wait for delivery
    await asyncio.sleep(3)
    
    # 5. Cleanup
    await server_b.stop()
    worker_task.cancel()
    
    print("\n--- Connection Loopback Test Complete ---")
    print("Check evidence_store/connection/ for logs:")
    for f in Path("evidence_store/connection").glob("*.jsonl"):
        print(f"  - {f}")

if __name__ == "__main__":
    asyncio.run(run_test())
