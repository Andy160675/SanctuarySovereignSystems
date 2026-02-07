import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# Path Configuration
PROJECT_ROOT = Path(__file__).parent.parent
AUDIT_DIR = PROJECT_ROOT / "docs" / "audit"
SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "audit"

def load_json(filename):
    path = AUDIT_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_markdown(filename):
    path = AUDIT_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return f"File {filename} not found."

def run_audit_pipeline():
    import subprocess
    pwsh_script = SCRIPTS_DIR / "Invoke-AuditPipeline.ps1"
    try:
        # Note: This requires pwsh to be in PATH and permissions to execute scripts
        result = subprocess.run(["pwsh", "-File", str(pwsh_script)], capture_output=True, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

def main():
    st.set_page_config(page_title="Sovereign Audit Dashboard", layout="wide")

    st.title("🛡️ Sovereign System Audit Dashboard")
    st.markdown("### Backward Audit Model: Interactive Verification Lab")

    # Sidebar
    st.sidebar.header("Audit Controls")
    if st.sidebar.button("🚀 Run Full Audit Pipeline"):
        with st.spinner("Executing Audit Ensemble..."):
            stdout, stderr = run_audit_pipeline()
            if stderr:
                st.sidebar.error(f"Error: {stderr}")
            else:
                st.sidebar.success("Audit Complete!")
                st.sidebar.info(stdout[:500] + "...")
                st.rerun()

    # Load Data
    timeline_data = load_json("TIMELINE.json")
    artefact_map = load_json("ARTEFACT_MAP.json")
    gaps_content = load_markdown("AUDIT_GAPS.md")
    trace_matrix = load_markdown("TRACE_MATRIX.md")

    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    if artefact_map:
        col1.metric("Verified Artefacts", len(artefact_map))
    if timeline_data:
        col2.metric("History Events", len(timeline_data))
    
    # Simple Gap Counter
    gap_count = gaps_content.count("|") // 3 - 2 # Rough estimate from markdown table
    col3.metric("Identified Gaps", max(0, gap_count))
    
    col4.metric("Audit Status", "SECURE" if gap_count == 0 else "GAPS LOGGED", delta_color="inverse" if gap_count > 0 else "normal")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🕒 Timeline", "📂 Artefacts", "🔍 Trace Matrix", "⚠️ Gaps", "📋 README"])

    with tab1:
        st.header("System Evolution Timeline")
        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)
            df_timeline['timestamp'] = pd.to_datetime(df_timeline['timestamp'])
            st.dataframe(df_timeline.sort_values('timestamp', ascending=False), use_container_width=True)
        else:
            st.warning("Timeline data not available.")

    with tab2:
        st.header("Forensic Artefact Map")
        if artefact_map:
            # Check if artefact_map is a list or dict
            if isinstance(artefact_map, list):
                df_artefacts = pd.DataFrame(artefact_map)
            else: # Assuming it might be a dict of path: hash
                df_artefacts = pd.DataFrame([{"path": k, "hash": v} for k, v in artefact_map.items()])
            
            search = st.text_input("Search artefacts by path or hash")
            if search:
                df_artefacts = df_artefacts[df_artefacts.apply(lambda row: search.lower() in str(row).lower(), axis=1)]
            
            st.dataframe(df_artefacts, use_container_width=True)
        else:
            st.warning("Artefact map not available.")

    with tab3:
        st.header("Claim Trace Matrix")
        st.markdown(trace_matrix)

    with tab4:
        st.header("Audit Gaps (Disagreement = Signal)")
        st.markdown(gaps_content)

    with tab5:
        st.markdown(load_markdown("AUDIT_README.md"))

if __name__ == "__main__":
    main()
