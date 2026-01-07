import json

from src.db import ReplayDB
from src.parser import parse_and_ensure_compressed


def test_init_empty_db(empty_db, replay_dir):
    ReplayDB(empty_db, replay_dir)

    header = json.loads((empty_db / "replays_header.json").read_text())
    assert header["total_count"] == 0
    assert len(tuple(empty_db.iterdir())) == 1, "Expected only a header file"


def test_load_empty_db(empty_db, replay_dir):
    db_updated_at_initial = json.loads((empty_db / "replays_header.json").read_text())[
        "updated_at"
    ]

    ReplayDB(empty_db, replay_dir)

    assert (
        db_updated_at_initial
        == json.loads((empty_db / "replays_header.json").read_text())["updated_at"]
    )


def test_load_non_empty_db_and_reconcile_downloadability(
    aerowalk_db, replay_dir, copy_replay
):
    replay_filename = "Aerowalk_Ivan_O__Vigur_24Nov2025_183934_0markers.rep"
    copied_replay_path = copy_replay(replay_filename)

    db = ReplayDB(aerowalk_db, replay_dir, _chunk_at_count=3)
    assert len(db.by_time) == 7
    for replay in db.by_time:
        if (
            replay.filename == replay_filename + ".zip"
        ):  # compresses and adds in one pass, even if non .zip
            assert replay.downloadable
        else:
            assert not replay.downloadable

    copied_replay_path.with_suffix(".rep.zip").unlink()
    db = ReplayDB(aerowalk_db, replay_dir, _chunk_at_count=3)
    assert len(db.by_time) == 7
    assert not db.by_filename[replay_filename + ".zip"].downloadable


def test_add_new_at_the_end(aerowalk_db, replay_dir, copy_replay):
    db = ReplayDB(aerowalk_db, replay_dir, _chunk_at_count=3)
    assert len(db.by_time) == 7

    replay_filename = "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    replay_copy_path = copy_replay(replay_filename)

    db.add_if_missing(parse_and_ensure_compressed(replay_copy_path))
    assert len(db.by_time) == 8


def test_reconcile_with_new_replay_played_at_mid_date(
    aerowalk_db, replay_dir, copy_replay
):
    replay_filename = "Simplicity_Ivan_O__Vigur_03Dec2025_194603_0markers.rep"
    copy_replay(replay_filename)

    db = ReplayDB(aerowalk_db, replay_dir, _chunk_at_count=3)
    assert len(db.by_time) == 8

    # new db, to see that the changes are there, and no lost updates
    db = ReplayDB(aerowalk_db, replay_dir, _chunk_at_count=3)
    assert len(db.by_time) == 8


def test_unmark_downloadable_on_reconciliation_if_missing(
    aerowalk_db, replay_dir, copy_replay
):
    db = ReplayDB(aerowalk_db, replay_dir, _chunk_at_count=3)
    assert len(db.by_time) == 7

    replay_filename = "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    replay_copy_path = copy_replay(replay_filename)

    db.add_if_missing(parse_and_ensure_compressed(replay_copy_path))
    assert len(db.by_time) == 8
