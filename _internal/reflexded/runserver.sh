#!/usr/bin/env bash
set -euo pipefail

cd /srv/steam/reflexded

# Build a proper argv from env vars (safe splitting, no re-globbing)
set -- $SRV_ARGS_COMMON $SRV_ARGS

export LD_LIBRARY_PATH=.:./linux64
exec ./reflexded "$@"
