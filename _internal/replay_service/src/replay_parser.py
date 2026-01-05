import dataclasses
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Self

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


@dataclass(frozen=True)
class Player:
    name: str
    score: int
    team: int
    steam_id: int


@dataclass(frozen=True)
class ReplayMetadata:
    protocol_version: int
    host_name: str
    game_mode: str
    map_steam_id: int
    map_title: str
    players: list[Player]
    marker_count: int
    started_at: datetime

    @classmethod
    def from_construct(cls, cont: Container) -> Self:
        return cls(
            protocol_version=cont.protocol_version,
            host_name=cont.host_name,
            game_mode=cont.game_mode,
            map_steam_id=cont.map_steam_id,
            map_title=cont.map_title,
            players=[Player(**player) for player in cont.players],
            marker_count=cont.marker_count,
            started_at=cont.started_at,
        )


@dataclass
class Replay:
    filename: str  # never change!
    finished_at: datetime  # never change!
    downloadable: bool = False
    metadata: ReplayMetadata | None = None

    def __hash__(self):
        return hash(self.filename)

    def __eq__(self, other):
        return isinstance(other, Replay) and self.filename == other.filename

    def to_jsonable(self) -> dict:
        dct = dataclasses.asdict(self)
        del dct["filename"]  # no need it, though it's inconsistent
        dct["finished_at"] = dct["finished_at"].isoformat()
        dct["metadata"]["started_at"] = dct["metadata"]["started_at"].isoformat()
        return dct


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


def parse_played_at_from_filename(filename: str) -> datetime:
    "The_Catalyst_pla1_pla2_01Dec2025_065955_0markers.rep -> 01 Dec 2025 06:59:55 UTC"
    datetime_ = "_".join(filename.rsplit("_", 3)[1:3])  # 01Dec2025_065955
    return datetime.strptime(datetime_, "%d%b%Y_%H%M%S").replace(tzinfo=timezone.utc)


def parse_raw(replay: Path) -> Container:
    with open(replay, "rb") as f:
        return ReplayHeaderStruct.parse(f.read())


def parse_zip_compressed(replay: Path) -> Container:
    with zipfile.ZipFile(replay, "r") as zf:
        # assuming exactly one file inside
        replay_ = zf.namelist()[0]
        with zf.open(replay_, "r") as replay_stream:
            return ReplayHeaderStruct.parse_stream(replay_stream)


def parse_and_ensure_compression(replay_path: Path) -> Replay:
    played_at = parse_played_at_from_filename(replay_path.name)
    result = Replay(filename=replay_path.name, finished_at=played_at, downloadable=True)
    try:
        if replay_path.suffix == ".zip":
            replay_cont = parse_zip_compressed(replay_path)
        elif replay_path.suffix == ".rep":
            replay_cont = parse_raw(replay_path)
            with zipfile.ZipFile(
                replay_path.with_suffix(".rep.zip.tmp"), "w"
            ) as replay_zip:
                replay_zip.write(replay_path)
            replay_path.with_suffix(".rep.zip.tmp").replace(
                replay_path.with_suffix(".rep.zip")
            )
            replay_path.unlink()
            result.filename = replay_path.with_suffix(".rep.zip").name
        else:
            raise ValueError(f"Unsupported replay file type: {replay_path.suffix}")

        result.metadata = ReplayMetadata.from_construct(replay_cont)
    except ConstructError as exc:
        print(f"Failed to parse replay {replay_path}", exc)

    return result


if __name__ == "__main__":
    path = Path(
        "replays/The_Purple_Catalyst_fuggywuggy_luny_25Dec2025_194521_0markers.rep.zip"
    )
    print(parse_and_ensure_compression(path))
