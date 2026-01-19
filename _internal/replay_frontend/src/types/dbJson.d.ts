interface Player {
  name: string;
  score: number;
  team: number;
  steam_id: number;
}

interface ReplayMeta {
  protocol_version: number;
  host_name: string;
  game_mode: string;
  map_steam_id: number;
  map_title: string;
  marker_count: number;
  started_at: Date;
  players: Player[];
}

interface Match {
  finished_at: Date;
  downloadable: boolean;
  metadata: ReplayMeta | null;
}

type Matches = Record<string, Match>;

interface ChunkHeader {
  filename: string;
  oldest_replay_ts: Date;
  latest_replay_ts: Date;
  count: number;
}

interface DBHeader {
  version: number;
  updated_at: Date;
  total_count: number;
  max_chunk_size: number;
  chunk_headers: ChunkHeader[];
}
