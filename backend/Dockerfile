FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH /app

# Copy requirements first for better layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary files (exclude tests, etc. using .dockerignore)
COPY . .

# Make wait-for-it.sh executable
RUN chmod +x wait-for-it.sh

# Run migrations and start server
CMD alembic upgrade head && python scripts/create_tables.py && python scripts/create_admin.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 