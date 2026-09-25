# ==============================================================================
# MIRROR-X Production Backend Dockerfile (Multi-stage, Non-root, Hardened)
# ==============================================================================

# Stage 1: Build Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Hardened Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install minimal runtime shared libraries for MySQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged mirrorx user and group
RUN groupadd -g 10001 mirrorx && \
    useradd -u 10001 -g mirrorx -s /bin/bash -m mirrorx

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/mirrorx/.local
ENV PATH=/home/mirrorx/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application source code
COPY --chown=mirrorx:mirrorx . .

# Set up artifacts and edge directories with correct permissions
RUN mkdir -p artifacts/models artifacts/edge && \
    chown -R mirrorx:mirrorx /app

# Switch to non-root user
USER mirrorx

# Expose API port
EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Launch production server with multiple workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--access-log"]
