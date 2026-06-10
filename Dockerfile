FROM python:3.14-slim

WORKDIR /workspace

# System deps
# - curl:    healthcheck
# - build-essential, gfortran: pmdarima / arch 编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Python deps — 先升 pip + setuptools + wheel,再装齐
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# App
COPY . .

# Expose API port (default 8000)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
