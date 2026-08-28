# Frontend is pre-built and committed at frontend/dist/ — no Node stage needed.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATABASE_URL="" \
    DB_POOL_SIZE=5 \
    DB_MAX_OVERFLOW=10

# System dependencies for matplotlib, Pillow, and PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (stubs, models, and services)
COPY app/        ./app/
COPY backend/    ./backend/
COPY static/     ./static/

# Pre-built frontend assets
COPY frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Container healthcheck probing /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Boot command — start uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
