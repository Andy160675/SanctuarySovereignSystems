from datetime import datetime
import csv
import os
import json

LOG_DIR = os.path.join("validation", "assistive_lab")
CSV_LOG = os.path.join(LOG_DIR, "lab_log.csv")
JSONL_LOG = os.path.join(LOG_DIR, "lab_runs.jsonl")

def log_run(model, score):
    os.makedirs(LOG_DIR, exist_ok=True)
    file_exists = os.path.isfile(CSV_LOG)
    with open(CSV_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Model", "Score"])
        writer.writerow([
            datetime.now().isoformat(),
            model,
            score["total"]
        ])

def log_event(event_data):
    os.makedirs(LOG_DIR, exist_ok=True)
    event_data["timestamp"] = datetime.now().isoformat()
    with open(JSONL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_data) + "\n")
