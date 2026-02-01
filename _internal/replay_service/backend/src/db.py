import hashlib
import json
import logging
import zipfile
from datetime import datetime, timezone
from itertools import batched
from pathlib import Path
from struct import error
from typing import Callable

from construct import ConstructError
from sortedcontainers import SortedListWithKey

from src.model import ChunkHeader, Header, ParsedReplay, Replay, ReplayMetadata
from src.parser import parse_finished_at, parse_raw, parse_zip_compressed

logger = logging.getLogger(__name__)


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

    def ingest_replay(self, filename: str) -> Replay | None:
        replay_path = self.replay_folder / filename
        if replay := self.by_filename.get(replay_path.name):
            if not replay_path.exists():
                self._mark_fs_missing(replay)
            else:
                self._mark_fs_present(replay)
            return replay

        if not replay_path.exists():
            return None

        logger.info(f"Ingesting new replay {replay_path.name}")

        parsing_result = self._parse(replay_path)
        compressed_path = self._ensure_compressed(replay_path)
        replay = Replay(
            filename=compressed_path.name,
            downloadable=True,
            finished_at=parsing_result.finished_at,
            metadata=parsing_result.metadata,
        )

        return self._add_if_missing(replay)

    def save_to_fs(self):
        # TODO: add debouncing, maybe
        if not self._unsaved_added and not self._unsaved_mutated:
            return

        logger.info(
            f"Saving DB to FS with {len(self._unsaved_added)} added and {len(self._unsaved_mutated)} mutated replays..."
        )

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

            # TODO: there is no need for hashing! Just use incremental numbers,
            #  and store it in the header. Or just plain timestamp
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

        logger.info("DB save completed.")

    def reconcile(self):
        logger.info("Reconciling DB with FS...")
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
                replay = self.ingest_replay(replay_path.name)

            if not replay:
                continue

            present_replays.add(replay)

        for replay in self.by_time:
            if replay not in present_replays:
                self._mark_fs_missing(replay)

        self.save_to_fs()
        logger.info("Reconciliation complete.")

    def _load_or_init_on_fs(self):
        if self._db_header_path.exists():
            logger.info("Found existing DB, loading...")
            self._load_from_fs()
        else:
            logger.info("No DB found, initializing...")
            self._init_header_fs()
        logger.info(f"Initialized DB with {len(self.by_time)} replays.")

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
                self._add_if_missing(Replay.from_jsonable(replay_data, filename))
                chunk_replay_count += 1

            assert chunk_replay_count == chunk_header.count
            total_replay_count += chunk_replay_count

        assert total_replay_count == header.total_count

        self._unsaved_added.clear()
        self._unsaved_mutated.clear()

    def _add_if_missing(self, replay: Replay) -> Replay:
        if replay.filename in self.by_filename:
            return replay

        self.by_filename[replay.filename] = replay
        self.by_time.add(replay)

        self._unsaved_added.add(replay)
        return replay

    def _mark_fs_present(self, db_replay: Replay):
        if db_replay.downloadable:
            return
        logger.info(f"Marking replay {db_replay.filename} as available for download.")
        db_replay.downloadable = True

        self._unsaved_mutated.add(db_replay)

    def _mark_fs_missing(self, db_replay: Replay):
        if not db_replay.downloadable:
            return
        logger.info(
            f"Marking replay {db_replay.filename} as not available for download."
        )
        db_replay.downloadable = False

        self._unsaved_mutated.add(db_replay)

    @classmethod
    def _parse(cls, replay_path: Path) -> ParsedReplay:
        # TODO: replay count can be parsed from replay header
        try:
            if replay_path.suffix == ".zip":
                metadata = ReplayMetadata.from_construct(
                    parse_zip_compressed(replay_path)
                )
            elif replay_path.suffix == ".rep":
                metadata = ReplayMetadata.from_construct(parse_raw(replay_path))
            else:
                raise ValueError(f"Unsupported replay file type: {replay_path.suffix}")
        except (ConstructError, error) as exc:
            metadata = None
            logger.warning(f"Failed to parse replay {replay_path}", exc_info=exc)

        return ParsedReplay(
            finished_at=parse_finished_at(replay_path.name), metadata=metadata
        )

    @staticmethod
    def _ensure_compressed(replay_path: Path) -> Path:
        if replay_path.suffix == ".zip":
            return replay_path

        with zipfile.ZipFile(
                replay_path.with_suffix(".rep.zip.tmp"), "w",
                compression=zipfile.ZIP_DEFLATED,
        ) as replay_zip:
            replay_zip.write(replay_path)

        # if we crash here, we will have dangling .tmp
        # but since the original replay is still here, it will be just rewritten

        replay_path.with_suffix(".rep.zip.tmp").replace(
            replay_path.with_suffix(".rep.zip")
        )

        # if we crash here, we will have dangling .rep,
        # but it will be processed again and removed on next reconciliation

        replay_path.unlink()

        return replay_path.with_suffix(".rep.zip")

    @staticmethod
    def _write_atomic(path: Path, obj: str | bytes):
        tmp = path.with_suffix(path.suffix + ".tmp")

        if type(obj) is bytes:
            tmp.write_bytes(obj)
        else:
            tmp.write_text(obj)

        tmp.replace(path)
