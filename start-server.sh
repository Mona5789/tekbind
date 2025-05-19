#!/usr/bin/env bash

# Set timezone
rm -rf /etc/localtime
ln -s /usr/share/zoneinfo/Asia/Kolkata /etc/localtime

# Create superuser if env vars are present
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python grasptek/manage.py createsuperuser --no-input
fi

# Collect static files
python grasptek/manage.py collectstatic --no-input

# Start Gunicorn
gunicorn grasptek.wsgi:application --user www-data --bind 0.0.0.0:8000 --workers 5 &

# Start nginx
nginx -g "daemon off;" -c "/opt/app/nginx.conf"
