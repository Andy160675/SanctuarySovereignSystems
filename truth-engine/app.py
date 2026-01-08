from fastapi import FastAPI, HTTPException
from txtai.embeddings import Embeddings
import uvicorn
import os
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

app = FastAPI(title="Sovereign Truth Engine")

embeddings = Embeddings({
    "path": "nomic-ai/nomic-embed-text-v1.5",
    "content": True,
    "hybrid": True,
    "bm25": 0.7,
    "weights": {"id": 2.0}
})

index_path = "/app/data/elite-truth-index"
index_loaded = False

if os.path.exists(index_path):
    try:
        embeddings.load(index_path)
        index_loaded = True
    except Exception as e:
        print(f"Failed to load index: {e}")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
    # app.py is under <repo>/truth-engine/app.py
    return Path(__file__).resolve().parents[1]


def _git_head(repo_root: Path) -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root), stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace").strip()
    except Exception:
        return None


def _write_export_event(event: dict) -> None:
    """Export-only firewall: write local artifacts; never call cross-system services."""
    try:
        root = _repo_root()
        exports_dir = root / "exports" / "truth_engine"
        exports_dir.mkdir(parents=True, exist_ok=True)

        events_path = exports_dir / "truth_events.jsonl"
        meta_path = exports_dir / "truth_export_meta.json"

        with events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        files = []
        if events_path.exists():
            files.append({"path": str(events_path.relative_to(root)).replace("\\", "/"), "sha256": _sha256_file(events_path)})

        meta = {
            "schema_name": "blade2ai.truth_export",
            "schema_version": "1.0.0",
            "created_utc": _utc_now_iso(),
            "producer_commit": _git_head(root),
            "files": files,
        }

        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.write("\n")

    except Exception as e:
        # Export must never break runtime behavior
        print(f"Export write failed: {e}")


@app.get("/search")
def search(q: str, limit: int = 7):
    if not index_loaded:
        raise HTTPException(status_code=503, detail="Index not loaded")

    try:
        results = embeddings.search(q, limit)
        response = {
            "query": q,
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "total": len(results)
        }

        _write_export_event({
            "event_type": "search",
            "created_utc": _utc_now_iso(),
            "query": q,
            "limit": limit,
            "total": len(results),
        })

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {
        "status": "healthy" if index_loaded else "degraded",
        "index_loaded": index_loaded,
        "index_path": index_path,
        "timestamp": datetime.now().isoformat(),
        "version": "5.0.0"
    }


@app.get("/stats")
def stats():
    if not index_loaded:
        raise HTTPException(status_code=503, detail="Index not loaded")

    try:
        return {
            "index_loaded": index_loaded,
            "index_path": index_path,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
