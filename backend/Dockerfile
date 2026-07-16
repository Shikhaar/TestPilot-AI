# ==============================================================================
# TestPilot AI — Backend Dockerfile
# Uses pip + requirements.txt for fast Docker builds (avoids Poetry SAT resolver)
# ==============================================================================

# Stage 1: Builder
FROM python:3.12-slim AS builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy and install requirements via pip (much faster than Poetry in Docker)
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Runtime
# ==============================================================================
FROM python:3.12-slim AS runtime

LABEL maintainer="TestPilot AI Team"
LABEL description="TestPilot AI Backend - AI-Powered Regression Testing Platform"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r testpilot && useradd -r -g testpilot -m -d /app testpilot

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy application source
COPY --chown=testpilot:testpilot . .

# Create directories
RUN mkdir -p /tmp/repos /app/logs \
    && chown -R testpilot:testpilot /tmp/repos /app/logs

# Switch to non-root user
USER testpilot

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
