# Multi-stage Dockerfile for Code Review Orchestration System

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/deploy.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY capstone /app/capstone
COPY deployment/.env /app/.env

# Set Python path
ENV PYTHONPATH=/app

# Create data directory for memory persistence
RUN mkdir -p /app/data/memory

# Expose port (if running webhook server)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import capstone; print('healthy')" || exit 1

# Default command (will be overridden by ADK)
CMD ["python", "-m", "capstone.agents.orchestrator"]
