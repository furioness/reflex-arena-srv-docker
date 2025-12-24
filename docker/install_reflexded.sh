#!/usr/bin/env bash
set -euo pipefail

CONTAINER_ALREADY_STARTED="/srv/steam/reflexded/CONTAINER_ALREADY_STARTED"
if [ -e $CONTAINER_ALREADY_STARTED ]; then
    exit 0
fi

cd /srv/steam/

wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz && tar -xf steamcmd_linux.tar.gz

./steamcmd.sh +runscript /docker/install_reflexded.steamcmd

cd reflexded
cp /docker/dedicatedserver.cfg .
cp /docker/reflexded.exe .

chmod o+x reflexded.exe
mkdir -pm 755 replays

touch $CONTAINER_ALREADY_STARTED
