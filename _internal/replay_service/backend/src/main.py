import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from queue import SimpleQueue

from inotify_simple import INotify, flags

from src.cleaner import Cleaner, CleanerConfig, MiB, GiB
from src.db import ReplayDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# TODO: consume cfg from the env
REPLAY_FOLDER = Path("../replays")
DB_PATH = Path("../db/")
MIN_FREE_SPACE_RATIO = 0.2
MIN_REPLAY_RETENTION_MiB = 5_000  # 5000 MB
MIN_EXPECTED_DISK_GiB = 10  # 10 GB
CLEAN_INTERVAL_SECONDS = 60 * 60


@dataclass(frozen=True)
class ReplayEvent:
    filename: str


def replay_worker(queue: SimpleQueue[ReplayEvent], db_ready: threading.Event):
    db = ReplayDB(DB_PATH, REPLAY_FOLDER)
    db_ready.set()  # db reconciliation is finished

    while True:
        event = queue.get()
        db.ingest_replay(event.filename)
        db.save_to_fs()


def inotify_producer(queue: SimpleQueue, db_ready: threading.Event):
    inotify = INotify()
    watch_flags = flags.CLOSE_WRITE | flags.MOVED_TO | flags.MOVED_FROM | flags.DELETE

    inotify.add_watch(REPLAY_FOLDER.resolve(), watch_flags)

    db_ready.wait()

    while True:
        for event in inotify.read():
            name = event.name
            mask = flags.from_mask(event.mask)

            if flags.IGNORED in mask:
                raise RuntimeError("inotify watcher is deleted!")

            if not name or flags.ISDIR in mask:
                continue

            if flags.CLOSE_WRITE in mask or flags.MOVED_TO in mask:
                if name.endswith(".rep") or name.endswith(".rep.zip"):
                    queue.put(ReplayEvent(name))

            elif flags.DELETE in mask or flags.MOVED_FROM in mask:
                if name.endswith(".rep.zip"):
                    queue.put(ReplayEvent(name))


def cleaner(db_ready: threading.Event):
    db_ready.wait()

    Cleaner(
        CleanerConfig(
            replay_folder=REPLAY_FOLDER,
            min_free_space_ratio=MIN_FREE_SPACE_RATIO,
            min_replay_retention_bytes=MIN_REPLAY_RETENTION_MiB * MiB,
            min_expected_disk_size_bytes=MIN_EXPECTED_DISK_GiB * GiB,
            clean_interval_seconds=CLEAN_INTERVAL_SECONDS,
        )
    ).clean_up_forever()


if __name__ == "__main__":
    replay_queue = SimpleQueue()
    db_ready = threading.Event()

    threading.Thread(target=inotify_producer, args=(replay_queue, db_ready)).start()
    threading.Thread(target=replay_worker, args=(replay_queue, db_ready)).start()
    threading.Thread(target=cleaner, args=(db_ready,)).start()
