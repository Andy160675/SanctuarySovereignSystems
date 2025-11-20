import sys
import os
import uuid
import json
import random
from pathlib import Path

# Add root to path
sys.path.append(os.getcwd())

from src.core.router import SovereignRouter

# Resolve Leads Directory
if os.path.exists("/data/property/Leads"):
    LEADS_DIR = Path("/data/property/Leads")
else:
    LEADS_DIR = Path("Property/Leads")

def mock_llm_analysis(text: str) -> dict:
    """
    Simulates an LLM analysis of the property text.
    In a real system, this would call an API.
    """
    text = text.lower()
    data = {
        "address": None,
        "asking_price": 0,
        "currency": "GBP",
        "condition_score": 8, # Default optimistic
        "risk_flags": [],
        "confidence": 0.7,
        "notes": "Automated extraction"
    }

    # Extract Address (Mock)
    if "sovereign rd" in text:
        data["address"] = "123 Sovereign Rd"
    elif "tonypandy" in text:
        data["address"] = "Near Tonypandy"
    
    # Extract Price (Mock)
    if "450,000" in text:
        data["asking_price"] = 450000
    
    # Extract Condition/Risks (Mock)
    if "modernization" in text:
        data["condition_score"] = 6
        data["notes"] = "Needs modernization"
    
    if "cracks" in text or "structural" in text:
        data["condition_score"] = 7 # INTENTIONAL ERROR for Calibration: High score despite defects
        data["risk_flags"].append("STRUCTURAL_RISK")
        data["notes"] = "Structural cracks visible"
    
    if "mold" in text or "rot" in text:
        data["condition_score"] = 6 # INTENTIONAL ERROR
        data["risk_flags"].append("BIOHAZARD")

    return data

def apply_guardrails(data: dict) -> dict:
    """
    Code-Level Guardrails (The "Brain Transplant" Logic)
    """
    # 1. Defects Cap
    # If ANY visual defect (cracks, mold, rot) is detected, condition_score MAX 5.
    defects = ["STRUCTURAL_RISK", "BIOHAZARD"]
    has_defects = any(flag in data.get("risk_flags", []) for flag in defects)
    
    if has_defects and data["condition_score"] > 5:
        print(f"   🛡️ GUARDRAIL TRIGGERED: Downgrading condition from {data['condition_score']} to 5 due to defects.")
        data["condition_score"] = 5
    
    return data

def run_analyst():
    # 1. Initialize Router
    try:
        router = SovereignRouter("property")
    except Exception as e:
        print(f"❌ FATAL: Router Init Failed: {e}")
        return

    print(f"🏘️  Property Analyst Online | Mode: {router.track.upper()}")

    # Ensure leads dir exists
    LEADS_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Process Leads
    files = [f for f in LEADS_DIR.iterdir() if f.is_file() and f.name.endswith(".txt")]
    
    if not files:
        print(f"   📭 No leads found in {LEADS_DIR}")
        return

    print(f"   Found {len(files)} leads to process...")

    for file_path in files:
        print(f"   Processing: {file_path.name}...")
        
        # Read Content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"     ❌ Read Failed: {e}")
            continue
        
        # LLM Analysis
        raw_data = mock_llm_analysis(content)
        
        # Apply Guardrails
        final_data = apply_guardrails(raw_data)

        # 3. Save via Router
        try:
            filename = f"{file_path.stem}.json"
            path = router.save_result(filename, final_data)
            print(f"     ✅ Draft Created: {path}")
        except Exception as e:
            print(f"     ❌ Failed: {e}")

if __name__ == "__main__":
    run_analyst()
