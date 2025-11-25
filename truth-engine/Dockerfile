FROM python:3.11-slim
WORKDIR /app
COPY truth-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY truth-engine/app.py .
EXPOSE 5050
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5050"]