# Reflex Arena Dedicated server quick deployment (version 2)

A simpler way to host dedicated Reflex Arena servers with the following features:
- quick deployment and auto start on system reboot, thanks to Docker Compose
- replays sharing with rate limits
- automatic replays compression
- automatic replays clean up on low disk space
- automatic synchronization with custom rulesets repo
- fully static web page with matches history and replays download
- a single config for everything


## How to
- get a Linux machine with Docker and Docker Compose installed
- clone the repo and `cd` into it
- copy `docker-compose.example.yml` as `docker-compose.yml` and edit it (details below)
- make sure the ports are open (google "how to open ports in a firewall" + name of your distro, usually it's `ufw`)
  - 25787, 25788, etc, for each server; both UDP and TCP!
  - 80 for the replays web page
- run docker `compose up -d`
- run `docker compose logs -f`, if after a few minutes or so you don't see any errors, go check the servers!

If you find this all too complicated, check the original
guide: https://github.com/m3fh4q/ReflexArenaDedicatedServerGuideLinux

### How to configure

All configuration is done in `docker-compose.yml`. There is an empty `reflexded/dedicatedserver.cfg` - keep it as is.

#### Common server settings

```yaml
x-dedicatedserver-cfg-env: &dedicatedserver-cfg-env
  SRV_ARGS_COMMON: >
    ...
```

settings under this header will be applied to all instances. Make sure to start each command with `+` - a reflexded
specific delimiter.

### Specific server instance settings

Copy `dedX` section, increment X by 1, increment the ports - both in service definition and in `SRV_ARGS` in
`+sv_gameport`, and add any additional settings. Those will override the common ones.

#### `SRV_ARGS_*` with special characters (`#`, quotes, spaces)

There are **two supported ways** to write server arguments. Pick any.

1) Put everything on one line and wrap it in single quotes:

```yaml
SRV_ARGS: '+sv_hostname #1 Bobr Rated EU +sv_gameport 25787'
```

2) Use YAML multiline string syntax:

```yaml
SRV_ARGS: >
  +sv_hostname #1 Bobr [Replays]
  +sv_gameport 25787
```

Beware! In the multiline form, `#` (and everything else) is treated as a normal character, not a comment.

If in doubt, check how reflexded uses it by running:

```bash
docker compose logs ded1 | grep 'applying command line paramaters:' -A 20
```

---

Remember to check the firewall for the ports!

Then run `docker compose up -d --remove-orphans` (remove orphans is useful in case you reduce the number of instances)
and see if things working.

### About VPS and performance requirements

No science here, just vague heuristics.

Things aren't clear, but for the cheapest shared CPU VPS with 1 vCPU and 1 GB of RAM, a safe limit should be around 3
servers with 9 players per server.

If there is such an option, prefer high CPU frequency servers.
Also, monitor CPU and RAM usage - make sure there are plenty of free resources. And add 1-3GB of swap, to be sure.
I have my speculations on the topic in the MISC section below.

For duels, a compressed replay usually takes around 3 MB, so for 10GB you will get around 3000 replays - sounds like
plenty.

Please, don't be too cheap! Better not to host at all than using laggy web-tier VPS - this game kills mentally hard
enough already without ping spikes and lags.

## Components details

If you just want to host and everything seems to work just fine, you probably can skip this.

### Why Docker Compose?

This simplifies initial installation and auto-start on system reboot, plus gives some level of isolation that keeps the
system clean.

Security-wise this is also a better thing, but as docker runs under `root`, this raises valid concerns, though I don't
expect anythign serious.

Also, it allows for better performance limiting. In the future `tq` could be applied to docker networks to limit web
part and give high priority for reflexded trafic (perhaps just the UDP side).

In the future it would be possible to ship just a single docker-compose.yml for deployment.

### Reflexded installer/updater

Runs once per `docker compose up`. If there is `reflexded/INSTALL_FINISHED_SENTINEL` - does nothing. Otherwise, runs
steamcmd installation script.

Currently, it attempts to run a public build (for linux, so it's 1.3 at minimum), on failure it tries `beta` version.

There is a handy `update_reflexded.sh` script that uses the same thing for updating the server.

### Rulesets updater

It keeps rulesets in sync with https://github.com/Nailok/reflex_rulesets.git (you can change for your own in docker
compose `RULESETS_GIT_REPO`). Also, you can put your own rulesets in `rulesets_local` folder (those will apply
automatically), but rulesets with the git will take precendence, so if you `callvote ruleset cr2`, you know that you
play the latest version, not some local mutation.

### Replays services

This build contains facilities for compressing, cleaning, and sharing replays via a static web page - in a low-resource
usage manner.

#### Backend

`replay_service` from docker compose is responsible for compressing, cleaning up, and parsing replays metadate.

Compression is automatic and uses a common .zip format.
Cleanup is done once per hour, you can configure limits in the `docker-compose.yml`.
`MIN_EXPECTED_DISK_GiB: 10` - this is a sanity check. On ZFS or other less common file systems, there could be problems
with figuring out free space. To be sure, run `docker compose logs replay_service` and look for something like
`Unable to determine disk usage!` or `Disk free: 20.5% (13378 MiB)` lines to be sure.

##### Replay parsing

Parsing is attempted using https://github.com/Donaldduck8/reflex-replay-tools thing, and may break with future reflex
updates (who would believe, reflex updates...). On errors, it falls back to parsing the replay name to get the match
date. If that thing crashes, then whole `replay_service` will too, so you contact me to see if it's fixable.

So far it works almost perfectly, except if a player leaves a match early, then they won't be listed.

Parsed DB is stored in `db` folder. The DB retains data even for removed replays, so works like a match history.

#### Frontend

Nginx serves replays and static files for a web page - there is no "active" component here, no input data except for a
URL path.

Currently implemented on Vue.js just because, plus, the original idea was to add some filtering, so it may worth the
slight overhead.
There is no dedicated build container or anything, nginx just serves `_internal/replay_frontend/dist` that comes from
the repo.

The initial idea was to use replays chunks instead of loading the whole set, so only what is used is loaded.
The current implementation is just to get something working.

## Miscellaneous

### RAM usage

**This remark was about 1.2 under wine, but probably still relevant - needs rechecking.**

It seems that memory usage is around 250MB without much dependence on a map.
But it could drop to stable 15-60 due to swapping, so make sure you have swap enabled, so you can host a few servers on low RAM machines.
Check `docker stats` for residual RAM usage and `cat /sys/fs/cgroup/system.slice/docker-<container-id-from docker stats>.scope/memory.swap.current` for the swap (in bytes).

### Migrating from the original build (on wine)

The easiest way is to start afresh (as in the how-to section), then move all the replays into the new location.

I'll try to make it possible for the future updates to work as simple `git pull` + comparison of docker-compose with a
clear list of changes.

#### Versioning

I'll ~~follow SemVer~~ increment versions on breaking changes, so if the version doesn't change, simple `git pull` (and
perhaps service restart) should do
the thing.

## Possible future improvements
- sanitized rulesets: there is a possibility that things like `sv_refpassword` can be included in it - need to sanitize
- TLS for the replay web server
- health checks with notifications
- using image repos instead of building everything locally, so the whole deployment could be just a single
  docker-compose file
- tc (Trafic Control) settings to limit web traffic and prioritize reflexded UDP
- adding donation links!
- the current replay frontend is ugly and has no filtering, there are some `ideas.md`/`TODO.md` files in the repo, so I
  won't cover details here
- updating reflexded automatically (for now keeping things manual so nothing silently breaks + it can be complicated)
