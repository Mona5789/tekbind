#!/usr/bin/env bash

# Set timezone
rm -rf /etc/localtime
ln -s /usr/share/zoneinfo/Asia/Kolkata /etc/localtime

# Run Django management tasks
cd grasptek

echo "Collecting static files..."
python manage.py collectstatic --no-input

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --no-input
fi

# Start Gunicorn server (listening on $PORT, required by Render)
exec gunicorn grasptek.wsgi:application --bind 0.0.0.0:$PORT --workers 4
