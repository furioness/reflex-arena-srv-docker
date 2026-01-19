#!/usr/bin/env bash
set -euo pipefail

cd /srv/steam/reflexded

export LD_LIBRARY_PATH=.:./linux64
exec ./reflexded $SRV_ARGS_COMMON $SRV_ARGS
