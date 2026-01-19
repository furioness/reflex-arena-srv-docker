Stage 1

- load header.js
- load all chunks into in-memory array
- render the list
- make things pretty

Stage 2

- load just the first chunk
- add pagination
- on pagination, load other chunks if needed

Stage 3

- store replays info in the indexedDB
- store chunks metadata in the indexedDB
- reload junks only if header's metadata shows it's new
- autoreload the header every 5 minutes

Stage 4

- add filtering
    - by player name or steam_id
    - by map name or map_steam_id
    - by date
    - by replaymarkers (more than 0)
    - by downloadability of replay

Stage 5

- add docker compose, make everything work

Stage 6

- add donation banner

Stage 7

- go back to backend and work on players steam avatars and map's backgrounds
