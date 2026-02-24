import {MatchNamed} from "../types/db-json";

export function orderMatches(matches: MatchNamed[]): MatchNamed[] {
    return matches.sort(
        (a, b) => b.finished_at.getTime() - a.finished_at.getTime()
    )
}
