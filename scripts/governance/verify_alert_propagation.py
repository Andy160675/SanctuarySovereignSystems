import argparse
import json
import os
from typing import List

ACKS_DIR = os.path.join("Governance", "alerts", "acks")


def load_required_nodes(path: str) -> List[str]:
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
        elif isinstance(data, dict) and "nodes" in data and isinstance(data["nodes"], list):
            return [str(x) for x in data["nodes"]]
        else:
            raise ValueError("Expected a JSON list or {\"nodes\": [...]} structure")


def main():
    parser = argparse.ArgumentParser(description="Verify that an Alert Update has been acknowledged by required nodes.")
    parser.add_argument("alert_id", help="Alert Update identifier")
    parser.add_argument("--required-nodes", dest="required_nodes", help="Path to JSON file listing required node IDs")

    args = parser.parse_args()
    required = load_required_nodes(args.required_nodes)

    ack_dir = os.path.join(ACKS_DIR, args.alert_id)
    if not os.path.isdir(ack_dir):
        print(f"No acknowledgements found for alert {args.alert_id}.")
        if required:
            print("Missing acks for:", ", ".join(required))
            raise SystemExit(1)
        else:
            raise SystemExit(0)

    present = {os.path.splitext(f)[0] for f in os.listdir(ack_dir) if f.endswith('.json')}

    missing = [n for n in required if n not in present]
    if missing:
        print(f"Alert {args.alert_id}: missing acknowledgements for: {', '.join(missing)}")
        raise SystemExit(1)

    print(f"Alert {args.alert_id}: acknowledgements present for {len(present)} node(s).")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
