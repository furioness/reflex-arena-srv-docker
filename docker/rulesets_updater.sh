#!/usr/bin/env bash
set -e

CONTAINER_ALREADY_STARTED="/srv/steam/reflexded/CONTAINER_ALREADY_STARTED"
if [ ! -e $CONTAINER_ALREADY_STARTED ]; then
    sleep 10
    exit 0
fi

mkdir -p /rulesets
cd /rulesets

if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/Nailok/reflex_rulesets.git .
fi

rm -r /srv/steam/reflexded/ruleset_* || true
cp ruleset_* /srv/steam/reflexded/

sleep 1h
