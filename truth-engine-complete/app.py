"""
Truth Engine - txtai-based RAG/Search Backend
Sovereign System - Phase 3 Module 2
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from txtai.embeddings import Embeddings
from typing import List, Optional
import os
import json

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
embeddings = Embeddings({
    "method": "sentence-transformers",
    "path": "sentence-transformers/all-MiniLM-L6-v2",
    "content": True
})

# Index storage path
INDEX_PATH = os.path.join(os.path.dirname(__file__), "data", "index")

# In-memory document store (will be persisted)
documents = []


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
    if not documents:
        return {"results": [], "message": "No documents indexed yet"}

    results = embeddings.search(query.query, query.limit)

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

    return {"results": enriched_results, "query": query.query}


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
