# Reflexded install & autoupdate

## 1. Goal

Provide a clean, race-free way to:

* install `reflexded` via SteamCMD once
* periodically check for updates
* restart running workers automatically when an update happens
* keep logs flowing to Docker logs
* avoid Docker socket access and complex orchestration

Constraints:

* Docker Compose (not Kubernetes)
* single host
* Wine-based Windows server
* simplicity > cleverness

---

## 2. General idea (final architecture)

### Roles

1. **Installer container (one-shot)**

    * Runs SteamCMD
    * Performs initial install
    * Exits with code 0 on success

2. **Updater container (long-running)**

    * Periodically runs SteamCMD update check
    * If update happened → touches an *update sentinel*

3. **Worker containers (servers)**

    * Run `reflexded.exe` under Wine
    * Watch the update sentinel via `inotify`
    * On sentinel change → exit
    * Docker restart policy restarts them

### Key principles

* **Single writer** to SteamCMD files (installer/updater only)
* **No install sentinel** (ordering handled by Compose)
* **One update sentinel** (event, not state)
* **Workers are dumb**: they only react to sentinel changes
* **Docker handles restarts**, not scripts

---

## 3. Docker Compose wiring

### Shared volume

```yaml
volumes:
  reflexded_data:
```

### Installer (one-shot)

```yaml
services:
  reflexded_installer:
    image: reflexded-manager
    command: install
    restart: "no"
    volumes:
      - reflexded_data:/srv/steam/reflexded
```

### Updater (long-running)

```yaml
  reflexded_updater:
    image: reflexded-manager
    command: update
    restart: unless-stopped
    depends_on:
      reflexded_installer:
        condition: service_completed_successfully
    volumes:
      - reflexded_data:/srv/steam/reflexded
```

### Worker(s)

```yaml
  ded1:
    image: reflexded-worker
    restart: unless-stopped
    init: true
    tty: true
    stdin_open: true
    depends_on:
      reflexded_installer:
        condition: service_completed_successfully
    volumes:
      - reflexded_data:/srv/steam/reflexded
```

Notes:

* `depends_on` is **startup ordering only**
* Installer runs once per `compose up`
* Updater and workers never race with installer

---

## 4. Manager image (installer + updater)

### Entry point skeleton

```bash
#!/usr/bin/env bash
set -euo pipefail

MODE=${1:?install|update}
ROOT=/srv/steam/reflexded
UPDATE_SENTINEL="$ROOT/.update_trigger"

case "$MODE" in
  install)
    run_install
    : > "$UPDATE_SENTINEL"   # create sentinel once
    ;;
  update)
    run_update_loop
    ;;
esac
```

### Update loop (simple polling)

```bash
run_update_loop() {
  while true; do
    if steamcmd_update_detected; then
      touch "$UPDATE_SENTINEL"
    fi
    sleep 6h
  done
}
```

Notes:

* Sentinel content is irrelevant
* `touch` updates mtime/ctime → inotify event
* Polling is unavoidable (Steam has no push API)

---

## 5. Worker logic (server containers)

### Pattern

* Run server normally
* Background watcher waits for sentinel change
* On event → `kill 0` (container exits)
* Docker restarts container

### Minimal worker script

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT=/srv/steam/reflexded
SENTINEL="$ROOT/.update_trigger"

(
  inotifywait "$SENTINEL" >/dev/null 2>&1
  echo "Update detected, restarting container"
  kill 0
) &

export WINEDEBUG=-all
wine ./reflexded.exe $SRV_ARGS_COMMON $SRV_ARGS
```

Why this works:

* `kill 0` kills whole process group (server + watcher + script)
* Container exits cleanly
* Restart policy restarts it
* No PID tracking needed

---

## 6. Sentinel semantics

* **Purpose**: runtime event only
* **Not** a state indicator
* **Not** an install marker

Rules:

* Pre-create sentinel (installer does this)
* Updater only `touch`es it on real updates
* Workers only watch it

Do **not**:

* rely on atime (often disabled)
* overload sentinel for install ordering

---

## 7. Signals, logging, and PID 1

Key decisions:

* `init: true` everywhere → sane signal handling (tini)
* Workers do **not** use `exec` (they supervise)
* Logs go to Docker logs regardless of foreground/background

Exit codes:

* `143` = clean SIGTERM (good)
* `137` = SIGKILL (bug)

---

## 8. Why not a single self-switching installer/updater container

Considered idea:

* same container
* first run installs, exits
* restarts into update mode

Problems:

* requires extra sentinel/state
* brittle lifecycle transitions
* installer exit semantics become unclear
* harder to reason about startup ordering

Conclusion:

* **two services, same image** is clearer and safer

---

## 9. About SteamCMD state reuse

Facts:

* SteamCMD keeps its own cache/config
* Re-running in a fresh container causes re-initialization

Options:

1. **Do nothing (recommended)**

    * SteamCMD startup cost is acceptable
    * Update interval is hours
    * Simplicity wins

2. **Persist SteamCMD directories** (optional)

    * Requires discovering and mounting SteamCMD paths
    * Adds complexity
    * Little real benefit unless updates are very frequent

Given constraints: **do not optimize prematurely**.

---

## 10. Final mental model

* Compose = startup ordering
* Installer = one-shot, exit code matters
* Updater = single writer, polling
* Sentinel = event bus
* Workers = reactive, disposable
* Docker = restart orchestration

Each piece does one thing.
No hidden coupling.
No fragile magic.

---

## 11. Open extensions (future)

* Detect active players before restart
* Graceful shutdown protocol
* Version pinning / rollback
* Shorter polling with manifest checks

All can be added without changing the core design.
