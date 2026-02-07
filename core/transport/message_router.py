"""
core/transport/message_router.py

Constitutional message router implementation.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from core.transport.constitutional_message import ConstitutionalMessage, MessagePriority
from core.transport.stls_protocol import SovereignTLSContext


class ConstitutionalMessageRouter:
    """Routes messages with constitutional priority and evidence."""

    def __init__(self, head_id: str, role: str, pki_dir: Optional[Path] = None):
        self.head_id = head_id
        self.role = role
        self.pki_dir = pki_dir or Path("evidence_store/pki")
        self.queue = asyncio.PriorityQueue()
        self.routing_table = self._load_routing_table()
        self.stls_ctx = SovereignTLSContext(head_id, role, self.pki_dir)

    def _load_routing_table(self) -> Dict[str, str]:
        # Simple static mapping for local test
        return {
            "pc-a": "127.0.0.1:8441",
            "pc-b": "127.0.0.1:8442",
            "pc-c": "127.0.0.1:8443",
        }

    async def route_message(self, message: ConstitutionalMessage):
        """Queue a message for delivery based on priority."""
        # PriorityQueue sorts ascending, so we use (priority_value, message)
        # Low priority (1) comes before Critical (4) in sorting, so we invert or handle.
        # Actually, if we want Critical first, we should use negative priority.
        await self.queue.put(( -message.priority.value, message ))
        print(f"[{self.head_id}] Message {message.message_id} queued with priority {message.priority.name}")

    async def start_worker(self):
        """Continuously process the message queue."""
        print(f"[{self.head_id}] Message router worker started")
        while True:
            prio, message = await self.queue.get()
            try:
                await self._deliver_message(message)
            except Exception as e:
                print(f"[{self.head_id}] Delivery failed for {message.message_id}: {e}")
            finally:
                self.queue.task_done()

    async def _deliver_message(self, message: ConstitutionalMessage):
        """Deliver message to recipients via sTLS."""
        for recipient in message.recipients:
            target_addr = self.routing_table.get(recipient)
            if not target_addr:
                print(f"[{self.head_id}] No route for {recipient}")
                continue

            # In a real impl, we'd use sTLS client connection.
            # For the local demo, we'll use aiohttp with our sTLS SSLContext.
            url = f"https://{target_addr}/message"
            
            # Create a custom TCPConnector with our sTLS context
            connector = aiohttp.TCPConnector(ssl=self.stls_ctx.context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, json=message.to_dict()) as resp:
                    if resp.status == 200:
                        print(f"[{self.head_id}] Message {message.message_id} delivered to {recipient}")
                        self._log_delivery_evidence(message, recipient, "delivered")
                    else:
                        print(f"[{self.head_id}] Delivery to {recipient} failed: {resp.status}")

    def _log_delivery_evidence(self, message: ConstitutionalMessage, recipient: str, status: str):
        out_dir = Path("evidence_store/connection")
        out_dir.mkdir(parents=True, exist_ok=True)
        ev_file = out_dir / f"delivery_{self.head_id}.jsonl"
        evidence = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message.message_id,
            "sender": self.head_id,
            "recipient": recipient,
            "status": status,
            "message_hash": message.generate_hash()
        }
        with ev_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evidence) + "\n")
