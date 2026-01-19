#!/usr/bin/env bash
set -euo pipefail

SENTINEL=/srv/steam/reflexded/INSTALL_FINISHED_SENTINEL
if [ -f $SENTINEL ]; then
  echo "reflexded is already installed, skipping"
  exit 0
fi

cd /srv/steam/

mkdir -p reflexded

./steamcmd.sh <<'EOF'
    @ShutdownOnFailedCommand 1
    @sSteamCmdForcePlatformType linux
    @NoPromptForPassword 1
    force_install_dir /srv/steam/reflexded
    login anonymous
    app_update 329740 -beta beta -betapassword betabetabeta validate
    quit
EOF

# explicit check, as steamcmd sometimes returns 0 even on errors
# at least in running with arguments format, the stdin seems to be fine
test -f /srv/steam/reflexded/reflexded || exit 1

cd reflexded

chmod o+x reflexded
mkdir -pm 755 replays


touch $SENTINEL
