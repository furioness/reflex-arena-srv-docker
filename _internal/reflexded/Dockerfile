FROM debian:13-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y ca-certificates libc6:i386 libcurl4t64 wget --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*



RUN mkdir -p /srv/steam/
WORKDIR /srv/steam/

RUN wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz \
    && tar -xf steamcmd_linux.tar.gz \
    && rm steamcmd_linux.tar.gz

COPY --chmod=+x runserver.sh /
COPY --chmod=+x install_reflexded.sh /

ENTRYPOINT ["/runserver.sh"]
