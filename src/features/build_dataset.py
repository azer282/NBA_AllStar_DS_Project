"""Build the modelling table: one row per NBA player-season, target `all_star`.

Module 1 helper written for Modules 3-4 (owner: Basile Chabrel, reviewer: Augustin Nilsson).
It turns the raw Kaggle files into data/processed/model_table_<mode>.csv.

Decisions implemented here (defaults proposed in Week 1, section 8; change them in
src/config.py, never in this file):

D1 traded players   -> keep ONE row per (player_id, season): the combined 2TM/3TM/... row
                       when it exists, otherwise the single team row.
D2 prediction time  -> two modes:
                       "prev" (main model): features = statistics of season s-1 only.
                              Everything is known before season s starts, so no leakage.
                       "full" (leakage demonstration only): features = statistics of season s,
                              which include games played AFTER the All-Star selection.
D3 replacements     -> every row of All-Star Selections.csv counts as a positive.
D4 season range     -> target seasons FIRST_TARGET_SEASON .. LAST_TARGET_SEASON
                       (seasons without a label, e.g. 1999, are dropped).

Usage (from the project root):
    python -m src.features.build_dataset
"""
import pandas as pd

from src.config import (
    DATA_PROCESSED_DIR,
    FIRST_TARGET_SEASON,
    LAST_TARGET_SEASON,
    RAW_FILES_DIR,
    TARGET_COL,
    ensure_dirs,
)

KEY = ["player_id", "season"]

# Statistics used as features. Identifiers (names, ids, team codes) are never features:
# a player id would let the model memorise who was an All-Star.
PER_GAME_COLS = [
    "g", "gs", "mp_per_game", "pts_per_game", "trb_per_game", "ast_per_game",
    "stl_per_game", "blk_per_game", "tov_per_game", "pf_per_game",
    "fga_per_game", "fta_per_game", "x3pa_per_game",
    "fg_percent", "x3p_percent", "ft_percent", "e_fg_percent",
]
ADVANCED_COLS = [
    "per", "ts_percent", "usg_percent", "ast_percent", "trb_percent", "stl_percent",
    "blk_percent", "tov_percent", "ows", "dws", "ws", "ws_48", "obpm", "dbpm", "bpm", "vorp",
]
# Stats re-expressed as a percentile rank inside their own season. Raw values drift across
# eras (pace, 3-point era); a within-season rank is comparable between 1985 and 2025.
RANKED_COLS = ["pts_per_game", "ws", "vorp", "per", "bpm", "mp_per_game"]


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_FILES_DIR / name)


def _one_row_per_player_season(df: pd.DataFrame) -> pd.DataFrame:
    """D1: keep the combined 2TM/3TM row for traded players, else the only row."""
    df = df[df["lg"] == "NBA"].copy()
    df["is_combined"] = df["team"].str.fullmatch(r"\dTM").fillna(False)
    df = df.sort_values(KEY + ["is_combined"], ascending=[True, True, False])
    return df.drop_duplicates(KEY, keep="first").drop(columns="is_combined")


def _main_team(per_game: pd.DataFrame) -> pd.DataFrame:
    """Team where the player played the most games that season (for team context)."""
    rows = per_game[(per_game["lg"] == "NBA") & ~per_game["team"].str.fullmatch(r"\dTM").fillna(False)]
    rows = rows.sort_values(KEY + ["g"], ascending=[True, True, False])
    return rows.drop_duplicates(KEY, keep="first")[KEY + ["team"]].rename(columns={"team": "main_team"})


def player_season_stats() -> pd.DataFrame:
    """One row per NBA player-season with per-game, advanced and team-context features."""
    per_game = _read("Player Per Game.csv")
    advanced = _read("Advanced.csv")
    info = _read("Player Season Info.csv")
    teams = _read("Team Summaries.csv")

    pg = _one_row_per_player_season(per_game)[KEY + ["player", "age", "pos"] + PER_GAME_COLS]
    adv = _one_row_per_player_season(advanced)[KEY + ADVANCED_COLS]
    exp = _one_row_per_player_season(info)[KEY + ["experience"]]
    stats = pg.merge(adv, on=KEY, how="left").merge(exp, on=KEY, how="left")

    # Team context: winning percentage of the player's main team that season.
    teams = teams[teams["lg"] == "NBA"].copy()
    teams["team_win_pct"] = teams["w"] / (teams["w"] + teams["l"])
    team_ctx = teams[["season", "abbreviation", "team_win_pct"]].rename(columns={"abbreviation": "main_team"})
    stats = stats.merge(_main_team(per_game), on=KEY, how="left")
    stats = stats.merge(team_ctx, on=["season", "main_team"], how="left").drop(columns="main_team")

    for col in RANKED_COLS:
        stats[f"{col}_season_rank"] = stats.groupby("season")[col].rank(pct=True)
    return stats


