#!/usr/bin/env bash
set -euo pipefail

STEAM_ROOT=/srv/steam
INSTALL_DIR=$STEAM_ROOT/reflexded
SENTINEL=$INSTALL_DIR/INSTALL_FINISHED_SENTINEL

if [[ -f "$SENTINEL" ]]; then
  echo "reflexded is already installed, skipping"
  exit 0
fi

cd "$STEAM_ROOT"
mkdir -p "$INSTALL_DIR"

install_stable() {
  ./steamcmd.sh <<EOF
    @ShutdownOnFailedCommand 1
    @sSteamCmdForcePlatformType linux
    @NoPromptForPassword 1
    force_install_dir $INSTALL_DIR
    login anonymous
    app_update 329740 validate
    quit
EOF
}

is_installed() {
  # steamcmd can fail with exit code 0,
  # so better to check whether reflexded is a non-empty file
  # but this isn't a guarantee anyway, so keep checking the logs!
  [[ -s "$INSTALL_DIR/reflexded" ]]
}

echo "Attempting stable install…"
install_stable

is_installed || {
  echo "ERROR: reflexded installation failed"
  exit 1
}

cd "$INSTALL_DIR"
chmod o+x reflexded
mkdir -pm 755 replays

touch "$SENTINEL"
