# NEXUS API Service Container (Development Foundation - Phase 02)
# Production and staging stages will be refined in Phase 32.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install base OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging configuration
COPY pyproject.toml .

# Development stage install
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# Copy source packages
COPY services/ ./services/
COPY digital_twin/ ./digital_twin/
COPY ml/ ./ml/
COPY geospatial/ ./geospatial/
COPY backtesting/ ./backtesting/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "services.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
