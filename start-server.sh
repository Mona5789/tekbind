#!/usr/bin/env bash
set -ex  # <-- enables debug + exit on error

ln -sf /usr/share/zoneinfo/Asia/Kolkata /etc/localtime

echo "Creating superuser if env vars present"
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --no-input || true
fi

echo "Collecting static files"
python manage.py collectstatic --no-input

echo "Starting Gunicorn"
exec gunicorn grasptek.wsgi:application --bind 0.0.0.0:8000 --workers 5
