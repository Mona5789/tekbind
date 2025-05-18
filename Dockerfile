FROM qprofiles_base:latest
COPY nginx.default /etc/nginx/sites-available/default
COPY nginx.conf /etc/nginx/nginx.conf
COPY start-server.sh /opt/app/
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log
RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache
RUN mkdir -p /opt/app/grasptek/media
COPY . /opt/app/grasptek/
COPY nginx.conf /opt/app/nginx.conf
WORKDIR /opt/app
RUN chown -R www-data:www-data /opt/app/
RUN chown -R www-data:www-data /opt/app/grasptek/
RUN chown -R www-data:www-data /opt/app/grasptek/media
RUN chmod +x /opt/app/start-server.sh
EXPOSE 8020
STOPSIGNAL SIGTERM
CMD ["/opt/app/start-server.sh"]
