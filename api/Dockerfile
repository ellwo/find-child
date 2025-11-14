FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /data/storage/faces

# Run database initialization, init default data, and start the app
CMD ["sh", "-c", "python -m app.init_db && python -m app.init_data && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

