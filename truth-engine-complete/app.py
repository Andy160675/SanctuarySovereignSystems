"""
Truth Engine - txtai-based RAG/Search Backend
Sovereign System - Phase 3 Module 2
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
try:
    from txtai.embeddings import Embeddings
    _TXT_AI_IMPORT_ERROR = None
except Exception as e:
    Embeddings = None
    _TXT_AI_IMPORT_ERROR = str(e)
from typing import List, Optional
import os
import json
import hashlib
import subprocess
import time
from collections import deque
from threading import Lock
from datetime import datetime, timezone
from pathlib import Path

app = FastAPI(title="Truth Engine", version="0.1.0")

# Enable CORS for Boardroom Shell
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Electron app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize txtai embeddings
embeddings = None
if Embeddings is not None:
    embeddings = Embeddings({
        "method": "sentence-transformers",
        "path": "sentence-transformers/all-MiniLM-L6-v2",
        "content": True
    })

# Index storage path
INDEX_PATH = os.path.join(os.path.dirname(__file__), "data", "index")

# In-memory document store (will be persisted)
documents = []


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
    # app.py is under <repo>/truth-engine-complete/app.py
    return Path(__file__).resolve().parents[1]


def _git_head(repo_root: Path) -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root), stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace").strip()
    except Exception:
        return None


_event_seq = 0
_event_seq_lock = Lock()


def _next_event_seq() -> int:
    global _event_seq
    with _event_seq_lock:
        _event_seq += 1
        return _event_seq


def _compute_event_id(*, producer_commit: str | None, seq: int, event: dict) -> str:
    payload = {
        "producer_commit": producer_commit or "",
        "seq": seq,
        "event_type": event.get("event_type"),
        "created_utc": event.get("created_utc"),
        "query": event.get("query"),
        "limit": event.get("limit"),
        "outcome": event.get("outcome"),
        "total": event.get("total"),
        "error_code": event.get("error_code"),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _write_export_event(event: dict) -> None:
    """Export-only firewall: write local artifacts; never call cross-system services."""
    try:
        root = _repo_root()
        producer_commit = _git_head(root)
        seq = _next_event_seq()

        event = dict(event)
        event.setdefault("seq", seq)
        event.setdefault("event_id", _compute_event_id(producer_commit=producer_commit, seq=seq, event=event))

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
            "producer_commit": producer_commit,
            "files": files,
        }

        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.write("\n")

    except Exception as e:
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


class Document(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: Optional[dict] = None


class SearchQuery(BaseModel):
    query: str
    limit: int = 5


@app.on_event("startup")
async def startup_event():
    """Load existing index if available"""
    global documents
    if embeddings is None:
        print(f"txtai not available: {_TXT_AI_IMPORT_ERROR}")
        return

    if os.path.exists(INDEX_PATH):
        print(f"Loading existing index from {INDEX_PATH}")
        embeddings.load(INDEX_PATH)

        # Load documents metadata
        docs_path = os.path.join(os.path.dirname(__file__), "data", "documents.json")
        if os.path.exists(docs_path):
            with open(docs_path, "r") as f:
                documents = json.load(f)
    else:
        print("No existing index found - starting fresh")


@app.post("/index")
async def index_document(doc: Document):
    """Index a single document"""
    global documents

    _write_export_event({
        "event_type": "index_request",
        "created_utc": _utc_now_iso(),
        "count": 1,
        "txtai_available": embeddings is not None,
    })

    if embeddings is None:
        raise HTTPException(status_code=503, detail="txtai not available")

    # Generate ID if not provided
    if not doc.id:
        doc.id = f"doc_{len(documents)}"

    # Add to documents store
    documents.append({
        "id": doc.id,
        "text": doc.text,
        "metadata": doc.metadata or {}
    })

    # Rebuild index with all documents
    data = [(d["id"], d["text"], None) for d in documents]
    embeddings.index(data)

    # Save index
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    embeddings.save(INDEX_PATH)

    # Save documents metadata
    docs_path = os.path.join(os.path.dirname(__file__), "data", "documents.json")
    with open(docs_path, "w") as f:
        json.dump(documents, f, indent=2)

    return {"status": "indexed", "id": doc.id, "total_documents": len(documents)}


@app.post("/index/batch")
async def index_batch(docs: List[Document]):
    """Index multiple documents at once"""
    global documents

    _write_export_event({
        "event_type": "index_batch_request",
        "created_utc": _utc_now_iso(),
        "count": len(docs),
        "txtai_available": embeddings is not None,
    })

    if embeddings is None:
        raise HTTPException(status_code=503, detail="txtai not available")

    for doc in docs:
        if not doc.id:
            doc.id = f"doc_{len(documents)}"

        documents.append({
            "id": doc.id,
            "text": doc.text,
            "metadata": doc.metadata or {}
        })

    # Rebuild index
    data = [(d["id"], d["text"], None) for d in documents]
    embeddings.index(data)

    # Save
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    embeddings.save(INDEX_PATH)

    docs_path = os.path.join(os.path.dirname(__file__), "data", "documents.json")
    with open(docs_path, "w") as f:
        json.dump(documents, f, indent=2)

    return {"status": "indexed", "count": len(docs), "total_documents": len(documents)}


@app.post("/search")
async def search(query: SearchQuery):
    """Search the indexed documents"""
    created_utc = _utc_now_iso()
    raw_query = "" if query.query is None else query.query
    normalized_query = raw_query.strip()

    # Deterministic bounds
    if len(normalized_query) < 1 or len(normalized_query) > 512:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": normalized_query,
            "limit": max(1, min(query.limit, 25)),
            "outcome": "bad_request",
            "total": 0,
            "error_code": "BAD_QUERY",
        }
        _write_export_event(event)
        return _search_error(400, "BAD_QUERY", "query must be 1-512 characters")

    normalized_limit = max(1, min(int(query.limit), 25))

    # Minimal spam guard (process-local)
    if _rate_limit_search():
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": normalized_query,
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
            "query": normalized_query,
            "limit": normalized_limit,
            "outcome": "unavailable",
            "total": 0,
            "error_code": "TXT_AI_UNAVAILABLE",
        }
        _write_export_event(event)
        return _search_error(503, "TXT_AI_UNAVAILABLE", "txtai not available")

    if not documents:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": normalized_query,
            "limit": normalized_limit,
            "outcome": "ok",
            "total": 0,
            "error_code": None,
        }
        _write_export_event(event)
        return {"results": [], "message": "No documents indexed yet"}

    try:
        results = embeddings.search(normalized_query, normalized_limit)
    except Exception:
        event = {
            "event_type": "search",
            "created_utc": created_utc,
            "query": normalized_query,
            "limit": normalized_limit,
            "outcome": "error",
            "total": 0,
            "error_code": "INTERNAL_ERROR",
        }
        _write_export_event(event)
        return _search_error(500, "INTERNAL_ERROR", "internal error")

    # Enrich results with document text and metadata
    enriched_results = []
    for doc_id, score in results:
        doc = next((d for d in documents if d["id"] == doc_id), None)
        if doc:
            enriched_results.append({
                "id": doc_id,
                "score": float(score),
                "text": doc["text"],
                "metadata": doc.get("metadata", {})
            })

    event = {
        "event_type": "search",
        "created_utc": created_utc,
        "query": normalized_query,
        "limit": normalized_limit,
        "outcome": "ok",
        "total": len(enriched_results),
        "error_code": None,
    }
    _write_export_event(event)

    return {"results": enriched_results, "query": normalized_query}


@app.get("/status")
async def status():
    """Get Truth Engine status"""
    return {
        "status": "online",
        "documents_indexed": len(documents),
        "index_exists": os.path.exists(INDEX_PATH)
    }


@app.delete("/index/clear")
async def clear_index():
    """Clear all indexed documents (use with caution!)"""
    global documents
    documents = []

    if os.path.exists(INDEX_PATH):
        import shutil
        shutil.rmtree(os.path.dirname(INDEX_PATH))

    return {"status": "cleared", "documents_indexed": 0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5050, log_level="info")
