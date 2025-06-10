FROM python:3.12.3

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LIBREOFFICE_PATH=/usr/bin/libreoffice
ENV PYTHONPATH=/usr/lib/python3/dist-packages
ENV PATH=/usr/bin:/usr/local/bin:$PATH
ENV DJANGO_SETTINGS_MODULE=grasptek.settings

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    unoconv \
    python3-uno \
    build-essential \
    python3-dev \
    libpq-dev \
    libdbus-1-dev \
    pkg-config \
    meson \
    ninja-build \
    libglib2.0-dev \
    dbus-x11 \
    gcc \
    cmake \
    libgirepository1.0-dev \
    gir1.2-glib-2.0 \
    libcairo2-dev \
    gobject-introspection \
    **libsystemd-dev** \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy project files
COPY . /opt/app/

# Install Python dependencies
RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache

# Expose port
EXPOSE 8000

# Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
