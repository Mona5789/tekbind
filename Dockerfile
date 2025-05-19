FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y nginx curl && \
    apt-get clean

# Copy requirements.txt first (for better caching)
COPY requirements.txt /opt/app/

# Install Python dependencies (including gunicorn if listed in requirements.txt)
RUN pip install --no-cache-dir -r /opt/app/requirements.txt

# Set timezone (optional, you can do this in your script too)
RUN ln -sf /usr/share/zoneinfo/Asia/Kolkata /etc/localtime

# Copy nginx config files
COPY nginx.default /etc/nginx/sites-available/default
COPY nginx.conf /etc/nginx/nginx.conf

# Copy your start script
COPY start-server.sh /opt/app/
RUN chmod +x /opt/app/start-server.sh

# Create necessary directories
RUN mkdir -p /opt/app/pip_cache /opt/app/grasptek/media

# Set working directory
WORKDIR /opt/app

# Copy the rest of your application code
COPY . /opt/app/

# Fix permissions for www-data user
RUN chown -R www-data:www-data /opt/app/

# Expose the port your app will run on
EXPOSE 8000

# Use the script to start gunicorn + nginx
CMD ["/opt/app/start-server.sh"]
