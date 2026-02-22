FROM python:3.11-slim
LABEL maintainer="Architect — Sovereign Systems Architect"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir pytest pytest-cov ruff mypy bandit
COPY . .
CMD ["pytest", "tests/", "-v", "--tb=short", "--cov=.", "--cov-report=term-missing"]
