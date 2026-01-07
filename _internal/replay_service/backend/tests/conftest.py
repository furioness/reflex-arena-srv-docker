import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest
from arrow import Arrow
from src.model import Player, Replay, ReplayMetadata

ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.fixture
def single_replay(copy_replay) -> tuple[Path, Replay]:
    replay = Replay(
        filename="Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep.zip",  # even though it's not zip
        finished_at=datetime(2026, 1, 5, 16, 13, 1, tzinfo=timezone.utc),
        downloadable=True,
        metadata=ReplayMetadata(
            protocol_version=89,
            host_name="#1 Bobr Rated http://bobr.furioness.net/ - demos",
            game_mode="1v1",
            map_steam_id=609506884,
            map_title="Pocket Infinity",
            players=[
                Player(name="Ivan O.", score=12, team=0, steam_id=76561198044136441),
                Player(name="Vigur", score=20, team=0, steam_id=76561198330103432),
            ],
            marker_count=0,
            started_at=Arrow(2026, 1, 5, 16, 3, 1, tzinfo=timezone.utc),
        ),
    )
    return copy_replay(
        "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    ), replay


@pytest.fixture
def single_replay_zip(copy_replay) -> tuple[Path, Replay]:
    replay = Replay(
        filename="Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep.zip",  # even though it's not zip
        finished_at=datetime(2026, 1, 5, 16, 13, 1, tzinfo=timezone.utc),
        downloadable=True,
        metadata=ReplayMetadata(
            protocol_version=89,
            host_name="#1 Bobr Rated http://bobr.furioness.net/ - demos",
            game_mode="1v1",
            map_steam_id=609506884,
            map_title="Pocket Infinity",
            players=[
                Player(name="Ivan O.", score=12, team=0, steam_id=76561198044136441),
                Player(name="Vigur", score=20, team=0, steam_id=76561198330103432),
            ],
            marker_count=0,
            started_at=Arrow(2026, 1, 5, 16, 3, 1, tzinfo=timezone.utc),
        ),
    )
    return copy_replay(
        "Pocket_Infinity_Vigur_Ivan_O__05Jan2026_161301_0markers.rep"
    ), replay


@pytest.fixture
def replay_dir(tmp_path):
    path = tmp_path / "replays"
    path.mkdir()
    return path


@pytest.fixture
def db_dir(tmp_path):
    return tmp_path / "db"


@pytest.fixture
def empty_db(db_dir):
    shutil.copytree(ASSETS_DIR / "dbs" / "empty", db_dir)
    return db_dir


@pytest.fixture
def aerowalk_db(db_dir):
    shutil.copytree(ASSETS_DIR / "dbs" / "aerowalk", db_dir)
    return db_dir


@pytest.fixture
def copy_replay(replay_dir):
    def _copy(name: str) -> Path:
        src = ASSETS_DIR / "replays" / name
        return Path(shutil.copy(src, replay_dir))

    return _copy
