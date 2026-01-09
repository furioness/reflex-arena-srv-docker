import zipfile
from datetime import datetime, timezone
from pathlib import Path

from construct import (
    BytesInteger,
    Container,
    Hex,
    Int32sl,
    Int32ul,
    Int64ul,
    PaddedString,
    Struct,
    Timestamp,
    this,
)

PlayerStruct = Struct(
    "name" / PaddedString(32, "utf-8"),
    "score" / Int32sl,
    "team" / Int32sl,
    "steam_id" / Int64ul,
)

ReplayHeaderStruct = Struct(
    "tag" / Hex(BytesInteger(4)),
    "protocol_version" / Int32ul,
    # "supportedVersion" / Computed(Check(this.protocolVersion == 89)),
    # Check(this.protocol_version == 89),
    "player_count" / Int32ul,
    "marker_count" / Int32ul,
    "unknown" / Int64ul,
    "map_steam_id" / Int64ul,
    "started_at" / Timestamp(Int64ul, 1.0, 1970),
    "game_mode" / PaddedString(64, "utf-8"),
    "map_title" / PaddedString(256, "utf-8"),
    "host_name" / PaddedString(256, "utf-8"),
    "players" / PlayerStruct[this.player_count],
).compile()


def parse_finished_at(filename: str) -> datetime:
    "The_Catalyst_pla1_pla2_01Dec2025_065955_0markers.rep -> 01 Dec 2025 06:59:55 UTC"
    datetime_ = "_".join(filename.rsplit("_", 3)[1:3])  # 01Dec2025_065955
    return datetime.strptime(datetime_, "%d%b%Y_%H%M%S").replace(tzinfo=timezone.utc)


def parse_finished_at_with_fallback(filename: str, fallback: datetime) -> datetime:
    try:
        return parse_finished_at(filename)
    except ValueError:
        return fallback


def parse_raw(replay: Path) -> Container:
    with open(replay, "rb") as f:
        return ReplayHeaderStruct.parse(f.read())


def parse_zip_compressed(replay: Path) -> Container:
    with zipfile.ZipFile(replay, "r") as zf:
        # assuming exactly one file inside
        replay_ = zf.namelist()[0]
        with zf.open(replay_, "r") as replay_stream:
            return ReplayHeaderStruct.parse_stream(replay_stream)
