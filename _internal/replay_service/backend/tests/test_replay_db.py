import json

from src.db import ReplayDB


def test_empty_replay_dir(tmp_path):
    replay_dir = tmp_path / "replays"
    db_dir = tmp_path / "db"
    replay_dir.mkdir()

    ReplayDB(db_dir, replay_dir)

    header = json.loads((db_dir / "replays_header.json").read_text())
    assert header["total_count"] == 0
    assert len(tuple(db_dir.iterdir())) == 1, "Expected only a header file"
