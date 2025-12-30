#!/usr/bin/env bash
set -euo pipefail

GIT_DIR='/rulesets_git'
LOCAL_DIR='/rulesets_local'
TARGET_DIR='/srv/steam/reflexded'

apply_rulesets() {
  echo 'Applying rulesets updates...'

  tmp=$(mktemp -d)
  (
      # non-matched globs don't rise an error, plus don't enter for loop
      # plus a sub-shell, so shopt are confined - just in case
      # and the final mv from a temp dir instead of direct cp - for a file-level atomicity
      shopt -s nullglob

      cp "$GIT_DIR"/ruleset_* "$tmp" 2>/dev/null || true
      cp "$LOCAL_DIR"/ruleset_* "$tmp" 2>/dev/null || true

      rm -f "$TARGET_DIR"/ruleset_*.cfg

      cd "$tmp"
      for f in ruleset_*.cfg; do
        mv "$f" "$TARGET_DIR/"
      done
    )

  rmdir "$tmp"

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

