# Multi-stage Dockerfile for FastAPI app
# Build stage
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies into a venv (no build tools needed for pre-built wheels)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy & install Python requirements (requirements.txt expected at repo root)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Final stage
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# OS packages needed at runtime (minimal: just curl for healthcheck)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder (includes installed packages)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . /app

# Expose port
EXPOSE 8000

# Healthcheck
# Use a single-line HEALTHCHECK (avoid embedded literal "\n" characters)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:8000/ || exit 1

# Run with a single worker by default (good for development). For production
# consider using a process manager or multiple workers behind a load balancer.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
