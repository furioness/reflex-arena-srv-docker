#!/usr/bin/env bash
set -euo pipefail

#   Steam> Update state (0x0) unknown, progress: 0.00 (0 / 0)
#   Error! App '329740' state is 0x6 after update job.
# steamcmd can fail to update with that error, this rm fixes it somehow.
sudo rm -f reflexded/steamapps/appmanifest_329740.acf

sudo rm -f reflexded/INSTALL_FINISHED_SENTINEL
docker compose stop
docker compose up reflexded_installer  # so we can see the logs
docker compose up -d
