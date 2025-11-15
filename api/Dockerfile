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
RUN pip install --no-cache-dir pydantic[email]
# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /data/storage/faces

# Run database initialization, migration, init default data, and start the app
CMD ["sh", "-c", "python -m app.init_db && python -m app.migrate_settings && python -m app.init_data && uvicorn app.main:app --host ${BACKEND_HOST:-0.0.0.0} --port 8000"]

