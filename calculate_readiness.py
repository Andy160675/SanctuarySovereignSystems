import json
import os
from datetime import datetime
from collections import deque

# --- CONFIGURATION ---
LOG_FILE = r"c:\sovereign-system\Governance\Logs\audit-insider.jsonl"
REPORT_FILE = "readiness_report.json"

# The "Gate" Criteria
THRESHOLDS = {
    "evidence-validator": {
        "window_size": 50,       # Look at last 50 reviews
        "min_accuracy": 0.95,    # Must have 95% acceptance rate
        "min_samples": 10        # Don't promote until at least 10 reviews
    },
    "property-analyst": {
        "window_size": 30,
        "min_accuracy": 0.90,
        "min_samples": 10
    }
    # Add new agents here as you build them
}

def load_logs(filepath):
    """Reads the JSONL audit log."""
    if not os.path.exists(filepath):
        print(f"⚠️  Log file not found: {filepath}")
        return []
    
    entries = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

def calculate_metrics(logs):
    """Calculates acceptance rate per agent based on rolling window."""
    
    # Group logs by agent (using a deque to keep only the rolling window)
    agent_data = {}
    
    for entry in logs:
        # Identify agent from filename or version tag
        # Assuming filename convention: "evidence-..." or "property-..."
        filename = entry.get('filename', '')
        if 'evidence' in filename.lower():
            agent_name = 'evidence-validator'
        elif 'property' in filename.lower():
            agent_name = 'property-analyst'
        else:
            continue # Skip unknown files
            
        if agent_name not in agent_data:
            agent_data[agent_name] = []
            
        agent_data[agent_name].append(entry)

    report = {}

    for agent, history in agent_data.items():
        config = THRESHOLDS.get(agent, {"window_size": 50, "min_accuracy": 0.95, "min_samples": 10})
        window = config['window_size']
        
        # Slice to get only the last N entries (The Rolling Window)
        recent_history = history[-window:]
        
        total_samples = len(recent_history)
        approvals = sum(1 for e in recent_history if e['decision'] == 'APPROVE')
        rejections = sum(1 for e in recent_history if e['decision'] == 'REJECT')
        
        accuracy = approvals / total_samples if total_samples > 0 else 0.0
        
        # Determine Status
        is_ready = (
            total_samples >= config['min_samples'] and 
            accuracy >= config['min_accuracy']
        )

        report[agent] = {
            "status": "READY_FOR_PROMOTION" if is_ready else "CALIBRATING",
            "metrics": {
                "accuracy": round(accuracy, 3),
                "target_accuracy": config['min_accuracy'],
                "samples_collected": total_samples,
                "samples_needed": config['min_samples'],
                "approvals": approvals,
                "rejections": rejections
            },
            "last_updated": datetime.now().isoformat()
        }

    return report

def main():
    print("📊 Analyzing Insider Audit Logs...")
    logs = load_logs(LOG_FILE)
    
    if not logs:
        print("   No logs found. Deploy agents to Insider to generate data.")
        return

    report = calculate_metrics(logs)
    
    # Output to JSON
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Console Summary
    print(f"\n📝 Report generated: {REPORT_FILE}\n")
    for agent, data in report.items():
        status_icon = "✅" if data['status'] == "READY_FOR_PROMOTION" else "🚧"
        acc_pct = data['metrics']['accuracy'] * 100
        print(f"{status_icon} {agent.upper()}")
        print(f"   Status: {data['status']}")
        print(f"   Accuracy: {acc_pct}% ({data['metrics']['approvals']}/{data['metrics']['samples_collected']})")
        print(f"   Threshold: {data['metrics']['target_accuracy'] * 100}%")
        print("-" * 30)

if __name__ == "__main__":
    main()