import zipfile
from datetime import datetime, timezone

import pytest

from src.db import ReplayDB
from src.model import ParsedReplay


def test_parsing_raw(single_replay):
    replay_path, expected_replay = single_replay
    parsed_replay = ReplayDB._parse(replay_path)

    assert parsed_replay == expected_replay


def test_parsing_zip(single_replay_zip):
    replay_path, expected_replay = single_replay_zip
    parsed_replay = ReplayDB._parse(replay_path)

    assert parsed_replay == expected_replay


def test_parsing_wrong_format(tmp_path):
    garbage_path = tmp_path / "garbage.txt"
    garbage_path.write_text("garbage")

    with pytest.raises(ValueError):
        ReplayDB._parse(garbage_path)


def test_parsing_unsupported_raw(tmp_path):
    garbage = tmp_path / "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    garbage.write_text("unsupported whatever")

    assert ReplayDB._parse(garbage) == ParsedReplay(
        finished_at=datetime(2026, 1, 5, 16, 13, 1, tzinfo=timezone.utc),
        metadata=None,
    )


def test_parsing_unsupported_zip(tmp_path):
    garbage = tmp_path / "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    garbage.write_text("unsupported whatever")
    with zipfile.ZipFile(garbage.with_suffix(".rep.zip"), "w") as garbage_zip:
        garbage_zip.write(garbage)

    assert ReplayDB._parse(garbage.with_suffix(".rep.zip")) == ParsedReplay(
        finished_at=datetime(2026, 1, 5, 16, 13, 1, tzinfo=timezone.utc),
        metadata=None,
    )


def test_failing_parse_with_bad_name(tmp_path):
    garbage = (
        tmp_path / "Pocket_Infinity_Vigur_Ivan_O__05Jan20UGANDA26_161301_0markers.rep"
    )
    garbage.touch()

    with pytest.raises(ValueError):
        ReplayDB._parse(garbage)
