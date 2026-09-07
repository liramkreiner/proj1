# syntax=docker/dockerfile:1

# ---------- Stage 1: build the React front-end ----------
FROM node:20-alpine AS frontend
WORKDIR /app/web/frontend
COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build          # -> /app/web/frontend/dist

# ---------- Stage 2: Python runtime ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install Python deps first for layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code (the math core + API).
COPY game/ ./game/
COPY game_theory/ ./game_theory/
COPY agents/ ./agents/
COPY web/backend/ ./web/backend/
COPY web/__init__.py ./web/__init__.py
COPY main.py demo.py ./

# Built SPA from stage 1, at the path the backend serves from.
COPY --from=frontend /app/web/frontend/dist ./web/frontend/dist

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c 'import os,urllib.request; urllib.request.urlopen("http://127.0.0.1:" + os.environ.get("PORT", "8000") + "/api/health")'

# Shell form so ${PORT} is expanded (works on Cloud Run, Render, Fly.io, ...).
CMD uvicorn web.backend.app:app --host 0.0.0.0 --port ${PORT}
