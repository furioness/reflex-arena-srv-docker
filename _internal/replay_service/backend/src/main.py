from dataclasses import dataclass
from pathlib import Path
from queue import SimpleQueue

from src.db import ReplayDB

REPLAY_FOLDER = Path("../replays")
DB_PATH = Path("../db/")


@dataclass(frozen=True)
class ReplayEvent:
    path: Path


class CleanUpEvent: ...


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
    db = ReplayDB(DB_PATH, REPLAY_FOLDER, _chunk_at_count=3)
