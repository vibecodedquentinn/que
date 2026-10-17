FROM node:22-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/data/voices && python -c "from pathlib import Path; from piper.download_voices import download_voice; download_voice('de_DE-thorsten-high', Path('/app/data/voices'))"
ENV DATA_DIR=/app/data
ENV STATIC_DIR=static
ENV TTS_PROVIDER=piper
ENV PIPER_VOICE=de_DE-thorsten-high
COPY backend/app ./app
COPY --from=frontend /fe/dist ./static
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
