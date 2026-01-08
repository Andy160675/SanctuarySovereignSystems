from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
try:
    from txtai.embeddings import Embeddings
    _TXT_AI_IMPORT_ERROR = None
except Exception as e:
    Embeddings = None
    _TXT_AI_IMPORT_ERROR = str(e)
import uvicorn
import os
import json
import hashlib
import subprocess
import time
from collections import deque
from threading import Lock
from datetime import datetime, timezone
from pathlib import Path

app = FastAPI(title="Sovereign Truth Engine")

embeddings = None
if Embeddings is not None:
    embeddings = Embeddings({
        "path": "nomic-ai/nomic-embed-text-v1.5",
        "content": True,
        "hybrid": True,
        "bm25": 0.7,
        "weights": {"id": 2.0}
    })

index_path = "/app/data/elite-truth-index"
index_loaded = False

if embeddings is not None and os.path.exists(index_path):
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


_SEARCH_RATE_LIMIT_PER_MINUTE = 30
_search_request_times = deque()
_search_rate_lock = Lock()


def _rate_limit_search() -> bool:
    """Returns True if the request should be rate-limited (process-local)."""
    now = time.time()
    cutoff = now - 60.0
    with _search_rate_lock:
        while _search_request_times and _search_request_times[0] < cutoff:
            _search_request_times.popleft()

        if len(_search_request_times) >= _SEARCH_RATE_LIMIT_PER_MINUTE:
            return True

        _search_request_times.append(now)
        return False


def _search_error(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": error_code, "message": message}})


@app.get("/search")
def search(q: str | None = None, limit: str | None = "7"):
    created_utc = _utc_now_iso()

    raw_query = "" if q is None else q
    query = raw_query.strip()

    try:
        parsed_limit = int(limit) if limit is not None else 7
    except Exception:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": query,
            "limit": 0,
            "outcome": "bad_request",
            "total": 0,
            "error_code": "BAD_LIMIT",
        }
        _write_export_event(event)
        return _search_error(400, "BAD_LIMIT", "limit must be an integer")

    # Deterministic bounds
    if len(query) < 1 or len(query) > 512:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": query,
            "limit": max(1, min(parsed_limit, 25)),
            "outcome": "bad_request",
            "total": 0,
            "error_code": "BAD_QUERY",
        }
        _write_export_event(event)
        return _search_error(400, "BAD_QUERY", "q must be 1-512 characters")

    # Clamp limit to 1–25
    normalized_limit = max(1, min(parsed_limit, 25))

    # Minimal spam guard (process-local)
    if _rate_limit_search():
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": query,
            "limit": normalized_limit,
            "outcome": "rate_limited",
            "total": 0,
            "error_code": "RATE_LIMITED",
        }
        _write_export_event(event)
        return _search_error(429, "RATE_LIMITED", "too many requests")

    if embeddings is None:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": query,
            "limit": normalized_limit,
            "outcome": "unavailable",
            "total": 0,
            "error_code": "TXT_AI_UNAVAILABLE",
        }
        _write_export_event(event)
        return _search_error(503, "TXT_AI_UNAVAILABLE", "txtai not available")

    if not index_loaded:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": query,
            "limit": normalized_limit,
            "outcome": "unavailable",
            "total": 0,
            "error_code": "INDEX_NOT_LOADED",
        }
        _write_export_event(event)
        return _search_error(503, "INDEX_NOT_LOADED", "index not loaded")

    try:
        results = embeddings.search(query, normalized_limit)
        total = len(results) if results is not None else 0

        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": query,
            "limit": normalized_limit,
            "outcome": "ok",
            "total": total,
            "error_code": None,
        }
        _write_export_event(event)

        return {
            "query": query,
            "results": results,
            "timestamp": _utc_now_iso(),
            "total": total,
        }
    except Exception:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": query,
            "limit": normalized_limit,
            "outcome": "error",
            "total": 0,
            "error_code": "INTERNAL_ERROR",
        }
        _write_export_event(event)
        return _search_error(500, "INTERNAL_ERROR", "internal error")


@app.get("/health")
def health():
    return {
        "status": "healthy" if index_loaded else "degraded",
        "index_loaded": index_loaded,
        "index_path": index_path,
        "txtai_available": embeddings is not None,
        "txtai_import_error": _TXT_AI_IMPORT_ERROR,
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
