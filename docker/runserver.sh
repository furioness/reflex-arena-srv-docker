#!/usr/bin/env bash

rm -r ruleset_*
cp rulesets/ruleset_* .

# exec and handling of CTRL+C seems to have no effect here...
WINEDEBUG=-all exec env wine ./reflexded.exe $SRV_ARGS
