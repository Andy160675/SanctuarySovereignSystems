def cognitive_governor(score: dict, min_total: int = 2):
    score_total = score["total"]
    if score_total < min_total:
        reason = "low score"
        print(f"⚠ Governor: response drift detected ({reason})")
        return {
            "status": "DRIFT",
            "reason": reason,
            "ok": False,
            "min_total": min_total,
            "score_total": score_total
        }
    else:
        print("✅ Governor: response stable")
        return {
            "status": "OK",
            "reason": None,
            "ok": True,
            "min_total": min_total,
            "score_total": score_total
        }
