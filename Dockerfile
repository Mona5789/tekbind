FROM python:3.10-slim

# Install system deps
RUN apt-get update && apt-get install -y nginx tzdata curl gcc \
    && rm -rf /var/lib/apt/lists/*

# Create working dir
WORKDIR /opt/app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Permissions
RUN chmod +x start-server.sh

# Expose port (Render uses $PORT)
EXPOSE 8000

CMD ["./start-server.sh"]
