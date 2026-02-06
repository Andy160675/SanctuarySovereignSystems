import argparse
import json
import os
from datetime import datetime, timezone
from Governance.ledger.decision_ledger import DecisionLedger

ALERTS_DIR = os.path.join("Governance", "alerts")


def iso_utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_alert(alert: dict) -> str:
    os.makedirs(ALERTS_DIR, exist_ok=True)
    alert_id = alert["alert_id"]
    path = os.path.join(ALERTS_DIR, f"{alert_id}.json")
    # Deterministic ordering
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(alert, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return path


def main():
    parser = argparse.ArgumentParser(description="Broadcast an Alert Update to all nodes.")
    parser.add_argument("--payload", help="Path to Alert Update JSON payload (conforms to schema)")
    parser.add_argument("--alert-id", dest="alert_id", help="Override/Provide alert_id")
    parser.add_argument("--incident-id", dest="incident_id")
    parser.add_argument("--observed", dest="observed")
    parser.add_argument("--boundary", dest="boundary")
    parser.add_argument("--change-type", dest="change_type", choices=["rule_update","guard_patch","constraint_change","policy_update","config_change"])
    parser.add_argument("--change-summary", dest="change_summary")
    parser.add_argument("--effective-ts", dest="effective_ts")
    parser.add_argument("--required-action", dest="required_actions", action="append", default=[])
    parser.add_argument("--origin-node", dest="origin_node")

    args = parser.parse_args()

    if args.payload and os.path.exists(args.payload):
        with open(args.payload, "r", encoding="utf-8") as f:
            alert = json.load(f)
    else:
        # Build from flags
        missing = [k for k in ["alert_id","incident_id","observed","boundary","change_type","change_summary","origin_node"] if getattr(args, k if k!="observed" else "observed") is None]
        if missing:
            parser.error(f"Missing required fields to construct alert: {', '.join(missing)} or provide --payload")
        alert = {
            "alert_id": args.alert_id,
            "incident_id": args.incident_id,
            "observed_at_gemba": args.observed,
            "boundary": args.boundary,
            "change": {
                "type": args.change_type,
                "summary": args.change_summary
            },
            "effective_ts": args.effective_ts or iso_utc_now(),
            "required_local_actions": args.required_actions,
            "origin_node": args.origin_node,
            "version": "1"
        }

    path = write_alert(alert)

    # Log broadcast to decision ledger
    DecisionLedger.log(
        decision="ALERT_UPDATE_BROADCAST",
        metadata={
            "alert_id": alert["alert_id"],
            "boundary": alert.get("boundary"),
            "incident_id": alert.get("incident_id"),
            "origin_node": alert.get("origin_node"),
            "effective_ts": alert.get("effective_ts"),
            "alert_path": path
        }
    )

    print(f"Broadcasted Alert Update: {alert['alert_id']} -> {path}")


if __name__ == "__main__":
    main()
