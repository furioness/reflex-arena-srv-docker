#!/usr/bin/env bash
set -euo pipefail

SENTINEL=/srv/steam/reflexded/INSTALL_FINISHED_SENTINEL
if [ -f $SENTINEL ]; then
  echo "reflexded is already installed, skipping"
  exit 0
fi

cd /srv/steam/

wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz && tar -xf steamcmd_linux.tar.gz

./steamcmd.sh <<'EOF'
@ShutdownOnFailedCommand 1
@sSteamCmdForcePlatformType windows
@NoPromptForPassword 1
force_install_dir /srv/steam/reflexded
login anonymous
app_update 329740 validate
quit
EOF

# explicit check, as steamcmd sometimes returns 0 even on errors
# at least in running with arguments format, the stdin seems to be fine
test -f /srv/steam/reflexded/reflexded.exe || exit 1

cd reflexded
cp /reflexded_fixed.exe reflexded.exe

chmod o+x reflexded.exe

# -p is not just for creating parents, it's for being silent, if the dir is already there
mkdir -p replays
chmod 755 replays

touch $SENTINEL
