FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y wine32:i386 wget nano htop \
 && rm -rf /var/lib/apt/lists/*

RUN useradd steam -m -r -s /bin/bash
USER steam

WORKDIR /home/steam

RUN wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz && tar -xf steamcmd_linux.tar.gz

COPY install_reflexded.steamcmd .

RUN ./steamcmd.sh +runscript install_reflexded.steamcmd

WORKDIR /home/steam/reflex/

COPY --chown=steam:steam --chmod=750 reflexded.exe runserver.sh ./

ENTRYPOINT ["/home/steam/reflex/runserver.sh"]
