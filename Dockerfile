# Polymarket Crypto Lab - Backend Dockerfile
FROM python:3.12-slim as backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY src/backend/ src/backend/
COPY config/ config/
COPY .env.example .

# Create necessary directories
RUN mkdir -p data logs

# Expose port
EXPOSE 8000

# Set default command
CMD ["python", "-m", "uvicorn", "src.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
