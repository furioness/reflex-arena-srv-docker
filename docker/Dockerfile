FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y gpg htop nano wget \
 && mkdir -pm755 /etc/apt/keyrings  \
 && wget -O - https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key - \
 && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources \
 && apt install -y winehq-stable \
 && rm -rf /var/lib/apt/lists/*

# RUN useradd steam -m -r -s /bin/bash
# USER steam
