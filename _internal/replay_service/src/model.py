import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar
from typing import Self

from construct import Container


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

    @classmethod
    def from_jsonable(cls, replay_json: dict, replay_filename: str) -> Self:
        metadata = None
        if meta := replay_json["metadata"]:
            metadata = ReplayMetadata(
                protocol_version=meta["protocol_version"],
                host_name=meta["host_name"],
                game_mode=meta["game_mode"],
                map_steam_id=meta["map_steam_id"],
                map_title=meta["map_title"],
                players=[Player(**p) for p in meta["players"]],
                marker_count=meta["marker_count"],
                started_at=datetime.fromisoformat(meta["started_at"]),
            )

        return cls(
            filename=replay_filename,
            finished_at=datetime.fromisoformat(replay_json["finished_at"]),
            downloadable=replay_json["downloadable"],
            metadata=metadata,
        )

    def to_jsonable(self) -> dict:
        dct = dataclasses.asdict(self)  # this is recursive, deep-copy
        del dct["filename"]  # no need it
        dct["finished_at"] = dct["finished_at"].isoformat()
        if dct["metadata"]:
            dct["metadata"]["started_at"] = dct["metadata"]["started_at"].isoformat()
        return dct


@dataclass
class ChunkHeader:
    filename: str
    oldest_replay_ts: datetime
    latest_replay_ts: datetime
    count: int

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            d["filename"],
            datetime.fromisoformat(d["oldest_replay_ts"]),
            datetime.fromisoformat(d["latest_replay_ts"]),
            d["count"],
        )

    def to_dict(self):
        return {
            "filename": self.filename,
            "oldest_replay_ts": self.oldest_replay_ts.isoformat(),
            "latest_replay_ts": self.latest_replay_ts.isoformat(),
            "count": self.count,
        }


@dataclass
class Header:
    SUPPORTED_VERSION: ClassVar[int] = 1

    updated_at: datetime
    total_count: int
    chunk_headers: list[ChunkHeader]
    max_chunk_size: int
    version: int = SUPPORTED_VERSION

    @classmethod
    def from_dict(cls, d: dict, expected_max_chunk_size: int):
        assert d["version"] == cls.SUPPORTED_VERSION
        header = cls(
            version=d["version"],
            updated_at=datetime.fromisoformat(d["updated_at"]),
            total_count=d["total_count"],
            max_chunk_size=d["max_chunk_size"],
            chunk_headers=[ChunkHeader.from_dict(c) for c in d["chunk_headers"]],
        )
        assert header.total_count == sum(ch_h.count for ch_h in header.chunk_headers)
        assert header.max_chunk_size == expected_max_chunk_size
        return header

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
            "total_count": self.total_count,
            "max_chunk_size": self.max_chunk_size,
            "chunk_headers": [c.to_dict() for c in self.chunk_headers],
        }
