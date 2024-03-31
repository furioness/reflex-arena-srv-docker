FROM debian:12

RUN apt-get update \
 && apt-get install -y zip \
 && rm -rf /var/lib/apt/lists/*

COPY cleanup_replays.sh /

ENTRYPOINT ["/cleanup_replays.sh"]
