# Step 2 — Candidate datasets (verified 2026-11-25 from this machine)

All facts below were checked by running code on 2026-11-25. "NOT VERIFIED" marks what we could not check.

## A. Kaggle — `sumitrodatta/nba-aba-baa-stats` ("NBA Stats (1947-present)")
- URL: https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats — owner Sumitro Datta, scraped from Basketball-Reference.
- Licence (Kaggle metadata): **CC0: Public Domain**. Caveat: the underlying data come from Basketball-Reference, whose terms we could not read (see C).
- Version on 2026-11-25: **57** (last updated 2026-11-01). Zip 11,316,600 B, SHA-256 `a4e2baa37c837853cf10996168e70c6b93aca8bcb050da28bb7a304d36c4bc74`.
- Download: `GET https://www.kaggle.com/api/v1/datasets/download/sumitrodatta/nba-aba-baa-stats?datasetVersionNumber=57`
  returned 302 to a signed Google Cloud Storage URL **without credentials** (public dataset). Pinning by version works (v56 and v57 resolve to different bundles).
  Fallback if anonymous download stops working: official Kaggle API with a personal key (`kaggle.json`), never committed.
- 22 CSV files. Key ones (all 33,780 rows, seasons 1947–2027, leagues NBA/ABA/BAA):
  - `Player Per Game.csv` (32 cols), `Player Totals.csv` (33 cols), `Advanced.csv` (30 cols: per, ts_percent, usg_percent, ows, dws, ws, ws_48, obpm, dbpm, bpm, vorp, ...),
    `Per 36 Minutes.csv`, `Per 100 Poss.csv` (from 1974), `Player Shooting.csv`, `Player Play By Play.csv` (from 1997), `Player Season Info.csv` (experience).
  - **Label: `All-Star Selections.csv`** — 2,058 rows, cols `player, player_id, team, season, lg, replaced`; seasons 1951–2026; NBA 1,850 + ABA 208.
  - Also present and **leaky for our target**: `Player Award Shares.csv`, `End of Season Teams.csv`, `End of Season Teams (Voting).csv`.
- `season` = end year of the season (2024 = 2023-24). **2027 = 2026-27 in progress** (441 rows, players with ~1–6 games): no label yet, must be excluded.
- Label checks:
  - `replaced=True` (184 rows). In 2024 it marks only the **injured selections**: Embiid and Randle `True`, their replacements
    Trae Young and Scottie Barnes `False` (24 players on BBRef rosters, 26 Kaggle rows).
    **CORRECTED in Step 3:** in 2007 both the 5 injured selections AND their 5 replacements have `replaced=True` (checked on the
    BBRef 2007 page). The meaning of the flag is **inconsistent across seasons**; it cannot be used as-is.
  - LeBron James: 22 All-Star seasons 2005–2026 in Kaggle, identical to NBA.com `PlayerAwards` (2004-05 … 2025-26).
  - No NBA label rows for **1999** (lockout season, no All-Star Game).
  - NBA All-Stars per season: min 20, max 30. No duplicate (player_id, season, lg) in the label file.
  - 1 label row with no stats row: Magic Johnson 1992 (selected, no regular-season games).
- Key structure: traded players have one row per team **plus a combined row with team code `2TM`/`3TM`/...** (9,380 rows belong to duplicated (player_id, season, lg) keys). Decision needed (see open decisions).
- NBA size: 1980–2026 → 25,349 stat rows, 20,550 unique player-seasons, 47 seasons, 1,183 label rows (~5.8%).
  1997–2026 → 18,254 rows, 14,569 player-seasons, 30 seasons, 758 label rows (~5.2%). (Rates include replaced=True; final rate depends on decisions.)
- Full-season stats only: **no stats up to the All-Star break.**

## B. `nba_api` (stats.nba.com)
- Package: https://pypi.org/project/nba_api/ — version 1.12.0, **MIT** licence (package only; the data belong to NBA.com, whose terms of use we have NOT VERIFIED).
- Reachable from this machine via `nba_api` (raw curl without the browser-like headers timed out). Responses in ~4 s.
- `LeagueDashPlayerStats` (one call per season, all players): seasons **from 1996-97 only** (1995-96 and 1979-80 return 0 rows).
  2023-24 → 540 players. Accepts `date_to_nullable` → e.g. DateTo=02/15/2024 gave max GP = 56: **stats up to the All-Star break are feasible in one call per season.**
  Advanced measure type also works with DateTo (USG_PCT, TS_PCT, PIE, NET_RATING, PACE) but **no PER / WS / BPM / VORP**.
- `PlayerGameLogs` accepts date_from/date_to and season (per-game logs).
- Label: no league-wide All-Star table found; `PlayerAwards(player_id)` returns DESCRIPTION "NBA All-Star" — **one call per player** (thousands of calls).
- The All-Star Game date per season is needed as the cut-off and is not given by these endpoints (could come from BBRef All-Star pages).

## C. Basketball-Reference (direct scraping)
- https://www.basketball-reference.com — reachable (HTTP 200): `leagues/NBA_2024_per_game.html`, `leagues/NBA_2024_advanced.html` (736 rows), `allstar/NBA_2024.html`.
- `robots.txt`: `User-agent: *` → `Crawl-delay: 3`.
- **Terms of use and bot-traffic pages returned HTTP 403** to curl and to the web fetcher → **NOT VERIFIED; must be read manually in a browser.**
- All-Star label: one page per season (`allstar/NBA_YYYY.html`, tables `East`/`West` + injury notes).
- Up to the All-Star break: per player-season `players/x/<id>/splits/<YYYY>` has a "All-Star | Pre" row (counting stats + shooting %),
  and `players/x/<id>/gamelog/<YYYY>` has dated per-game rows (`player_game_log_reg`). **Feasible but ~1 request per player-season**
  (~500 per season × N seasons; at 3 s crawl delay ≈ 25 min per season, ≈ 12 h for 30 seasons), and dependent on terms we could not read.

## Recommendation (to be confirmed by the team)
Primary: **A (Kaggle sumitrodatta, pinned version 57)**. Optional second source only if we choose the "first half" prediction time: **B (`nba_api`, DateTo = All-Star break)**, which restricts coverage to 1996-97+.
