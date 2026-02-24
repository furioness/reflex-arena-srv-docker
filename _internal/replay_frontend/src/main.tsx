import {loadAllMatches} from "./data/api";
import {orderMatches} from "./data/transform";
import {MatchList} from "./components/MatchList";

const matches = await loadAllMatches();
const orderedMatches = orderMatches(matches);

const container = document.querySelector("#matches")!;

container.appendChild(
    <MatchList matches={orderedMatches}/>
)
