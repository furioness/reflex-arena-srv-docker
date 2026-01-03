#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

GIT_DIR='/rulesets_git'
LOCAL_DIR='/rulesets_local'
TARGET_DIR='/srv/steam/reflexded'
TMP="$TARGET_DIR/.rulesets.tmp"

apply_rulesets() {
  echo 'Applying rulesets updates...'

  rm -rf "$TMP"
  mkdir -p "$TMP"

  # Prioritize git over local, so if local will ever be commited or just a name clash,
  # players won't have to wonder which version they are on
  #
  # Why not just cp into the target? cp ins't atomic. mv is,
  # but only when on the same FS (thus, TMP is in the target dir).
  cp "$LOCAL_DIR"/ruleset_* "$TMP" 2>/dev/null || true
  cp "$GIT_DIR"/ruleset_* "$TMP" 2>/dev/null || true

  # if we exit after this line, there won't be any ruleset - fine.
  # I don't expect ded containers to run without this anyway.
  rm -f "$TARGET_DIR"/ruleset_*.cfg

  for ruleset in "$TMP"/ruleset_*.cfg; do
    mv "$ruleset" "$TARGET_DIR/"
  done

  rm -rf "$TMP"
  echo "Rulesets are applied."
}

apply_rulesets_locked() {
  (
      flock --timeout 30 9
      apply_rulesets
    ) 9>/var/lock/rulesets.lock
}

update_git_if_changed() {
  echo 'Checking git for ruleset updates...'
  mkdir -p "$GIT_DIR"
  cd "$GIT_DIR"

  if [ -d ".git" ]; then
    old=$(git rev-parse HEAD)
    git fetch origin
    git reset --hard origin/HEAD
    new=$(git rev-parse HEAD)

    if [[ "$old" != "$new" ]]; then
      apply_rulesets_locked
    fi

  else
    git clone $RULESETS_GIT_REPO .
    apply_rulesets_locked
  fi

  echo 'Checking git is finished.'
}

# updating local rulesets in background
inotifywait -m -e create,modify,delete,move "$LOCAL_DIR" |
while read -r _; do
  apply_rulesets_locked
done &

# updating git rulesets via polling
while true; do
  update_git_if_changed
  sleep 5m
done

