# -*- coding: utf-8 -*-
"""
Sovereign System - Home Page

Main entry point for the Streamlit governance cockpit.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.boardroom.anchoring import load_chain, verify_chain_integrity, get_chain_summary
from src.boardroom.chain_governed_verify import run_governed_chain_verification


def get_quick_health() -> dict:
    """Quick health check for status display."""
    chain = load_chain()
    if not chain:
        return {"status": "EMPTY", "length": 0, "valid": None}

    verification = verify_chain_integrity()
    is_valid = verification.get("valid", False)
    return {
        "status": "VALID" if is_valid else "INVALID",
        "length": len(chain),
        "valid": is_valid
    }


def main():
    st.set_page_config(
        page_title="Sovereign System",
        page_icon="[S]",
        layout="wide"
    )

    # Global chain health indicator (heartbeat)
    health = get_quick_health()

    # Top bar with chain status
    col1, col2, col3 = st.columns([6, 2, 2])
    with col1:
        st.title("Sovereign System")
    with col2:
        if health["status"] == "VALID":
            st.success(f"Chain: VALID ({health['length']})")
        elif health["status"] == "EMPTY":
            st.info("Chain: EMPTY")
        else:
            st.error("Chain: INVALID")
    with col3:
        if st.button("Verify Now (Governed)"):
            with st.spinner("Creating governed verification..."):
                result = run_governed_chain_verification(
                    requested_by="ui:operator",
                    rationale="Manual chain verification from Governance Cockpit.",
                )
                status = result.get("verification_status")
                if status is True or status == "VALID":
                    st.success("Verified!")
                    if result.get("verification_summary"):
                        st.caption(f"Anchors: {result['verification_summary'].get('verified_anchors')}/{result['verification_summary'].get('total_anchors')}")
                else:
                    st.error(f"Failed: {result.get('verification_summary', {}).get('errors', 0)} errors")
                st.caption(f"Decision: {result.get('session_id')}")

    st.divider()

    st.markdown("""
    ## Institutional Governance Cockpit

    This is the control surface for the sovereign system - a self-governing machine
    with cryptographic memory, external witness capability, and full audit transparency.

    ---

    ### System Components

    | Component | Purpose | Status |
    |-----------|---------|--------|
    | **Boardroom 13** | 13-role deliberation harness | Active |
    | **Governance Gate** | Hard gates: evidence, ethics, legal, security, consensus | Active |
    | **Hash Chain** | Cryptographic continuity spine | Active |
    | **External Anchor** | Third-party witness (RFC3161/IPFS/Arweave) | Configured |
    | **Automation Driver** | Post-commit action dispatch | Active |
    | **Evidence Exporter** | Forensic bundle generation | Active |

    ---

    ### Navigation

    Use the sidebar or links below to access system views:

    - **Governance Board** - View decisions, anchors, and chain health
    - **Export Evidence** - Generate sealed forensic bundles
    - **Configuration** - System settings and directory status

    ---

    ### Quick Stats
    """)

    # Quick stats in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Chain Length", health["length"])

    with col2:
        chain_status = "Valid" if health["valid"] else ("Empty" if health["valid"] is None else "Invalid")
        st.metric("Chain Status", chain_status)

    # Count decisions
    commits_dir = PROJECT_ROOT / "DATA" / "_commits"
    decision_count = len(list(commits_dir.glob("decision_*.json"))) if commits_dir.exists() else 0

    with col3:
        st.metric("Decisions", decision_count)

    # Count exports
    exports_dir = PROJECT_ROOT / "exports"
    export_count = len(list(exports_dir.glob("evidence_bundle_*.zip"))) if exports_dir.exists() else 0

    with col4:
        st.metric("Exports", export_count)

    st.divider()

    st.markdown("""
    ### Architecture Overview

    ```
    +-----------------+     +------------------+     +------------------+
    |  Boardroom 13   | --> | Governance Gate  | --> |   Hash Chain     |
    | (Deliberation)  |     | (Hard Gates)     |     | (Audit Spine)    |
    +-----------------+     +------------------+     +------------------+
                                    |                        |
                                    v                        v
                            +------------------+     +------------------+
                            | Automation       |     | External Anchor  |
                            | (Consequences)   |     | (Witness Layer)  |
                            +------------------+     +------------------+
                                    |                        |
                                    v                        v
                            +------------------+     +------------------+
                            | Pipelines        |     | Evidence Export  |
                            | (POC/Data/Ops)   |     | (Forensic Bundles)|
                            +------------------+     +------------------+
    ```

    ---

    ### Constitutional Properties

    1. **Sovereign Truth**: Internal memory cannot be quietly rewritten
    2. **External Non-Repudiation**: Third parties can verify existence timestamps
    3. **Hard Gate Enforcement**: No action without evidence, ethics, legal, security, consensus
    4. **Full Traceability**: Every decision has a Merkle receipt and chain position
    5. **Forensic Readiness**: Any decision can be exported as a sealed bundle

    ---

    *"The organism remembers what it did, can prove it didn't rewrite history,
    and a third party can confirm when that memory existed."*
    """)


if __name__ == "__main__":
    main()
