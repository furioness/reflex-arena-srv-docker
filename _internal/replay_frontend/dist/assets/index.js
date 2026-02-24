// src/consts.ts
var DB_ROOT = "/db";
var REPLAYS_ROOT = "/replays";

// src/data/api.ts
async function loadAllMatches() {
  const matches2 = [];
  const header = await loadDBHeader();
  for (const chunkHeader of header.chunk_headers.slice().reverse()) {
    matches2.push(...await loadChunk(chunkHeader));
  }
  console.debug(`Loaded ${Object.keys(matches2).length} matches`);
  return matches2;
}
async function loadDBHeader() {
  const HEADER_URL = `${DB_ROOT}/replays_header.json`;
  const response = await fetch(HEADER_URL);
  if (!response.ok) {
    throw new Error(`Failed fetching Replay Header DB, status: ${response.status}`);
  }
  const result = await response.json();
  result.updated_at = new Date(result.updated_at);
  for (const chunk of result.chunk_headers) {
    chunk.oldest_replay_ts = new Date(chunk.oldest_replay_ts);
    chunk.latest_replay_ts = new Date(chunk.latest_replay_ts);
  }
  return result;
}
async function loadChunk(chunk) {
  const response = await fetch(`${DB_ROOT}/${chunk.filename}`);
  if (!response.ok) {
    throw new Error(`Failed fetching Replay Header DB, status: ${response.status}`);
  }
  const result = await response.json();
  return Object.entries(result).map(([filename, match]) => {
    const finished_at = new Date(match.finished_at);
    const metadata = match.metadata ? {
      ...match.metadata,
      started_at: new Date(match.metadata.started_at)
    } : null;
    return {
      ...match,
      finished_at,
      metadata,
      filename
    };
  });
}

// src/data/transform.ts
function orderMatches(matches2) {
  return matches2.sort(
    (a, b) => b.finished_at.getTime() - a.finished_at.getTime()
  );
}

// src/utils/format.ts
function formatDate(date) {
  let formatter;
  if (date.getFullYear() == (/* @__PURE__ */ new Date()).getFullYear()) {
    formatter = new Intl.DateTimeFormat(void 0, {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  } else {
    formatter = new Intl.DateTimeFormat(void 0, {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  }
  return formatter.format(date);
}
function getReplayUrl(filename) {
  return `/${REPLAYS_ROOT}/${filename}`;
}
function getPlayerSteamProfileUrl(playerSteamId) {
  return `https://steamcommunity.com/profiles/${playerSteamId}`;
}
function getMapWorkshopUrl(mapSteamId) {
  return `https://steamcommunity.com/sharedfiles/filedetails/?id=${mapSteamId}`;
}

// src/jsx-runtime/jsx-runtime.ts
function jsx(tag, props) {
  return createElement(tag, props);
}
function jsxs(tag, props) {
  return createElement(tag, props);
}
function Fragment(props) {
  const frag = document.createDocumentFragment();
  appendChildren(frag, props?.children);
  return frag;
}
function createElement(tag, props) {
  const { children, ...rest } = props ?? {};
  if (typeof tag === "function") {
    return tag({ ...rest, children });
  }
  const el = document.createElement(tag);
  for (const key in rest) {
    const value = rest[key];
    if (key === "className") {
      el.setAttribute("class", value);
    } else if (key.startsWith("on") && typeof value === "function") {
      el.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value !== false && value != null) {
      el.setAttribute(key, String(value));
    }
  }
  appendChildren(el, children);
  return el;
}
function appendChildren(parent, children) {
  if (children == null || children === false) return;
  const list = Array.isArray(children) ? children : [children];
  for (const child of list) {
    if (child == null || child === false) continue;
    if (typeof child === "string" || typeof child === "number") {
      parent.appendChild(document.createTextNode(String(child)));
    } else if (child instanceof Node) {
      parent.appendChild(child);
    }
  }
}

// src/components/Match.tsx
function Match({ match }) {
  const meta = match.metadata;
  return /* @__PURE__ */ jsxs("div", { className: "match-row", children: [
    /* @__PURE__ */ jsx("div", { className: "cell date", children: formatDate(match.finished_at) }),
    meta && /* @__PURE__ */ jsxs(Fragment, { children: [
      /* @__PURE__ */ jsx("div", { className: "cell mode", children: meta.game_mode }),
      /* @__PURE__ */ jsx("div", { className: "cell download", children: match.downloadable ? /* @__PURE__ */ jsx("a", { href: getReplayUrl(match.filename), children: "Download" }) : /* @__PURE__ */ jsx("span", { className: "disabled", children: "Download" }) }),
      /* @__PURE__ */ jsx("div", { className: "cell marker-count" + (meta.marker_count > 0 ? " highlighted" : ""), children: meta.marker_count }),
      /* @__PURE__ */ jsx("div", { className: "cell map", title: meta.map_title, children: /* @__PURE__ */ jsx("a", { href: getMapWorkshopUrl(meta.map_steam_id), target: "_blank", children: meta.map_title }) }),
      /* @__PURE__ */ jsx("div", { className: "cell players", children: /* @__PURE__ */ jsx("div", { className: "players-scroll", children: meta.players.map((player) => /* @__PURE__ */ jsxs("div", { className: "player", children: [
        /* @__PURE__ */ jsx(
          "a",
          {
            href: getPlayerSteamProfileUrl(player.steam_id),
            className: "player-name",
            target: "_blank",
            children: player.name
          }
        ),
        /* @__PURE__ */ jsx("span", { className: "score", children: player.score })
      ] })) }) })
    ] }),
    !meta && /* @__PURE__ */ jsx("div", { className: "", children: match.downloadable ? /* @__PURE__ */ jsx("a", { href: getReplayUrl(match.filename), children: match.filename }) : /* @__PURE__ */ jsx("span", { className: "disabled", children: match.filename }) })
  ] });
}

// src/components/MatchList.tsx
function MatchList({ matches: matches2 }) {
  return /* @__PURE__ */ jsx(Fragment, { children: matches2.map((match) => /* @__PURE__ */ jsx(Match, { match })) });
}

// src/main.tsx
var matches = await loadAllMatches();
var orderedMatches = orderMatches(matches);
var container = document.querySelector("#matches");
container.appendChild(
  /* @__PURE__ */ jsx(MatchList, { matches: orderedMatches })
);
