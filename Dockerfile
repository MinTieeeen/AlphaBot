FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .
COPY .env.sample .env

# Create content directory
RUN mkdir -p content

# Default: run full workflow
CMD ["python", "main.py"]
