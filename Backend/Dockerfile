FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip

# Install numpy FIRST with correct version for Python 3.11
RUN pip install --no-cache-dir numpy==1.26.4

# Install heavy dependencies (they will use the numpy we just installed)
RUN pip install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir transformers==4.44.2
RUN pip install --no-cache-dir sentence-transformers==3.1.1

# Copy requirements and install remaining packages
COPY reqs.txt .
RUN pip install --no-cache-dir -r reqs.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p database uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}