FROM redis:latest

RUN mkdir -p /data /var/log/redis
RUN touch /var/log/redis/redis.log
RUN chmod 777 /var/log/redis/redis.log

VOLUME /data

COPY redis.conf /usr/local/etc/redis/redis.conf

CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
EXPOSE 6379