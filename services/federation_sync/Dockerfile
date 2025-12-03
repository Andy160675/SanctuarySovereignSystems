FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    httpx==0.26.0 \
    pydantic==2.5.3

# Copy application
COPY app.py .

# Expose port
EXPOSE 8094

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8094/health', timeout=5).raise_for_status()"

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8094"]
