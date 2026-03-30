# Use python slim (Debian-based) to maintain glibc compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install necessary system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    openssl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose default HTTP Port
EXPOSE 3000

# Start the application
CMD ["python", "app.py"]
