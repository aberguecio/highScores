FROM python:3.11-slim

WORKDIR /app

# Install build deps and pip packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/

# Create data directory
RUN mkdir -p /data

EXPOSE 8000

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000