#!/usr/bin/env bash
set -e

ln -sf /usr/share/zoneinfo/Asia/Kolkata /etc/localtime

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --no-input
fi

python manage.py collectstatic --no-input

exec gunicorn grasptek.wsgi:application --bind 0.0.0.0:8000 --workers 5
