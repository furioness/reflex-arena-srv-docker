import zipfile
from datetime import datetime, timezone
from pathlib import Path

from construct import (
    Struct,
    PaddedString,
    Int32sl,
    Int32ul,
    Int64ul,
    BytesInteger,
    this,
    Hex,
    Timestamp,
    Container,
)
from construct.core import ConstructError

from model import ReplayMetadata, Replay

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


def _parse_finished_at_from_filename(filename: str) -> datetime:
    "The_Catalyst_pla1_pla2_01Dec2025_065955_0markers.rep -> 01 Dec 2025 06:59:55 UTC"
    datetime_ = "_".join(filename.rsplit("_", 3)[1:3])  # 01Dec2025_065955
    return datetime.strptime(datetime_, "%d%b%Y_%H%M%S").replace(tzinfo=timezone.utc)


def _parse_raw(replay: Path) -> Container:
    with open(replay, "rb") as f:
        return ReplayHeaderStruct.parse(f.read())


def _parse_zip_compressed(replay: Path) -> Container:
    with zipfile.ZipFile(replay, "r") as zf:
        # assuming exactly one file inside
        replay_ = zf.namelist()[0]
        with zf.open(replay_, "r") as replay_stream:
            return ReplayHeaderStruct.parse_stream(replay_stream)


def _ensure_compressed(replay_path: Path) -> Path:
    if replay_path.suffix == ".zip":
        return replay_path

    with zipfile.ZipFile(replay_path.with_suffix(".rep.zip.tmp"), "w") as replay_zip:
        replay_zip.write(replay_path)

    replay_path.with_suffix(".rep.zip.tmp").replace(replay_path.with_suffix(".rep.zip"))
    replay_path.unlink()
    return replay_path.with_suffix(".rep.zip")


def parse_and_ensure_compressed(replay_path: Path) -> Replay:
    parsed_meta = None
    try:
        if replay_path.suffix == ".zip":
            replay_cont = _parse_zip_compressed(replay_path)
        elif replay_path.suffix == ".rep":
            replay_cont = _parse_raw(replay_path)
        else:
            raise ValueError(f"Unsupported replay file type: {replay_path.suffix}")
        parsed_meta = ReplayMetadata.from_construct(replay_cont)
    except ConstructError as exc:
        print(f"Failed to parse replay {replay_path}", exc)

    filename = _ensure_compressed(replay_path)

    return Replay(
        filename=filename.name,
        finished_at=_parse_finished_at_from_filename(replay_path.name),
        downloadable=True,
        metadata=parsed_meta,
    )


if __name__ == "__main__":
    path = Path(
        "replays/The_Purple_Catalyst_fuggywuggy_luny_25Dec2025_194521_0markers.rep.zip"
    )
    print(parse_and_ensure_compressed(path))
