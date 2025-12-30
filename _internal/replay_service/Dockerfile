FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y zip \
 && rm -rf /var/lib/apt/lists/*

COPY --chmod=+x cleanup_replays.sh /

ENTRYPOINT ["/cleanup_replays.sh"]
