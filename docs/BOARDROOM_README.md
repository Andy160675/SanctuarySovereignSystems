# Boardroom (Streamlit) - Quickstart

## Files
- `boardroom/boardroom_app.py` - Streamlit app (First-Run Checklist + Dashboard)
- `docs/health/health_check_openapi.yaml` - Health endpoint contract
- `boardroom/requirements.txt` - minimal Python deps

## Run locally

1. Create venv and install deps:
   ```bash
   cd boardroom
   python -m venv .venv
   source .venv/bin/activate        # or .venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   ```

2. Start Boardroom:
   ```bash
   streamlit run boardroom_app.py --server.port 8501
   ```

3. Open: http://localhost:8501

## Expected health endpoints

Boardroom expects these URLs to exist and return JSON matching `docs/health/health_check_openapi.yaml`:

| Endpoint | Port |
|----------|------|
| `/health/core` | 8001 |
| `/health/truth` | 8002 |
| `/health/enforce` | 8003 |
| `/health/models` | 8004 |
| `/health/rag_index` | 8005 |

Unreachable endpoints are treated as `status: down`.

## Example healthy response

```json
{
  "status": "healthy",
  "latency_ms": 12.3,
  "version": "1.0.0",
  "uptime_s": 12345,
  "details": {
    "dependencies": {
      "db": "healthy"
    }
  }
}
```

## Integration with LAN Deployment

On a multi-node deployment:

| Node | Services | Ports |
|------|----------|-------|
| NODE-01 (Orchestrator) | Boardroom, Core | 8501, 8001 |
| NODE-02 (Truth Engine) | Truth, RAG | 8002, 8005 |
| NODE-03 (Agent Fleet) | Enforce, Models | 8003, 8004 |

Update `HEALTH_ENDPOINTS` in `boardroom_app.py` with actual node IPs:

```python
HEALTH_ENDPOINTS = {
    "Core": "http://192.168.50.10:8001/health/core",
    "Truth Engine": "http://192.168.50.20:8002/health/truth",
    "Enforcement API": "http://192.168.50.30:8003/health/enforce",
    "Models / Ollama": "http://192.168.50.30:8004/health/models",
    "RAG Index": "http://192.168.50.20:8005/health/rag_index",
}
```

## Next steps

1. Implement the 5 health endpoints in backend services
2. Wire Truth search to actual `/truth/search` API
3. Wire Core Analyze to `/core/analyze` API
4. Connect Alerts/Activity to real metrics stack
