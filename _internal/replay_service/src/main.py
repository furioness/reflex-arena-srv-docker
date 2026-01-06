import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import batched
from pathlib import Path
from queue import SimpleQueue
from typing import Callable

from sortedcontainers import SortedListWithKey

from replay_parser import (
    parse_and_ensure_compression as parse_replay,
    Replay,
    ReplayMetadata,
    Player,
)

REPLAY_FOLDER = Path("./replays")
DB_PATH = Path("./db/")
DB_HEADER_PATH = DB_PATH / "replays_header.json"
HEADER_VERSION = 1
CHUNK_MAX_SIZE = 250  # changing will require dropping DB


@dataclass(frozen=True)
class ReplayEvent:
    path: Path


class CleanUpEvent: ...


class ReplayDB:
    def __init__(
            self,
            path: Path,
            replay_folder: Path,
            reconcile_on_init=True,
    ):
        self.path = path
        self.replay_folder = replay_folder

        self.reconcile_on_init = reconcile_on_init
        self.by_filename: dict[str, Replay] = {}

        self._sort_key: Callable[[Replay], datetime] = lambda replay: replay.finished_at
        self.by_time: SortedListWithKey[Replay, datetime] = SortedListWithKey(
            key=self._sort_key
        )

        self._unsaved_mutated: set[Replay] = set()
        self._unsaved_added: set[Replay] = set()

        self._load_or_init_on_fs()

        if self.reconcile_on_init:
            self.reconcile()

    def _load_or_init_on_fs(self):
        """
        header.json
        ```json
            "version": 1,
            "updated_at": 171232131,
            "total_count": 937,
            "chunks": [{
                "filename": "chunk_1_hash_hgx234ja.json",
                "latest_replay_ts": 171232131,
                "oldest_replay_ts": 17041223,
                "count": 25,
            }, {...}, ...]
        ```

        chunk_1_hash_hgx234ja.json
        ```json
            {
                "The_Purple_Catalyst_pla1_pla2_01Dec2025_065955_0markers.rep": {
                    "finishedAt": 17041223,
                    "downloadable": true,
                    "metadata": {
                       "protocol_version": 89
                        "host_name": "Bobr #1"
                        "game_mode": "1v1"
                        "map_steam_id": 3459056036
                        "map_title": "The Purple Catalyst"
                        "players": [
                            {"name": "pla1", "score": 8, "team": 0, "steam_id": 1234567890},
                            {...}
                        ]
                        marker_count: 0
                        startedAt: 17040223
                    }
                },
                "...": {}
            }
        ```
        """
        if DB_HEADER_PATH.exists():
            with open(DB_HEADER_PATH, "r") as header_f:
                header = json.load(header_f)
            if header["version"] != HEADER_VERSION:
                raise ValueError(f"Unsupported header version: {header['version']}")
            total_replay_count = 0
            for chunk_meta in header["chunks"]:
                with open(DB_PATH / chunk_meta["filename"], "r") as chunk_f:
                    chunk = json.load(chunk_f)
                chunk_replay_count = 0
                for filename, replay_data in chunk.items():
                    replay = Replay(
                        filename=filename,
                        finished_at=datetime.fromisoformat(replay_data["finished_at"]),
                        downloadable=replay_data["downloadable"],
                    )
                    if meta := replay_data["metadata"]:
                        replay.metadata = ReplayMetadata(
                            protocol_version=meta["protocol_version"],
                            host_name=meta["host_name"],
                            game_mode=meta["game_mode"],
                            map_steam_id=meta["map_steam_id"],
                            map_title=meta["map_title"],
                            players=[Player(**p) for p in meta["players"]],
                            marker_count=meta["marker_count"],
                            started_at=datetime.fromisoformat(meta["started_at"]),
                        )
                    self.add_if_missing(replay)
                    chunk_replay_count += 1
                assert chunk_replay_count == chunk_meta["count"]
                total_replay_count += chunk_replay_count
            assert total_replay_count == header["total_count"]
            self._unsaved_added.clear()
            self._unsaved_mutated.clear()
        else:  # init empty db
            DB_PATH.mkdir(parents=True, exist_ok=True)
            self._write_atomic(
                DB_HEADER_PATH,
                json.dumps(
                    {
                        "version": HEADER_VERSION,
                        "updated_at": datetime.now().isoformat(),
                        "chunks": [],
                        "total_count": 0,
                    },
                ),
            )

    def save_to_fs(self):
        """
        db_dir = Path("/replays_db")

        for tmp in db_folder.glob("*.tmp"):
            tmp.unlink()

        tmp_dir = db_dir.with_name(db_dir.name + ".tmp")

        # build everything in tmp_dir
        tmp_dir.mkdir(exist_ok=True)

        write_chunks(tmp_dir)
        write_header(tmp_dir)

        # atomic swap
        tmp_dir.replace(db_dir)


        1. Full DB dump:
        - get sorted replays
        - batch them
        - for each batch, write out chunk
        - save chunks to the header

        2. Single element change:
            - get idx
            - get related chunk
            - recreate the chunk, calculate hash
            - replace old chunk with the new one in the header

        3. Few elements change:
            - the same as with a single element
            - but don't write out chunks until everything is processed
            -- better: write out individual chunks when they are fully processed

        header update:
            - read the header
            - keep a list of changed junks
            - write out chunks with hash in the name
            - replace chunks by index
            - write out updated header (tmp + mv)

        questions:
            - given db_replay idx, which chunk needs updating
            - get all affected chunk idxs
            - write out updated chunks, update header

        chunk update:
            - get chunk idx
            - write out updated chunk, calculate hash, mv with updated name
            - update header
            - write out header

        replay_idx -> chunk_idx:
        replay_idx // CHUNK_MAX_SIZE
        CS = 10
        idx = 3 -> 0
        idx = 11 -> 1
        idx = 9 -> 0
        """

        if not self._unsaved_added and not self._unsaved_mutated:
            return

        header = json.loads(DB_HEADER_PATH.read_text())

        affected_chunk_idxs = set()
        if self._unsaved_added:
            earliest_unsaved_added_idx = min(self.by_time.index(rpl) for rpl in self._unsaved_added)
            for chunk_idx in range(earliest_unsaved_added_idx // CHUNK_MAX_SIZE,
                                   len(self.by_time) // CHUNK_MAX_SIZE + 1):
                affected_chunk_idxs.add(chunk_idx)
        for replay in self._unsaved_mutated:
            affected_chunk_idxs.add(self.by_time.index(replay) // CHUNK_MAX_SIZE)

        self._unsaved_added.clear()
        self._unsaved_mutated.clear()

        old_chunk_paths = {
            header["chunks"][idx]["filename"]
            for idx in filter(
                lambda idx: idx < len(header["chunks"]), affected_chunk_idxs
            )
        }

        for chunk_idx, chunk in enumerate(batched(self.by_time, CHUNK_MAX_SIZE)):
            if chunk_idx not in affected_chunk_idxs:
                continue
            chunk = tuple(chunk)
            # chunk to chunk_json
            """
            chunk_1_hash_hgx234ja.json
            ```json
            {
                "The_Purple_Catalyst_pla1_pla2_01Dec2025_065955_0markers.rep": {
                    "finishedAt": 17041223,
                    "downloadable": true,
                    "metadata": {
                       "protocol_version": 89
                        "host_name": "Bobr #1"
                        "game_mode": "1v1"
                        "map_steam_id": 3459056036
                        "map_title": "The Purple Catalyst"
                        "players": [
                            {"name": "pla1", "score": 8, "team": 0, "steam_id": 1234567890},
                            {...}
                        ]
                        marker_count: 0
                        startedAt: 17040223
                    }
                },
                "...": {}
            }
        ```
            """
            chunk_json = {replay.filename: replay.to_jsonable() for replay in chunk}
            chunk_json = json.dumps(chunk_json).encode()

            chunk_hash = hashlib.blake2s(
                chunk_json, digest_size=6, usedforsecurity=False
            ).hexdigest()
            chunk_name = f"chunk_{chunk_idx}_{chunk_hash}.json"

            self._write_atomic(DB_PATH / chunk_name, chunk_json)

            """header
            "chunks": [{
                "filename": "chunk_1_hash_hgx234ja.json",
                "latest_replay_ts": 171232131,
                "oldest_replay_ts": 17041223,
                "count": 25,
            """
            chunk_meta = {
                "filename": chunk_name,
                "oldest_replay_ts": min(
                    chunk, key=self._sort_key
                ).finished_at.isoformat(),
                "latest_replay_ts": max(
                    chunk, key=self._sort_key
                ).finished_at.isoformat(),
                "count": len(chunk),
            }
            if chunk_idx < len(header["chunks"]):
                header["chunks"][chunk_idx] = chunk_meta
            else:
                header["chunks"].append(chunk_meta)

        header["total_count"] = sum(chunk["count"] for chunk in header["chunks"])
        header["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._write_atomic(DB_HEADER_PATH, json.dumps(header))

        # clean up
        for chunk_path in old_chunk_paths:
            (DB_PATH / chunk_path).unlink()

        for tmp in DB_PATH.glob("*.tmp"):
            tmp.unlink()

    def add_if_missing(self, replay: Replay) -> None:
        if replay.filename in self.by_filename:
            return

        self.by_filename[replay.filename] = replay
        self.by_time.add(replay)
        self._unsaved_added.add(replay)

    def _mark_fs_present(self, db_replay: Replay):
        if db_replay.downloadable:
            return
        db_replay.downloadable = True
        self._unsaved_mutated.add(db_replay)

    def _mark_fs_missing(self, db_replay: Replay):
        if not db_replay.downloadable:
            return
        db_replay.downloadable = False
        self._unsaved_mutated.add(db_replay)

    def reconcile(self):
        present_replays = set()
        for replay_path in self.replay_folder.iterdir():
            if not (
                    replay_path.name.endswith(".rep")
                    or replay_path.name.endswith(".rep.zip")
            ):
                continue

            if replay := self.by_filename.get(replay_path.name):
                self._mark_fs_present(replay)
            else:
                replay = parse_replay(replay_path)
                self.add_if_missing(replay)
            present_replays.add(replay)

        for replay in self.by_time:
            if replay not in present_replays:
                self._mark_fs_missing(replay)

        self.save_to_fs()

    @staticmethod
    def _write_atomic(path: Path, obj: str | bytes):
        tmp = path.with_suffix(path.suffix + ".tmp")
        if type(obj) is bytes:
            tmp.write_bytes(obj)
        else:
            tmp.write_text(obj)
        tmp.replace(path)


def replay_worker(queue: SimpleQueue[ReplayEvent | CleanUpEvent]):
    db = ReplayDB(DB_PATH, REPLAY_FOLDER)

    while True:
        match queue.get():
            case ReplayEvent(path=path):
                handle_replay(db, path)
            case CleanUpEvent():
                clean_up(db)
            case _:
                raise ValueError("Unknown event type")


# if __name__ == "__main__":
#     replay_queue = SimpleQueue()
#     threading.Thread(
#         target=ionotify_producer, args=(replay_queue,), daemon=True
#     ).start()
#     threading.Thread(target=replay_worker, args=(replay_queue,), daemon=True).start()
#     threading.Thread(
#         target=clean_up_producer, args=(replay_queue,), daemon=True
#     ).start()

if __name__ == "__main__":
    db = ReplayDB(DB_PATH, REPLAY_FOLDER)
