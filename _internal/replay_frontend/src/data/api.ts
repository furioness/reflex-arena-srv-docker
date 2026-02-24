import {ChunkHeader, DBHeader, MatchesRecord, MatchNamed} from "../types/db-json";
import {DB_ROOT} from "../consts";

export async function loadAllMatches() {
    const matches: MatchNamed[] = []
    const header: DBHeader = await loadDBHeader()

    for (const chunkHeader of header.chunk_headers.slice().reverse()) {
        matches.push(...await loadChunk(chunkHeader))
    }
    console.debug(`Loaded ${Object.keys(matches).length} matches`)

    return matches
}

async function loadDBHeader() {
    const HEADER_URL = `${DB_ROOT}/replays_header.json`

    const response = await fetch(HEADER_URL)
    if (!response.ok) {
        throw new Error(`Failed fetching Replay Header DB, status: ${response.status}`)
    }

    const result: DBHeader = await response.json()
    result.updated_at = new Date(result.updated_at)
    for (const chunk of result.chunk_headers) {
        chunk.oldest_replay_ts = new Date(chunk.oldest_replay_ts)
        chunk.latest_replay_ts = new Date(chunk.latest_replay_ts)
    }
    return result
}

async function loadChunk(chunk: ChunkHeader): Promise<MatchNamed[]> {
    const response = await fetch(`${DB_ROOT}/${chunk.filename}`);
    if (!response.ok) {
        throw new Error(`Failed fetching Replay Header DB, status: ${response.status}`);
    }

    const result = (await response.json()) as MatchesRecord;

    return Object.entries(result).map(([filename, match]) => {
        const finished_at = new Date(match.finished_at);

        const metadata = match.metadata
            ? {
                ...match.metadata,
                started_at: new Date(match.metadata.started_at),
            }
            : null;

        return {
            ...match,
            finished_at,
            metadata,
            filename,
        };
    });
}

