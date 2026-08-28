# ── Stage 1: build React frontend ────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --prefer-offline
COPY frontend/ .
RUN npm run build

# ── Stage 2: production Python image ─────────────────────────────────────────
FROM python:3.14-slim

# system deps for matplotlib/Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (stubs + pyc bytecode)
COPY app/        ./app/
COPY backend/    ./backend/

# Copy built frontend
COPY --from=frontend-build /build/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Boot command — import backend shim first, then start uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
