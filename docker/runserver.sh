#!/usr/bin/env bash
set -euo pipefail

cd /srv/steam/reflexded

CONTAINER_ALREADY_STARTED="/srv/steam/reflexded/CONTAINER_ALREADY_STARTED"
if [ ! -e $CONTAINER_ALREADY_STARTED ]; then
    sleep 10
    exit 0
fi

# sleep $((RANDOM % 3 + 1))

# exec and handling of CTRL+C seems to have no effect here...
WINEDEBUG=-all exec env wine ./reflexded.exe $SRV_ARGS
