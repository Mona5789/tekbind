#!/usr/bin/env bash
set -e

# Convert timezone (optional)
ln -sf /usr/share/zoneinfo/Asia/Kolkata /etc/localtime

echo "Starting app..." >&2
env >&2
ls -l /opt/app >&2

# Create superuser if needed
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --no-input
fi

python manage.py collectstatic --no-input

# Use $PORT from Render
exec gunicorn grasptek.wsgi:application --bind 0.0.0.0:$PORT --workers 5
