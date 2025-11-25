# Truth Engine - txtai RAG Backend

Sovereign System Phase 3 - Module 2

## Purpose

Semantic search and knowledge retrieval backend using txtai embeddings. Provides the "memory" and "recall" capabilities for the Boardroom Shell and Blade Scanner.

## Installation

```bash
cd E:\SOVEREIGN-2025\PROJECTS_ACTIVE\truth-engine
pip install -r requirements.txt
```

## Running

```bash
# Development
python app.py

# Production (with uvicorn)
uvicorn app:app --host 127.0.0.1 --port 5050 --reload
```

## API Endpoints

### POST /index
Index a single document
```json
{
  "text": "Your document text here",
  "metadata": {"source": "file.txt", "date": "2025-11-19"}
}
```

### POST /index/batch
Index multiple documents at once
```json
[
  {"text": "Document 1", "metadata": {}},
  {"text": "Document 2", "metadata": {}}
]
```

### POST /search
Search indexed documents
```json
{
  "query": "your search query",
  "limit": 5
}
```

### GET /status
Check Truth Engine status

### DELETE /index/clear
Clear all indexed documents (use with caution)

## Integration

- **Boardroom Shell** connects to `http://localhost:5050` for searches
- **Blade Scanner** sends metadata via `/index/batch` endpoint
- **Golden Master** can index file manifests for auditable search

## Storage

- Index: `data/index/`
- Document metadata: `data/documents.json`

Both are persisted and loaded on startup.
