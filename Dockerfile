FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data thingsboard_gateway

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "src/main.py"]
