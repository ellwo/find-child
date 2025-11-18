FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pydantic[email]
# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /data/storage/faces

# Run database initialization and start the app
# Note: uvicorn doesn't have a direct flag for max body size
# We need to set it via environment variable or use a reverse proxy
# For now, we'll use the default and handle large files in the application
CMD ["sh", "-c", "python -m app.init_db && uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300"]

