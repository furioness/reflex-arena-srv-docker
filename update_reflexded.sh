#!/usr/bin/env bash

#   Steam> Update state (0x0) unknown, progress: 0.00 (0 / 0)
#   Error! App '329740' state is 0x6 after update job.
# steamcmd can fail to update with that error, this rm fixes it somehow.
sudo rm -f reflexded/steamapps/appmanifest_329740.acf

sudo rm -f reflexded/INSTALL_FINISHED_SENTINEL
docker compose stop
docker compose up -d
