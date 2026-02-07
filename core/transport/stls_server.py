"""
core/transport/stls_server.py

Sovereign TLS (sTLS) server implementation using aiohttp for constitutional mTLS.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import ssl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from aiohttp import web


class SovereignTLSServer:
    """sTLS server with constitutional enforcement."""

    def __init__(self, head_id: str, port: int, allowed_roles: List[str], pki_dir: Optional[Path] = None):
        self.head_id = head_id
        self.port = port
        self.allowed_roles = allowed_roles
        self.pki_dir = pki_dir or Path("evidence_store/pki")
        self.app = web.Application()
        self.setup_routes()
        self.runner: Optional[web.AppRunner] = None

    def setup_routes(self):
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_post("/evidence", self.submit_evidence)
        self.app.router.add_post("/message", self.handle_message)

    def _create_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        
        # Load server cert and key
        ctx.load_cert_chain(
            certfile=str(self.pki_dir / f"{self.head_id}.pem"),
            keyfile=str(self.pki_dir / f"{self.head_id}.key"),
        )
        
        # Load CA for client auth
        ctx.load_verify_locations(cafile=str(self.pki_dir / "root-ca.crt"))
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    async def start(self):
        ssl_ctx = self._create_ssl_context()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", self.port, ssl_context=ssl_ctx)
        await site.start()
        print(f"sTLS Server [{self.head_id}] started on 127.0.0.1:{self.port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    async def health_check(self, request: web.Request) -> web.Response:
        return web.json_response({
            "status": "healthy",
            "head": self.head_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def submit_evidence(self, request: web.Request) -> web.Response:
        data = await request.json()
        # Log evidence arrival
        print(f"[{self.head_id}] Evidence received: {data.get('type')}")
        return web.json_response({"received": True})

    async def handle_message(self, request: web.Request) -> web.Response:
        data = await request.json()
        peer_cert = request.transport.get_extra_info('ssl_object').getpeercert()
        remote_cn = None
        if peer_cert:
            for tup in peer_cert.get('subject', []):
                for k, v in tup:
                    if k == 'commonName':
                        remote_cn = v
                        break

        # Log connection evidence
        self._log_connection_evidence(remote_cn, "message_received", data.get('message_id'))

        print(f"[{self.head_id}] Message received from {data.get('sender')} (CN: {remote_cn})")
        return web.json_response({"status": "delivered", "head": self.head_id})

    def _log_connection_evidence(self, remote_cn: Optional[str], event: str, message_id: Optional[str]):
        out_dir = Path("evidence_store/connection")
        out_dir.mkdir(parents=True, exist_ok=True)
        ev_file = out_dir / f"server_{self.head_id}.jsonl"
        evidence = {
            "timestamp": datetime.utcnow().isoformat(),
            "head": self.head_id,
            "remote_cn": remote_cn,
            "event": event,
            "message_id": message_id
        }
        with ev_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evidence) + "\n")
