# Functional requirements for the new replays frontend
Given `replays` directory with replays in .rep or .rep.zip format:
- subscribe to events of file changes (inotify)
- parse replays on addition
- compress replays
- remove old replays when out of free space
  - when handling new replay event
  - every few hours, so the system is not overloaded
- on start, parse all not-yet-parsed replays (including the compressed ones) and compress yet uncompressed
- store metadata in a chunked format, alike HLS - small header file with links for chunks and timestamps
    - info about each junk must include data range and count of items
- using steam API to fetch urls for players avatars and map previews
  - this must be updated from time to time (probably by testing the links on 404 error)
- http frontend (using vuejs, probably)
    - rendering info per each replay, including avatars and map previews
    - polling of the metadata header file and autoupdating the list
    - loading the metadata header on each start
    - comprehensive filtering by criteria:
        - player name and steam id
          - multiple players
        - map name and steam id
        - date
        - (optionally) everything above but negated
    - laxed nginx rates for frontend files
    - TLS with autorenewal
    - donation link
    - proper browser caching configuration
- nginx and builder each in its own container
Optimistic estimate: 15 + 10 + 10 + 10 + 10 + 20 + 50 + 30 + 10 + 120 + 30 + 5 + 90 + 15 + 5 + 50 + 45 + 30 + 10 = 565 / 60 = 9.4h
