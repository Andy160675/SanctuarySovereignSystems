FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pyyaml

COPY . .

EXPOSE 8097

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8097"]
