FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY ../backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../backend /app/backend
COPY . /app/worker

ENV PYTHONPATH=/app

CMD ["python", "worker/worker.py"]
