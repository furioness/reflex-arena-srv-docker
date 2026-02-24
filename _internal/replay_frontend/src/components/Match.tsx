import {MatchNamed} from "../types/db-json";
import {formatDate, getMapWorkshopUrl, getPlayerSteamProfileUrl, getReplayUrl} from "../utils/format";


type Props = {
    match: MatchNamed;
};

export function Match({match}: Readonly<Props>) {
    const meta = match.metadata;

    return (
        <div className="match-row">
            <div className="cell date">
                {formatDate(match.finished_at)}
            </div>

            {meta && (
                <>
                    <div className="cell mode">
                        {meta.game_mode}
                    </div>

                    <div className="cell download">
                        {match.downloadable ? (
                            <a href={getReplayUrl(match.filename)}>Download</a>
                        ) : (
                            <span className="disabled">Download</span>
                        )}
                    </div>

                    <div className={"cell marker-count" + (meta.marker_count > 0 ? " highlighted" : "")}>
                        {meta.marker_count}
                    </div>

                    <div className="cell map" title={meta.map_title}>
                        <a href={getMapWorkshopUrl(meta.map_steam_id)} target="_blank">
                            {meta.map_title}
                        </a>
                    </div>

                    <div className="cell players">
                        <div className="players-scroll">
                            {meta.players.map(player => (
                                <div className="player">
                                    <a
                                        href={getPlayerSteamProfileUrl(player.steam_id)}
                                        className="player-name"
                                        target="_blank"
                                    >
                                        {player.name}
                                    </a>
                                    <span className="score">{player.score}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}

            {!meta && (
                <div className="">
                    {match.downloadable ? (
                        <a href={getReplayUrl(match.filename)}>{match.filename}</a>
                    ) : (
                        <span className="disabled">{match.filename}</span>
                    )}
                </div>
            )}
        </div>
    );
}