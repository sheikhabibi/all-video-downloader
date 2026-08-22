FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (including ffmpeg and C libraries for curl-cffi)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render sets the PORT environment variable)
EXPOSE 5000

# Start the application using Gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
