# Multistage Build: zuerst Frontend statisch exportieren, dann Backend mit eingebettetem Frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update \
 && apt-get install --no-install-recommends -y curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

FROM python-base AS deps
WORKDIR /install
COPY infra/docker/requirements-backend.txt /install/requirements.txt
RUN pip install -r requirements.txt

FROM python-base AS runtime
WORKDIR /app
ENV FRONTEND_STATIC_PATH=/app/frontend_static \
    PYTHONPATH=/app
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY shared/python/djr_core/djr_core /app/djr_core
COPY ingestion /app/ingestion
COPY data_lake /app/data_lake
COPY skills /app/skills
COPY analytics /app/analytics
COPY backend /app/backend
COPY --from=frontend-build /build/out /app/frontend_static
RUN useradd --system --uid 1000 djr \
 && chown -R djr:djr /app
USER djr
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --silent --fail http://127.0.0.1:8081/api/v1/health || exit 1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1", "--no-access-log"]
