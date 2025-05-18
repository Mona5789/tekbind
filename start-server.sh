#!/usr/bin/env bash
# start-server.sh
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] ; then     
	    (cd grasptek; python manage.py createsuperuser --no-input)
fi
 (cd grasptek; python manage.py collectstatic --no-input)
rm -rf /etc/localtime
ln -s /usr/share/zoneinfo/Asia/Kolkata /etc/localtime
(cd grasptek; gunicorn grasptek.wsgi --user www-data --bind 0.0.0.0:8000 --workers 5) &
nginx -g "daemon off;" -c "/opt/app/nginx.conf"

  
