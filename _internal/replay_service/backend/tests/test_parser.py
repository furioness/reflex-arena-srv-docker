import zipfile
from datetime import datetime, timezone

from src import parser

import pytest

from src.model import Replay


def test_parsing_raw(single_replay):
    replay_path, expected_replay = single_replay
    parsed_replay = parser.parse_and_ensure_compressed(replay_path)

    assert replay_path.with_suffix(".rep.zip").exists()
    assert not replay_path.exists()  # don't keep uncompressed original file

    assert parsed_replay == expected_replay
    assert parsed_replay.filename == expected_replay.filename
    assert parsed_replay.finished_at == expected_replay.finished_at
    assert parsed_replay.downloadable == expected_replay.downloadable
    assert parsed_replay.metadata == expected_replay.metadata


def test_parsing_zip(single_replay_zip):
    replay_path, expected_replay = single_replay_zip
    parsed_replay = parser.parse_and_ensure_compressed(replay_path)

    assert replay_path.with_suffix(".rep.zip").exists()

    assert parsed_replay == expected_replay
    assert parsed_replay.filename == expected_replay.filename
    assert parsed_replay.finished_at == expected_replay.finished_at
    assert parsed_replay.downloadable == expected_replay.downloadable
    assert parsed_replay.metadata == expected_replay.metadata


def test_parsing_wrong_format(tmp_path):
    garbage = tmp_path / "garbage.txt"
    garbage.write_text("garbage")

    with pytest.raises(ValueError):
        parser.parse_and_ensure_compressed(garbage)


def test_parsing_unsupported_raw(tmp_path):
    garbage = tmp_path / "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    garbage.write_text("unsupported whatever")

    assert parser.parse_and_ensure_compressed(garbage) == Replay(
        filename=garbage.with_suffix(".rep.zip").name,
        finished_at=datetime(2026, 1, 5, 16, 13, 1, tzinfo=timezone.utc),
        downloadable=True,
        metadata=None,
    )


def test_parsing_unsupported_zip(tmp_path):
    garbage = tmp_path / "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    garbage.write_text("unsupported whatever")
    with zipfile.ZipFile(garbage.with_suffix(".rep.zip"), "w") as garbage_zip:
        garbage_zip.write(garbage)

    assert parser.parse_and_ensure_compressed(
        garbage.with_suffix(".rep.zip")
    ) == Replay(
        filename=garbage.with_suffix(".rep.zip").name,
        finished_at=datetime(2026, 1, 5, 16, 13, 1, tzinfo=timezone.utc),
        downloadable=True,
        metadata=None,
    )


def test_failing_parse_with_bad_name(tmp_path):
    garbage = (
        tmp_path / "Pocket_Infinity_Vigur_Ivan_O__05Jan20UGANDA26_161301_0markers.rep"
    )
    garbage.touch()

    with pytest.raises(ValueError):
        parser.parse_and_ensure_compressed(garbage)
