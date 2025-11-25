FROM python:3.11-slim
WORKDIR /app
COPY watcher.py .
RUN pip install watchdog
CMD ["python", "watcher.py"]