def all_star_labels() -> pd.DataFrame:
    """D3: every NBA row of the label file is a positive (starters, reserves, replacements)."""
    labels = _read("All-Star Selections.csv")
    labels = labels[labels["lg"] == "NBA"][KEY].drop_duplicates()
    labels[TARGET_COL] = 1
    return labels


def build_model_table(mode: str = "prev", unlabelled_season: int | None = None) -> pd.DataFrame:
    """Return the modelling table for prediction mode "prev" (no leakage) or "full" (leaky).

    unlabelled_season: build the rows of ONE season that has no label yet (e.g. 2027, in
    progress) so the trained model can score it. Its target column is left empty (NaN).
    """
    if mode not in ("prev", "full"):
        raise ValueError("mode must be 'prev' or 'full'")
    stats = player_season_stats()
    labels = all_star_labels()
    labelled_seasons = set(labels["season"])

    # Population: every player with an NBA row in the target season s.
    population = stats[["player_id", "season", "player", "age", "experience"]].copy()
    if unlabelled_season is None:
        population = population[population["season"].between(FIRST_TARGET_SEASON, LAST_TARGET_SEASON)]
        population = population[population["season"].isin(labelled_seasons)]
    else:
        population = population[population["season"] == unlabelled_season]

    # All-Star history known BEFORE season s (labels of earlier seasons only).
    history = labels.sort_values(KEY).copy()
    history["n_prev_all_star"] = history.groupby("player_id").cumcount() + 1
    hist_rows = []
    for season in population["season"].unique():
        past = history[history["season"] < season].groupby("player_id")["n_prev_all_star"].max()
        last = history[history["season"] == season - 1]["player_id"]
        hist_rows.append(pd.DataFrame({
            "player_id": past.index, "season": season, "n_prev_all_star": past.values,
        }).assign(all_star_prev_season=lambda d: d["player_id"].isin(last).astype(int)))
    hist = pd.concat(hist_rows, ignore_index=True)

    feature_cols = PER_GAME_COLS + ADVANCED_COLS + ["team_win_pct"] + [f"{c}_season_rank" for c in RANKED_COLS]
    if mode == "prev":
        feats = stats[KEY + feature_cols].copy()
        feats["season"] = feats["season"] + 1  # stats of s-1 describe target season s
        feats = feats.rename(columns={c: f"prev_{c}" for c in feature_cols})
    else:
        feats = stats[KEY + feature_cols].rename(columns={c: f"cur_{c}" for c in feature_cols})

    table = population.merge(feats, on=KEY, how="left")
    table = table.merge(hist, on=KEY, how="left")
    table[["n_prev_all_star", "all_star_prev_season"]] = table[["n_prev_all_star", "all_star_prev_season"]].fillna(0)
    if mode == "prev":
        # Rookies and players who missed season s-1 have no previous stats: flag them.
        table["has_prev_season"] = table["prev_g"].notna().astype(int)
    table = table.merge(labels, on=KEY, how="left")
    if unlabelled_season is None:
        table[TARGET_COL] = table[TARGET_COL].fillna(0).astype(int)
    return table.sort_values(KEY).reset_index(drop=True)


def main() -> None:
    ensure_dirs()
    for mode in ("prev", "full"):
        table = build_model_table(mode)
        path = DATA_PROCESSED_DIR / f"model_table_{mode}.csv"
        table.to_csv(path, index=False)
        print(f"{mode}: {len(table):,} rows, {table[TARGET_COL].sum():,} All-Stars "
              f"({table[TARGET_COL].mean():.2%}), seasons {table.season.min()}-{table.season.max()} -> {path.name}")


if __name__ == "__main__":
    main()
