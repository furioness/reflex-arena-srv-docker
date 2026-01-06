# Replay handler backend
### Core responsibilities:
- compress replays
- delete replays if disk space is low, starting from the oldest
- parse replays and keep a history of matches, including marker for replay downloadability
- the history artifact is a bunch of static jsons for nginx to serve
- the service must survive restarts
- the service must have a low memory/cpu footprint

## Modules
### Replay Parser
- parses headers for protocol 89, but attempts any version
- if it can't parse, at least returns `Replay.finished_at` derived from filename
- parses both compressed (.zip) and raw formats
- overwrites raw with compressed

### ReplayDB
- holds data about current and past replays
- always adds replays, only change is `downloadable` field
- produces chunked json files, that both serve as DB storage and data source for the frontend
- supports handling of old/in-between replays, though practicality for a large storage is questionable

## Invariants
- expected replay format - `.rep` or `.rep.zip`
- replay identity is filename
- `Replay.finished_at` is derived from filename and immutable, used for sorting
- replays are parsed just once
- older replays are on the lowest chunk index
- chunk index = replay_index // CHUNK_MAX_SIZE
- chunks are contiguous and ordered
- chunk filenames include content hash
- chunks can be overwritten
- any FS changes are atomic (mv .tmp target within the same FS) or eventually consistent (no raw and uncompressed replays simultaneously, clean up of old chunks, old .tmp files)
- chunking size is a constant
- must have read/write access to the DB and the replays directories
