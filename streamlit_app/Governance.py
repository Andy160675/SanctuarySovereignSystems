# -*- coding: utf-8 -*-
"""
Governance & Evidence Board - Streamlit Dashboard

Surfaces:
- Recent governance decisions
- Internal and external anchors
- Chain health status
- One-click evidence bundle export
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import streamlit as st

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.boardroom.anchoring import load_chain, verify_chain_integrity, get_chain_summary
from src.boardroom.external_anchor import ExternalAnchorConfig, get_supported_backends

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_ROOT = PROJECT_ROOT / "DATA"
COMMITS_DIR = DATA_ROOT / "_commits"
SNAPSHOTS_DIR = DATA_ROOT / "_work" / "snapshots"
CHAIN_FILE = DATA_ROOT / "_anchor_chain.json"
EXPORTS_DIR = PROJECT_ROOT / "exports"

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_decisions() -> List[Dict[str, Any]]:
    """Load all governance decisions from commits directory."""
    decisions = []
    if not COMMITS_DIR.exists():
        return decisions

    for f in sorted(COMMITS_DIR.glob("decision_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_file"] = f.name
            decisions.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    return decisions


def load_anchor_receipts() -> Dict[str, Dict[str, Any]]:
    """Load anchor receipts keyed by decision file."""
    receipts = {}
    if not COMMITS_DIR.exists():
        return receipts

    for f in COMMITS_DIR.glob("decision_*.anchor.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            # Key by corresponding decision file
            decision_file = f.name.replace(".anchor.json", ".json")
            receipts[decision_file] = data
        except (json.JSONDecodeError, IOError):
            continue

    return receipts


def get_chain_health() -> Dict[str, Any]:
    """Get chain health status."""
    chain = load_chain()
    if not chain:
        return {
            "status": "EMPTY",
            "length": 0,
            "integrity": None,
            "message": "No anchors in chain"
        }

    verification = verify_chain_integrity()
    is_valid = verification.get("valid", False)
    errors = verification.get("errors", [])
    summary = get_chain_summary()

    return {
        "status": "HEALTHY" if is_valid else "BROKEN",
        "length": summary.get("total_anchors", len(chain)),
        "integrity": is_valid,
        "errors": errors,
        "first_anchor": summary.get("genesis_timestamp"),
        "last_anchor": summary.get("latest_timestamp"),
        "message": "Chain integrity verified" if is_valid else f"Chain broken: {errors}"
    }


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------

def render_decision_card(decision: Dict[str, Any], anchor: Optional[Dict[str, Any]] = None):
    """Render a single decision card."""
    session_id = decision.get("session_id", "Unknown")
    outcome = decision.get("outcome", "UNKNOWN")
    timestamp = decision.get("committed_at", decision.get("timestamp", ""))

    # Outcome color
    if outcome == "APPROVED":
        outcome_color = "green"
        outcome_icon = "[APPROVED]"
    elif outcome == "REJECTED":
        outcome_color = "red"
        outcome_icon = "[REJECTED]"
    else:
        outcome_color = "orange"
        outcome_icon = f"[{outcome}]"

    with st.container():
        st.markdown(f"### {session_id}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Outcome:** :{outcome_color}[{outcome_icon}]")
        with col2:
            st.markdown(f"**Time:** {timestamp[:19] if timestamp else 'N/A'}")
        with col3:
            if anchor:
                st.markdown("**Anchored:** Yes")
            else:
                st.markdown("**Anchored:** No")

        # Gates summary
        gates = decision.get("gates", {})
        if gates:
            gate_status = []
            for gate, passed in gates.items():
                status = "PASS" if passed else "FAIL"
                gate_status.append(f"{gate}: {status}")
            st.markdown(f"**Gates:** {' | '.join(gate_status)}")

        # Merkle root
        merkle = decision.get("merkle", {})
        if merkle and merkle.get("root"):
            root = merkle["root"]
            st.code(f"Merkle Root: {root[:32]}...", language=None)

        # External anchor info
        ext_anchor = decision.get("external_anchor")
        if ext_anchor:
            backend = ext_anchor.get("backend", "unknown")
            dry_run = ext_anchor.get("dry_run", True)
            status = ext_anchor.get("status", "")

            ext_info = f"External: {backend.upper()}"
            if dry_run:
                ext_info += " (dry-run)"
            st.markdown(f"**{ext_info}** - {status}")

            # Show backend-specific info
            if backend == "rfc3161" and ext_anchor.get("rfc3161_token"):
                st.code(f"RFC3161 Token: {ext_anchor['rfc3161_token'][:40]}...", language=None)
            elif backend == "ipfs" and ext_anchor.get("ipfs_cid"):
                st.code(f"IPFS CID: {ext_anchor['ipfs_cid']}", language=None)
            elif backend == "arweave" and ext_anchor.get("arweave_tx_id"):
                st.code(f"Arweave TX: {ext_anchor['arweave_tx_id']}", language=None)

        # Expandable details
        with st.expander("Full Decision JSON"):
            st.json(decision)

        st.divider()


def render_chain_health(health: Dict[str, Any]):
    """Render chain health status."""
    status = health["status"]

    if status == "HEALTHY":
        st.success(f"Chain Status: HEALTHY - {health['length']} anchors")
    elif status == "EMPTY":
        st.info("Chain Status: EMPTY - No anchors yet")
    else:
        st.error(f"Chain Status: BROKEN - {health.get('message', 'Unknown error')}")

    if health.get("first_anchor"):
        st.markdown(f"**First anchor:** {health['first_anchor']}")
    if health.get("last_anchor"):
        st.markdown(f"**Last anchor:** {health['last_anchor']}")


def render_config_panel():
    """Render external anchor configuration panel."""
    st.subheader("External Anchor Configuration")

    config = ExternalAnchorConfig.load()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Backend:** {config.backend}")
        st.markdown(f"**Dry Run:** {config.dry_run}")
    with col2:
        st.markdown(f"**Enabled:** {'Yes' if config.is_enabled() else 'No'}")
        st.markdown(f"**Supported:** {', '.join(get_supported_backends())}")

    if config.backend == "rfc3161":
        st.markdown(f"**TSA URL:** {config.rfc3161_url or 'Not configured'}")
    elif config.backend == "ipfs":
        st.markdown(f"**Gateway:** {config.ipfs_gateway or 'Not configured'}")
    elif config.backend == "arweave":
        st.markdown(f"**Gateway:** {config.arweave_gateway or 'Not configured'}")


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Governance Board",
        page_icon="[G]",
        layout="wide"
    )

    st.title("Governance & Evidence Board")
    st.markdown("*Sovereign System - Decision Audit & External Anchoring*")

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        view = st.radio(
            "Select View",
            ["Decisions", "Chain Health", "Configuration", "Export"]
        )

        st.divider()

        # Quick stats
        decisions = load_decisions()
        health = get_chain_health()

        st.metric("Total Decisions", len(decisions))
        st.metric("Chain Length", health["length"])
        st.metric("Chain Status", health["status"])

    # Main content
    if view == "Decisions":
        st.header("Recent Governance Decisions")

        decisions = load_decisions()
        anchors = load_anchor_receipts()

        if not decisions:
            st.info("No governance decisions found.")
            st.markdown("""
            **To create a decision:**
            1. Run a boardroom session
            2. The decision will be committed to `DATA/_commits/`
            3. Refresh this page to see results
            """)
        else:
            for decision in decisions[:20]:  # Show last 20
                file_name = decision.get("_file", "")
                anchor = anchors.get(file_name)
                render_decision_card(decision, anchor)

    elif view == "Chain Health":
        st.header("Anchor Chain Health")

        health = get_chain_health()
        render_chain_health(health)

        st.divider()

        # Show chain details
        chain = load_chain()
        if chain:
            st.subheader(f"Chain Contents ({len(chain)} anchors)")

            for i, anchor in enumerate(chain[-10:]):  # Show last 10
                with st.expander(f"Anchor #{len(chain) - 10 + i + 1}: {anchor.get('file_path', 'unknown')[:50]}..."):
                    st.json(anchor)
        else:
            st.info("No anchors in chain yet.")

    elif view == "Configuration":
        st.header("System Configuration")

        render_config_panel()

        st.divider()

        st.subheader("Directory Structure")
        dirs = [
            ("Commits", COMMITS_DIR),
            ("Snapshots", SNAPSHOTS_DIR),
            ("Chain File", CHAIN_FILE),
            ("Exports", EXPORTS_DIR),
        ]

        for name, path in dirs:
            exists = path.exists()
            status = "EXISTS" if exists else "MISSING"
            color = "green" if exists else "red"
            st.markdown(f"**{name}:** `{path}` - :{color}[{status}]")

    elif view == "Export":
        st.header("Evidence Bundle Export")

        decisions = load_decisions()

        if not decisions:
            st.info("No decisions available for export.")
        else:
            st.markdown("Select a session to export as a sealed evidence bundle:")

            session_ids = [d.get("session_id", "unknown") for d in decisions]
            selected = st.selectbox("Session", session_ids)

            if st.button("Export Bundle"):
                with st.spinner("Creating evidence bundle..."):
                    try:
                        # Import and run export
                        from scripts.export_evidence_bundle import create_evidence_bundle

                        bundle_path = create_evidence_bundle(
                            selected,
                            EXPORTS_DIR,
                            verbose=False
                        )

                        if bundle_path and bundle_path.exists():
                            st.success(f"Bundle created: {bundle_path.name}")
                            st.markdown(f"**Size:** {bundle_path.stat().st_size:,} bytes")
                            st.markdown(f"**Location:** `{bundle_path}`")

                            # Offer download
                            with open(bundle_path, "rb") as f:
                                st.download_button(
                                    "Download Bundle",
                                    f.read(),
                                    file_name=bundle_path.name,
                                    mime="application/zip"
                                )
                        else:
                            st.error("Failed to create bundle - no files found for session")

                    except Exception as e:
                        st.error(f"Export failed: {e}")

            st.divider()

            # Show existing exports
            st.subheader("Existing Exports")
            if EXPORTS_DIR.exists():
                exports = list(EXPORTS_DIR.glob("evidence_bundle_*.zip"))
                if exports:
                    for exp in sorted(exports, reverse=True)[:10]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"`{exp.name}`")
                        with col2:
                            st.markdown(f"{exp.stat().st_size:,} bytes")
                else:
                    st.info("No exports found.")
            else:
                st.info("Exports directory not created yet.")


if __name__ == "__main__":
    main()
