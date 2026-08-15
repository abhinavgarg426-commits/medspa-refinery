# Dockerfile for Miami MedSpa Data Refinery
# Multi-stage build for smaller production image

# ---- Build Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to /app/.venv
RUN python -m venv .venv && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY scraper.py server.py mcp_server.py medspa_data.db ./

# Ensure database is writable (Render/Cloudflare persistent disk mount point)
RUN mkdir -p /app/data && \
    cp medspa_data.db /app/data/medspa_data.db && \
    ln -sf /app/data/medspa_data.db /app/medspa_data.db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD /app/.venv/bin/python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=3).raise_for_status()"

# Run the FastAPI server with x402 middleware
# Use the venv python directly
CMD ["/app/.venv/bin/uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]