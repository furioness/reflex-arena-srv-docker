#!/usr/bin/env bash
set -euo pipefail

echo "Compressing replays..."
find "$REPLAY_DIR" -type f -name '*.rep' -printf '%T+ %p\n' | sort | cut -d' ' -f2- | while IFS= read -r file; do
    zip "${file}.zip" "$file" && rm "$file"
done
echo -e "Compressing finished.\n"


echo "Deleting old replays..."
USED_SPACE_THRESHOLD=70

# Check current disk usage for the specified filesystem
CURRENT_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//g')

# If disk usage exceeds the threshold
while [ "$CURRENT_USAGE" -gt "$USED_SPACE_THRESHOLD" ]; do
    # Find the oldest .rep.gz file based on the timestamp of the gzip archive
    OLDEST_FILE=$(find "$REPLAY_DIR" -type f -name '*.rep.zip' -printf '%T+ %p\n' | sort | head -n 1 | cut -d' ' -f2-)
    if [ -z "$OLDEST_FILE" ]; then
        echo "No files to delete."
        break
    fi
    echo "Deleting oldest file: $OLDEST_FILE"
    rm -f "$OLDEST_FILE"
    CURRENT_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//g')
done
echo "Cleanup finished."

echo "Sleeping..."
sleep 6h
