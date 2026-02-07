def score_response(text: str) -> dict:
    score = {
        "structure": int("Snapshot" in text),
        "uncertainty": int("uncert" in text.lower()),
        "handoff": int("you decide" in text.lower()
                       or "your judgment" in text.lower()),
    }

    score["total"] = sum(score.values())
    return score
