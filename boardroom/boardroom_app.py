#!/usr/bin/env python3
"""
Boardroom Streamlit app - Phase 5B (aggregated health + system setup + indexer)

Run:
  python -m venv .venv
  .venv\Scripts\Activate.ps1    # on Windows PowerShell
  pip install -r requirements.txt
  streamlit run boardroom_app.py --server.port 8501
"""
import time
import requests
import streamlit as st
from typing import Dict, Any

# --------- CONFIG ---------
AGGREGATED_HEALTH_URL = "http://localhost:8502/health"
AGGREGATED_INDEXER_URL = "http://localhost:8502/actions/index_truth"
TRINITY_SVC_HISTORY_URL = "http://localhost:8600/api/trinity/svc/history"
TRINITY_SVC_HEAD_URL = "http://localhost:8600/api/trinity/svc/head"
TRINITY_RUN_CASE_URL = "http://localhost:8600/api/trinity/run_case"
HEALTH_POLL_TIMEOUT = 2.0

# --------- HELPERS ---------
def fetch_aggregated_health(url: str, timeout: float = HEALTH_POLL_TIMEOUT) -> Dict[str, Any]:
    """Get aggregated health JSON from the backend."""
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}", "raw": resp.text}
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def post_indexer(url: str, payload: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
    """POST to the backend indexer endpoint."""
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        try:
            return {"ok": resp.ok, "status_code": resp.status_code, "data": resp.json()}
        except Exception:
            return {"ok": resp.ok, "status_code": resp.status_code, "data": resp.text}
    except Exception as e:
        return {"ok": False, "status_code": None, "data": {"error": str(e)}}


def status_badge(status: str):
    """Render a compact status badge."""
    s = (status or "").lower()
    if s in ("healthy", "pass", "configured"):
        st.markdown("**🟢 Healthy**")
    elif s in ("degraded", "unknown", "warning"):
        st.markdown("**🟡 Degraded**")
    elif s in ("fail", "down", "missing"):
        st.markdown("**🔴 Down**")
    else:
        st.markdown(f"**⚪ {status}**")


# --------- UI: System Setup & Live Status ---------
def render_system_setup(health_payload: Dict[str, Any]):
    st.title("System Setup - First Run")

    if "error" in health_payload:
        st.error(f"Cannot reach aggregated health endpoint: {health_payload['error']}")
        if st.button("Retry"):
            st.rerun()
        return

    overall = health_payload.get("overall_status", "degraded")
    checks = health_payload.get("checks", {})
    services = health_payload.get("services", {})

    if overall == "healthy":
        st.success("Organism status: HEALTHY")
    else:
        st.info("Organism status: needs attention - see checklist below")

    st.markdown("---")
    st.header("Smart Setup Checklist")

    key_order = ["env_file", "services_running", "ollama_model", "truth_index"]
    for k in key_order:
        v = checks.get(k)
        if not v:
            st.write(f"- {k}: (not reported)")
            continue
        status = v.get("status", "").lower()
        message = v.get("message") or v.get("msg") or str(v)
        col1, col2 = st.columns([4, 1])
        with col1:
            label = {
                "env_file": "Environment configured (.env)",
                "services_running": "Core services running",
                "ollama_model": "Ollama default model present",
                "truth_index": "Truth Engine indexed"
            }.get(k, k)
            st.write(f"**{label}**")
            st.caption(message)
        with col2:
            status_badge(status)

    st.markdown("---")

    truth_chk = checks.get("truth_index", {})
    truth_status = truth_chk.get("status", "").lower() if truth_chk else "unknown"
    if truth_status in ("fail", "unknown", "missing"):
        st.warning("Truth Engine appears to have no indexed data.")
        if st.button("Run Truth Indexer (sample)"):
            with st.spinner("Triggering indexer..."):
                out = post_indexer(AGGREGATED_INDEXER_URL, {"sample": True})
            if out.get("ok"):
                st.success("Indexer trigger accepted")
                st.json(out.get("data"))
            else:
                st.error("Indexer trigger failed")
                st.json(out.get("data"))
    else:
        st.info("Truth Engine index looks healthy.")
        if st.button("Re-run Truth Indexer (sample)"):
            with st.spinner("Triggering indexer..."):
                out = post_indexer(AGGREGATED_INDEXER_URL, {"sample": True})
            if out.get("ok"):
                st.success("Indexer trigger accepted")
                st.json(out.get("data"))
            else:
                st.error("Indexer trigger failed")
                st.json(out.get("data"))

    st.markdown("---")
    st.header("Live Service Status")
    cols = st.columns(3)
    i = 0
    if isinstance(services, dict) and services:
        for name, svc in services.items():
            col = cols[i % 3]
            with col:
                st.markdown(f"**{name}**")
                status = svc.get("status")
                status_badge(status)
                endpoint = svc.get("endpoint") or svc.get("url") or ""
                latency = svc.get("latency_ms")
                if latency is not None:
                    try:
                        st.caption(f"{latency:.0f} ms")
                    except Exception:
                        st.caption(f"{latency} ms")
                else:
                    st.caption("Check logs")
            i += 1
    else:
        st.info("No services reported by aggregated health endpoint.")

    st.markdown("---")
    colr, colm = st.columns([1, 3])
    with colr:
        if st.button("Refresh now"):
            st.rerun()
    with colm:
        st.write("Auto-refresh can be implemented in a later iteration.")


def render_dashboard_view(health_payload: Dict[str, Any]):
    st.title("Sovereign Boardroom - Dashboard")
    if "error" in health_payload:
        st.error(f"Cannot reach aggregated health endpoint: {health_payload['error']}")
        if st.button("Retry"):
            st.rerun()
        return

    overall = health_payload.get("overall_status", "degraded")
    if overall == "healthy":
        st.success("Organism status: HEALTHY")
    else:
        st.warning("Organism status: needs attention")

    col1, col2 = st.columns([3, 2])
    with col1:
        q = st.text_input("Global Truth Search", placeholder="Search evidence, policies, events...")
        if st.button("Search", key="dash_search"):
            st.info(f"(stub) Would search for: {q}")
    with col2:
        st.markdown("#### Quick Actions")
        if st.button("Analyze Text (Core)"):
            st.info("Use Core page for analysis.")
        if st.button("View Violations (Enforce)"):
            st.info("Use Enforce page for violations.")

    st.markdown("---")
    st.markdown("### System at a glance")
    services = health_payload.get("services", {})
    cols = st.columns(len(services) or 1)
    for (name, svc), col in zip(services.items(), cols):
        with col:
            st.markdown(f"**{name}**")
            status_badge(svc.get("status"))
            latency = svc.get("latency_ms")
            if latency is not None:
                st.caption(f"{latency:.0f} ms")
            else:
                st.caption("Latency: -")

    st.markdown("---")
    st.markdown("### Alerts & Activity (stub)")
    st.info("(stub) Alerts and recent events will be shown here in a later iteration.")


def render_core_page():
    st.title("Core - Analyze Text")
    text = st.text_area("Input text", height=200)
    if st.button("Analyze with Core"):
        st.info("(stub) send to Core API")


def render_truth_page():
    st.title("Truth - Search Evidence")
    q = st.text_input("Query")
    if st.button("Search Truth"):
        st.info("(stub) search truth")


def render_enforce_page():
    st.title("Enforce - Actions")
    action = st.selectbox("Action", ["quarantine", "flag", "redact"])
    subject = st.text_input("Subject")
    context = st.text_area("Context")
    if st.button("Send Enforcement"):
        st.info("(stub) send to Enforce API")


def fetch_svc_history() -> Dict[str, Any]:
    """Fetch SVC commit history from Trinity backend."""
    try:
        resp = requests.get(TRINITY_SVC_HISTORY_URL, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def fetch_svc_head() -> Dict[str, Any]:
    """Fetch HEAD commit from Trinity backend."""
    try:
        resp = requests.get(TRINITY_SVC_HEAD_URL, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def run_trinity_case(case_id: str, query: str) -> Dict[str, Any]:
    """Run a Trinity case and return results."""
    try:
        resp = requests.post(TRINITY_RUN_CASE_URL, json={"case_id": case_id, "query": query}, timeout=30.0)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
    except Exception as e:
        return {"error": str(e)}


def render_svc_page():
    """Render SVC (Sovereign Version Control) tab."""
    st.title("SVC - Sovereign Version Control")
    st.markdown("Immutable audit trail of all Trinity runs")

    st.markdown("---")

    # HEAD commit section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("HEAD Commit")
    with col2:
        if st.button("Refresh", key="svc_refresh"):
            st.rerun()

    head = fetch_svc_head()
    if "error" in head:
        st.warning(f"Cannot reach Trinity backend: {head['error']}")
        st.info("Make sure Trinity is running on port 8600")
    elif head.get("head") is None:
        st.info("No commits yet. Run a Trinity case to create the first commit.")
    else:
        commit = head.get("head", {})
        integrity = commit.get("integrity_status", "UNKNOWN")
        risk = commit.get("risk_lens", "unknown")

        # Status badges
        if integrity == "INTACT":
            st.success(f"Integrity: INTACT | Risk: {risk}")
        elif integrity == "COMPROMISED":
            st.error(f"Integrity: COMPROMISED | Risk: {risk}")
        else:
            st.warning(f"Integrity: {integrity} | Risk: {risk}")

        # Commit details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Case ID", commit.get("case_id", "-"))
        with col2:
            st.metric("Evidence", commit.get("evidence_count", 0))
        with col3:
            st.metric("Mismatches", commit.get("mismatch_count", 0))

        # Hash display
        commit_hash = commit.get("commit_hash", "")
        if commit_hash:
            st.code(f"Commit: {commit_hash[:16]}...", language=None)

        # Timestamp
        ts = commit.get("timestamp", "")
        if ts:
            st.caption(f"Timestamp: {ts}")

    st.markdown("---")

    # Run new case section
    st.subheader("Run Trinity Case")
    col1, col2 = st.columns([2, 1])
    with col1:
        case_id = st.text_input("Case ID", value="CASE-TEST-001")
        query = st.text_input("Query", value="evidence")
    with col2:
        st.write("")  # Spacer
        st.write("")
        if st.button("Run Case", type="primary"):
            with st.spinner("Running Trinity pipeline..."):
                result = run_trinity_case(case_id, query)

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                if result.get("success"):
                    st.success("Case completed successfully!")
                    summary = result.get("summary", {})
                    st.json({
                        "run_id": result.get("run_id"),
                        "integrity": summary.get("integrity_status"),
                        "risk_lens": summary.get("risk_lens"),
                        "evidence_found": summary.get("evidence_found"),
                        "action": summary.get("action_taken")
                    })
                else:
                    st.error("Case failed")
                    st.json(result)

    st.markdown("---")

    # Commit history section
    st.subheader("Commit History")
    history = fetch_svc_history()

    if "error" in history:
        st.warning(f"Cannot fetch history: {history['error']}")
    else:
        commits = history.get("commits", [])
        if not commits:
            st.info("No commits in history yet.")
        else:
            st.caption(f"Total commits: {len(commits)} | Chain valid: {history.get('chain_valid', '?')}")

            # Display commits as a table
            for i, commit in enumerate(commits[:20]):  # Show last 20
                is_head = (i == 0)
                integrity = commit.get("integrity_status", "?")
                risk = commit.get("risk_lens", "?")

                # Color based on integrity
                if integrity == "INTACT":
                    icon = "🟢"
                elif integrity == "COMPROMISED":
                    icon = "🔴"
                else:
                    icon = "🟡"

                with st.expander(
                    f"{icon} {commit.get('case_id', '?')} | {commit.get('timestamp', '?')[:19]} {'← HEAD' if is_head else ''}",
                    expanded=is_head
                ):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**Evidence:** {commit.get('evidence_count', 0)}")
                    with col2:
                        st.write(f"**Mismatches:** {commit.get('mismatch_count', 0)}")
                    with col3:
                        st.write(f"**Risk:** {risk}")
                    with col4:
                        st.write(f"**Action:** {commit.get('action_taken', '?')}")

                    commit_hash = commit.get("commit_hash", "")
                    if commit_hash:
                        st.code(commit_hash, language=None)

                    # LLM analysis if present
                    llm = commit.get("llm_analysis", {})
                    if llm:
                        st.caption("LLM Analysis:")
                        st.text(llm.get("inner_summary", ""))


def main():
    st.set_page_config(page_title="Sovereign Boardroom", layout="wide")

    if "page" not in st.session_state:
        st.session_state["page"] = "first_run"

    health_payload = fetch_aggregated_health(AGGREGATED_HEALTH_URL)

    st.sidebar.title("System Status (Live)")
    if "error" in health_payload:
        st.sidebar.error("Aggregated health unavailable")
        if st.sidebar.button("Retry"):
            st.rerun()
    else:
        services = health_payload.get("services", {})
        for name, svc in services.items():
            col1, col2 = st.sidebar.columns([2, 1])
            with col1:
                st.sidebar.write(name)
            with col2:
                status = svc.get("status", "down")
                s = status.lower()
                if s == "healthy":
                    st.sidebar.markdown("🟢")
                elif s in ("degraded", "unknown"):
                    st.sidebar.markdown("🟡")
                else:
                    st.sidebar.markdown("🔴")

    st.sidebar.markdown("---")
    choice = st.sidebar.radio("Navigate", ["System Setup", "Dashboard", "Core", "Truth", "Enforce", "SVC"],
                              index=0 if st.session_state["page"] == "first_run" else 1)

    if choice == "System Setup":
        st.session_state["page"] = "first_run"
        render_system_setup(health_payload)
    elif choice == "Dashboard":
        st.session_state["page"] = "dashboard"
        render_dashboard_view(health_payload)
    elif choice == "Core":
        st.session_state["page"] = "core"
        render_core_page()
    elif choice == "Truth":
        st.session_state["page"] = "truth"
        render_truth_page()
    elif choice == "Enforce":
        st.session_state["page"] = "enforce"
        render_enforce_page()
    elif choice == "SVC":
        st.session_state["page"] = "svc"
        render_svc_page()


if __name__ == "__main__":
    main()
