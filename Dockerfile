FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set workdir and install Python deps
WORKDIR /opt/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of app
COPY . .

# Permissions
RUN chmod +x start-server.sh

# Expose port (Render uses $PORT)
EXPOSE 8000

CMD ["./start-server.sh"]
