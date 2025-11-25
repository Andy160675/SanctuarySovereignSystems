from fastapi import FastAPI, HTTPException
from txtai.embeddings import Embeddings
import uvicorn, os
from datetime import datetime

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

@app.get("/search")
def search(q: str, limit: int = 7):
    if not index_loaded:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        results = embeddings.search(q, limit)
        return {
            "query": q,
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "total": len(results)
        }
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
        # Get basic stats from embeddings
        return {
            "index_loaded": index_loaded,
            "index_path": index_path,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)