FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y wine32:i386 wget nano htop \
 && rm -rf /var/lib/apt/lists/*

# RUN useradd steam -m -r -s /bin/bash
# USER steam
