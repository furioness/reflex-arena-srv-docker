import hashlib
import json
from datetime import datetime, timezone
from itertools import batched
from pathlib import Path
from typing import Callable

from sortedcontainers import SortedListWithKey

from src.model import Replay, Header, ChunkHeader
from src.parser import parse_and_ensure_compressed


class ReplayDB:
    def __init__(
        self,
        path: Path,
        replay_folder: Path,
        reconcile_on_init=True,
        _chunk_at_count=250,  # changing will require dropping DB
    ):
        self._db_path = path
        self._db_header_path = path / "replays_header.json"
        self.replay_folder = replay_folder

        self.reconcile_on_init = reconcile_on_init
        self._chunk_max_size = _chunk_at_count

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
        if self._db_header_path.exists():
            self._load_from_fs()
        else:
            self._init_header_fs()

    def _init_header_fs(self):
        self._db_path.mkdir(parents=True, exist_ok=True)
        self._write_atomic(
            self._db_header_path,
            json.dumps(
                Header(
                    updated_at=datetime.now(),
                    total_count=0,
                    chunk_headers=[],
                    max_chunk_size=self._chunk_max_size,
                ).to_dict()
            ),
        )

    def _load_from_fs(self):
        with open(self._db_header_path, "r") as header_f:
            header = json.load(header_f)
        header = Header.from_dict(header, self._chunk_max_size)

        total_replay_count = 0
        for chunk_header in header.chunk_headers:
            with open(self._db_path / chunk_header.filename, "r") as chunk_f:
                chunk = json.load(chunk_f)

            chunk_replay_count = 0
            for filename, replay_data in chunk.items():
                self.add_if_missing(Replay.from_jsonable(replay_data, filename))
                chunk_replay_count += 1

            assert chunk_replay_count == chunk_header.count
            total_replay_count += chunk_replay_count

        assert total_replay_count == header.total_count

        self._unsaved_added.clear()
        self._unsaved_mutated.clear()

    def save_to_fs(self):
        if not self._unsaved_added and not self._unsaved_mutated:
            return

        header = Header.from_dict(
            json.loads(self._db_header_path.read_text()), self._chunk_max_size
        )

        affected_chunk_idxs = set()
        if self._unsaved_added:
            earliest_unsaved_added_idx = min(
                self.by_time.index(rpl) for rpl in self._unsaved_added
            )
            for chunk_idx in range(
                earliest_unsaved_added_idx // self._chunk_max_size,
                len(self.by_time) // self._chunk_max_size + 1,
            ):
                affected_chunk_idxs.add(chunk_idx)
        for replay in self._unsaved_mutated:
            affected_chunk_idxs.add(self.by_time.index(replay) // self._chunk_max_size)

        self._unsaved_added.clear()
        self._unsaved_mutated.clear()

        old_chunk_paths = {
            header.chunk_headers[idx].filename
            for idx in filter(
                lambda idx: idx < len(header.chunk_headers), affected_chunk_idxs
            )
        }

        for chunk_idx, db_chunk in enumerate(
            batched(self.by_time, self._chunk_max_size)
        ):
            if chunk_idx not in affected_chunk_idxs:
                continue

            db_chunk = tuple(db_chunk)

            chunk_json = {replay.filename: replay.to_jsonable() for replay in db_chunk}
            chunk_json = json.dumps(chunk_json).encode()

            chunk_hash = hashlib.blake2s(
                chunk_json, digest_size=6, usedforsecurity=False
            ).hexdigest()
            chunk_name = f"chunk_{chunk_idx}_{chunk_hash}.json"

            self._write_atomic(self._db_path / chunk_name, chunk_json)

            chunk_meta = ChunkHeader(
                filename=chunk_name,
                oldest_replay_ts=min(db_chunk, key=self._sort_key).finished_at,
                latest_replay_ts=max(db_chunk, key=self._sort_key).finished_at,
                count=len(db_chunk),
            )

            if chunk_idx < len(header.chunk_headers):
                header.chunk_headers[chunk_idx] = chunk_meta
            else:
                header.chunk_headers.append(chunk_meta)

        header.total_count = sum(chunk.count for chunk in header.chunk_headers)
        header.updated_at = datetime.now(timezone.utc)

        self._write_atomic(self._db_header_path, json.dumps(header.to_dict()))

        # clean up
        for chunk_path in old_chunk_paths:
            (self._db_path / chunk_path).unlink()

        for tmp in self._db_path.glob("*.tmp"):
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
                replay = parse_and_ensure_compressed(replay_path)
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
