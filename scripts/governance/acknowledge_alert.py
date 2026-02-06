import argparse
import json
import os
from datetime import datetime, timezone
from Governance.ledger.decision_ledger import DecisionLedger

ACKS_DIR = os.path.join("Governance", "alerts", "acks")


def iso_utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_ack(alert_id: str, node_id: str, ack: dict) -> str:
    path_dir = os.path.join(ACKS_DIR, alert_id)
    os.makedirs(path_dir, exist_ok=True)
    path = os.path.join(path_dir, f"{node_id}.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ack, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return path


def main():
    parser = argparse.ArgumentParser(description="Acknowledge receipt and application of an Alert Update.")
    parser.add_argument("alert_id", help="Alert Update identifier")
    parser.add_argument("--node-id", dest="node_id", default=os.environ.get("NODE_ID", "UNKNOWN"))
    parser.add_argument("--applied", dest="applied", action="store_true", help="Set if guard/rule was applied")
    parser.add_argument("--note", dest="note", help="Optional note")

    args = parser.parse_args()
    ts = iso_utc_now()

    ack = {
        "alert_id": args.alert_id,
        "node_id": args.node_id,
        "ack_ts": ts,
        "applied": bool(args.applied),
        "note": args.note or ""
    }

    path = write_ack(args.alert_id, args.node_id, ack)

    DecisionLedger.log(
        decision="ALERT_ACK",
        metadata={
            "alert_id": args.alert_id,
            "node_id": args.node_id,
            "applied": bool(args.applied),
            "ack_path": path,
            "ack_ts": ts
        }
    )

    print(f"Acknowledged Alert {args.alert_id} @ {args.node_id} -> {path}")


if __name__ == "__main__":
    main()
