#!/bin/bash
# Sovereign System V3 - One-Click Demo
# Tag: v3.0.0-complete

echo ""
echo "  ============================================================"
echo "   SOVEREIGN SYSTEM V3 - One-Click Demo"
echo "   Tag: v3.0.0-complete"
echo "  ============================================================"
echo ""

cd "$(dirname "$0")"

# Check Python
echo "  [1/4] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "  ERROR: Python not found. Please install Python 3.10+"
    exit 1
fi
python3 --version
echo "        Python OK"

# Check Streamlit
echo ""
echo "  [2/4] Checking Streamlit..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "        Installing Streamlit..."
    pip3 install streamlit
fi
echo "        Streamlit OK"

# Check project modules
echo ""
echo "  [3/4] Checking project modules..."
if ! python3 -c "from src.boardroom.anchoring import load_chain" 2>/dev/null; then
    echo "  ERROR: Project modules not found. Run from repo root."
    exit 1
fi
echo "        Modules OK"

# Launch
echo ""
echo "  [4/4] Launching Governance Cockpit..."
echo ""
echo "  ============================================================"
echo "   Opening browser at http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo "  ============================================================"
echo ""

# Try to open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501 &
elif command -v open &> /dev/null; then
    open http://localhost:8501 &
fi

streamlit run streamlit_app/Home.py --server.headless true
