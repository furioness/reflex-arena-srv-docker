#!/usr/bin/env bash
set -euo pipefail

cd /srv/steam/reflexded

# sleep $((RANDOM % 3 + 1))
# that sleep was an attempt to fix a rare error,
# when after frequent restarts, there appear some odd errors
# regarding something about steam and certificates
# which felt like rate limit on master server registration or VAC auth
# but it's too rare, and I'm not sure, so whatever...

# exec and handling of CTRL+C seems to have no effect here...
export WINEDEBUG=-all
exec wine ./reflexded.exe $SRV_ARGS_COMMON $SRV_ARGS
