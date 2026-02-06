#!/usr/bin/env python3
"""
Sovereign Self-Heal Monitor
Generates/updates evidence/SITREP.md with live node reachability status.

Usage:
    python tools/self_heal_monitor.py --write-sitrep

Features:
    - Per-node reachability check (🟢 ONLINE / 🔴 UNREACHABLE)
    - Preserves existing Version: and Seal manifest: lines
    - UTC timestamp on every update
"""

import sys
import socket
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import re

SITREP_PATH = Path("evidence/SITREP.md")
NODES_CONFIG = Path("CONFIG/nodes.yaml")

# Default nodes if config not found
DEFAULT_NODES = [
    {"name": "localhost", "host": "127.0.0.1", "port": 22},
]

def load_nodes():
    """Load node configuration or use defaults."""
    if NODES_CONFIG.exists():
        try:
            import yaml
            config = yaml.safe_load(NODES_CONFIG.read_text())
            return config.get("nodes", DEFAULT_NODES)
        except:
            pass
    return DEFAULT_NODES

def check_node_reachable(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a node is reachable via TCP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_node_status(nodes: list) -> list:
    """Check status of all nodes."""
    results = []
    for node in nodes:
        name = node.get("name", "unknown")
        host = node.get("host", "127.0.0.1")
        port = node.get("port", 22)
        reachable = check_node_reachable(host, port)
        results.append({
            "name": name,
            "host": host,
            "port": port,
            "status": "🟢 ONLINE" if reachable else "🔴 UNREACHABLE"
        })
    return results

def preserve_metadata(existing_content: str) -> dict:
    """Extract Version and Seal manifest lines to preserve."""
    metadata = {}
    
    version_match = re.search(r'^Version:\s*(.+)$', existing_content, re.MULTILINE)
    if version_match:
        metadata['version'] = version_match.group(0)
    
    seal_match = re.search(r'^- Seal manifest:\s*(.+)$', existing_content, re.MULTILINE)
    if seal_match:
        metadata['seal'] = seal_match.group(0)
    
    return metadata

def write_sitrep(node_status: list, metadata: dict = None):
    """Write SITREP.md with current status."""
    SITREP_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        "# SOVEREIGN SYSTEM SITREP",
        "",
        f"**Last Updated:** {timestamp}",
        "",
    ]
    
    # Preserve version if exists
    if metadata and 'version' in metadata:
        lines.append(metadata['version'])
        lines.append("")
    
    lines.extend([
        "## Node Status",
        "",
        "| Node | Host | Port | Status |",
        "|------|------|------|--------|",
    ])
    
    for node in node_status:
        lines.append(f"| {node['name']} | {node['host']} | {node['port']} | {node['status']} |")
    
    lines.extend([
        "",
        "## System Health",
        "",
    ])
    
    online_count = sum(1 for n in node_status if "ONLINE" in n['status'])
    total_count = len(node_status)
    health_pct = (online_count / total_count * 100) if total_count > 0 else 0
    
    lines.append(f"- **Nodes Online:** {online_count}/{total_count} ({health_pct:.0f}%)")
    lines.append(f"- **Overall Status:** {'✅ HEALTHY' if health_pct >= 80 else '⚠️ DEGRADED' if health_pct >= 50 else '❌ CRITICAL'}")
    
    # Preserve seal manifest if exists
    if metadata and 'seal' in metadata:
        lines.extend(["", "## Seals", "", metadata['seal']])
    
    lines.append("")
    
    SITREP_PATH.write_text("\n".join(lines))
    print(f"✅ SITREP updated: {SITREP_PATH}")

def main():
    parser = argparse.ArgumentParser(description="Sovereign Self-Heal Monitor")
    parser.add_argument("--write-sitrep", action="store_true", help="Write/update SITREP.md")
    parser.add_argument("--check-only", action="store_true", help="Check nodes without writing")
    args = parser.parse_args()
    
    print("=" * 50)
    print("SOVEREIGN SELF-HEAL MONITOR")
    print("=" * 50)
    
    nodes = load_nodes()
    print(f"\nChecking {len(nodes)} node(s)...")
    
    status = get_node_status(nodes)
    
    for node in status:
        print(f"  {node['name']}: {node['status']}")
    
    if args.write_sitrep:
        metadata = {}
        if SITREP_PATH.exists():
            metadata = preserve_metadata(SITREP_PATH.read_text())
        write_sitrep(status, metadata)
    
    print("=" * 50)

if __name__ == "__main__":
    main()
