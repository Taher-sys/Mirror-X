# ==============================================================================
# MIRROR-X Master Production Dockerfile
# ==============================================================================

# Build Stage
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Hardened Runtime Stage
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 10001 mirrorx && \
    useradd -u 10001 -g mirrorx -s /bin/bash -m mirrorx

COPY --from=builder /root/.local /home/mirrorx/.local
ENV PATH=/home/mirrorx/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY --chown=mirrorx:mirrorx backend/ .

RUN mkdir -p artifacts/models artifacts/edge && \
    chown -R mirrorx:mirrorx /app

USER mirrorx

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--access-log"]
