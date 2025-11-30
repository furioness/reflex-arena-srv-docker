# Reflex Arena Dedicated server quick deployment

A simpler way to host dedicated Reflex Arena servers with the following features:
- quick deployment and auto start on system reboot, thanks to Docker Compose
- integration with stats from reflexarena.ru
- replays sharing with limited speed
- replays compression
- replays clean up on low disk space
- auto-updating custom rulesets


## How to
- get a Linux machine with Docker and Docker Compose installed
- clone the repo and `cd` into it
- edit configs (details are below): `docker-compose.yml` and `docker/dedicatedserver.cfg`
- make sure the ports are open 
  - 25787, 25788, etc, for each server; UDP, and maybe TCP too
  - 80 for the replays web page
- run docker compose up
- profit!!!

## Quirks/specifics
### Adding/removing server instances
So far the method is to edit docker-compose.yml and add/remove dedX services. Make sure you don't duplicate ports (both in the service itself and the SRV_ARGS line) and server names.
So SRV_ARGS for a specific instance, `docker/dedicatedserver.cfg` for all.


### Reflexarena.ru and the cracked reflexded.exe
There is reflexarenaded.exe patched as by these instructions https://github.com/sesencheg/reflex-arena.ru 
It can be problematic if suddenly we get a new reflexded build (was highly unlikely at the moment of creation all of this).
If this happens, comment out line `cp /docker/reflexded.exe .` in `docker/install_reflexded.sh`.

### Ports
I'm not sure whether both TCP and UDP opened ports are required, but it shouldn't hurt to open them.
Also, don't do tricks like using different ports in the server's config and the one exposed in Docker, as a server reports its open port to the Steam master server, so the server can be listed in the server browser.
And yes, make sure it isn't blocked by a firewall.

### Replays
Replays are removed once the system has used more than the specified amount of free disk space, as per `docker/cleanup_replays.sh`.
If you are using cheap hosting with a small amount of storage, logs and package manager cache can quickly eat up the space, so you end up without any replays at all.

### Rulesets
If you want to have your ruleset, you have to make a pull request to this repo https://github.com/Nailok/reflex_rulesets.git
You can tag D-X in the Reflex Arena RU Discord server https://discord.com/invite/vQ3rx5m to speed up things.

### Server doesn't load some maps from the workshop
Check the logs (`docker compose logs -f ded1` and try the thing on that server), if you see something like `Crypto API failed certificate check, error flags 0x00000008 for '/CN=cache7-waw1.steamcontent.com'`, then the system's certificate storage must be outdated.
Using a fresh wine version must fix the thing. Simply run `docker compose up --build -d` to rebuild the image.


## Possible future improvements
- switch to native Linux build
- use an event-based approach for
  - rulesets: there must be some way to subscribe and keep listening for GitHub events
  - replays: there are tons of ionotify libs to listen for files, so the compressing and cleaning up can start right after the replay is completed
- better compression: if stacking replays of the same maps, it must yield significantly better compression, as a significant portion of a replay is an embedded map itself
- local rulesets: an option to use local rulesets
- sanitized rulesets: there is a possibility that things like `sv_refpassword` can be included in it - need to sanitize
- all the shenanigans with Docker: use Incus instead, and merge things
- add/remove instances: some script to simplify things, that won't require manual edit of configs
- TLS for the replay web server
- a nicer replays web page
- health checks
- using image repos instead of building everything locally (but you must trust the repo)
- replace cracked reflexded.exe with cracking script, so there won't be any obscure executable
- a better folder structure - why storing `dedicatedserver.cfg` in the `docker` folder?
