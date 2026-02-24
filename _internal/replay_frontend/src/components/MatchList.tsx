import {MatchNamed} from "../types/db-json";
import {Match as MatchElement} from "./Match";

type Props = {
    matches: MatchNamed[];
};

export function MatchList({matches}: Readonly<Props>) {
    return (
        <>
            {matches.map(match => (
                <MatchElement match={match}/>
            ))}
        </>
    );
}