"""Read-only helpers for the Week 1 dataset audit (Module 2 - owner: Augustin Nilsson).

Nothing here modifies, filters, imputes or saves the raw data. Every function takes
DataFrames and returns new summary tables only.
"""

import numpy as np
import pandas as pd

# Keys of one stat row in the player files (one row per player, season, league, team)
ROW_KEY = ["player_id", "season", "lg", "team"]
# Keys of one player-season (our unit of analysis); traded players have several rows
PLAYER_SEASON_KEY = ["player_id", "season", "lg"]
# Basketball-Reference code for a traded player's combined row: 2TM, 3TM, 4TM, 5TM
COMBINED_TEAM_PATTERN = r"^(\d)TM$"

# A count column is "not recorded in this era" for a league-season when fewer than
# this share of rows have a value (counts are recorded for everyone or for no one).
ERA_RECORDED_MIN_SHARE = 0.5

# Percentage / rate columns and the count that is their denominator.
PERCENT_DENOMINATOR = {
    "fg_percent": "fga",
    "x3p_percent": "x3pa",
    "x2p_percent": "x2pa",
    "ft_percent": "fta",
    "e_fg_percent": "fga",
    "ts_percent": "fga_plus_fta",  # TS% = PTS / (2 * (FGA + 0.44 * FTA))
    "x3p_ar": "fga",
    "f_tr": "fga",
    "tov_percent": "fga_fta_tov",  # TOV% = TOV / (FGA + 0.44 * FTA + TOV)
}


# ---------------------------------------------------------------------------
# Missingness
# ---------------------------------------------------------------------------
def missingness_table(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Count and percentage of missing values per column (only columns with any NaN)."""
    n_missing = df.isna().sum()
    out = pd.DataFrame(
        {
            "table": table_name,
            "column": n_missing.index,
            "n_missing": n_missing.values,
            "pct_missing": (100 * n_missing / len(df)).round(2).values,
        }
    )
    return out[out.n_missing > 0].reset_index(drop=True)


def _league_season_share(df: pd.DataFrame, col: str) -> pd.Series:
    """For each row, the share of non-missing values of `col` in its (league, season)."""
    return df[col].notna().groupby([df["lg"], df["season"]]).transform("mean")


def explain_missing(core: pd.DataFrame, col: str, mp_based: bool = False) -> pd.Series:
    """Label every missing cell of `col` with a structural reason, or 'unexplained'.

    `core` must hold `col` plus the count columns (fga, fta, x3pa, x2pa, mp) of the
    same row. The "base" of a column is its denominator: the attempts for a
    percentage (see PERCENT_DENOMINATOR), minutes played for an advanced rate
    metric (mp_based=True), and nothing for a plain count. Rules, applied in order:
      1. base not recorded (NaN)                    -> 'not recorded in era'
      2. base equals 0                              -> 'zero denominator'
      3. column recorded for < 50% of league-season -> 'not recorded in era'
      4. otherwise                                  -> 'unexplained'
    """
    missing = core[col].isna()
    reason = pd.Series(pd.NA, index=core.index, dtype="string")
    base_name = PERCENT_DENOMINATOR.get(col)
    if base_name == "fga_plus_fta":
        base = core["fga"] + core["fta"]
    elif base_name == "fga_fta_tov":
        base = core["fga"] + core["fta"] + core["tov"]
    elif base_name is not None:
        base = core[base_name]
    elif mp_based:
        base = core["mp"]
    else:
        base = None  # plain count: only rule 3 can explain it

    share = _league_season_share(core, col)
    no_rule = pd.Series(False, index=core.index)
    rule1 = missing & base.isna() if base is not None else no_rule
    rule2 = (missing & ~rule1 & (base == 0)) if base is not None else no_rule
    rule3 = missing & ~rule1 & ~rule2 & (share < ERA_RECORDED_MIN_SHARE)
    reason[rule1 | rule3] = "not recorded in era"
    reason[rule2] = "zero denominator"
    reason[missing & reason.isna()] = "unexplained"
    return reason


def structural_summary(
    core: pd.DataFrame, columns: list[str], mp_based_columns: set[str] = frozenset()
) -> pd.DataFrame:
    """One row per column: missing count split by structural reason."""
    rows = []
    for col in columns:
        reason = explain_missing(core, col, mp_based=col in mp_based_columns)
        counts = reason.value_counts()
        missing_rows = core.loc[reason.notna(), "season"]
        rows.append(
            {
                "column": col,
                "n_missing": int(core[col].isna().sum()),
                "not_recorded_in_era": int(counts.get("not recorded in era", 0)),
                "zero_denominator": int(counts.get("zero denominator", 0)),
                "unexplained": int(counts.get("unexplained", 0)),
                "last_season_with_missing": (
                    int(missing_rows.max()) if len(missing_rows) else None
                ),
            }
        )
    return pd.DataFrame(rows)


def first_recorded_season(df: pd.DataFrame, col: str, league: str) -> int | None:
    """First season in which `col` is recorded for >= ERA_RECORDED_MIN_SHARE of rows."""
    sub = df[df["lg"] == league]
    share = sub[col].notna().groupby(sub["season"]).mean()
    recorded = share[share >= ERA_RECORDED_MIN_SHARE]
    return int(recorded.index.min()) if len(recorded) else None


# ---------------------------------------------------------------------------
# Keys and traded players
# ---------------------------------------------------------------------------
def traded_player_structure(totals: pd.DataFrame) -> dict:
    """Check how traded players are stored: one row per team + one combined 'kTM' row.

    Returns counts only; it does not choose which rows to keep (open decision).
    """
    combined_digit = totals["team"].str.extract(COMBINED_TEAM_PATTERN)[0]
    is_combined = combined_digit.notna()
    group_size = totals.groupby(PLAYER_SEASON_KEY)["team"].transform("size")
    multi = group_size > 1

    groups = totals[multi].assign(
        is_combined=is_combined[multi],
        combined_digit=pd.to_numeric(combined_digit[multi]),
    )
    per_group = groups.groupby(PLAYER_SEASON_KEY).agg(
        n_rows=("team", "size"),
        n_combined=("is_combined", "sum"),
        digit=("combined_digit", "max"),
    )
    # Games: combined row vs sum of the team rows
    g_combined = groups[groups.is_combined].set_index(PLAYER_SEASON_KEY)["g"]
    g_teams = groups[~groups.is_combined].groupby(PLAYER_SEASON_KEY)["g"].sum()
    g_check = (g_combined - g_teams.reindex(g_combined.index)).abs()

    return {
        "n_rows_total": int(len(totals)),
        "n_rows_combined_code": int(is_combined.sum()),
        "combined_codes": sorted(totals.loc[is_combined, "team"].unique().tolist()),
        "n_rows_TOT_code": int((totals["team"] == "TOT").sum()),
        "n_player_seasons_traded": int(len(per_group)),
        "n_rows_in_traded_groups": int(multi.sum()),
        "n_groups_without_exactly_one_combined_row": int((per_group.n_combined != 1).sum()),
        "n_groups_digit_mismatch": int(
            (per_group.digit != per_group.n_rows - per_group.n_combined).sum()
        ),
        "n_groups_combined_games_ne_sum_of_team_games": int((g_check != 0).sum()),
        "n_single_row_with_combined_code": int((is_combined & ~multi).sum()),
    }


# ---------------------------------------------------------------------------
# Leakage screening
# ---------------------------------------------------------------------------
# Player stat files: full-season aggregates (prediction-time dependent)
_SEASON_STAT_FILES = {
    "Player Per Game.csv", "Player Totals.csv", "Advanced.csv", "Per 36 Minutes.csv",
    "Per 100 Poss.csv", "Player Shooting.csv", "Player Play By Play.csv",
}
_TEAM_STAT_FILES = {
    "Team Summaries.csv", "Team Stats Per Game.csv", "Team Totals.csv",
    "Team Stats Per 100 Poss.csv", "Opponent Stats Per Game.csv", "Opponent Totals.csv",
    "Opponent Stats Per 100 Poss.csv",
}
_POST_SEASON_FILES = {
    "Player Award Shares.csv", "End of Season Teams.csv", "End of Season Teams (Voting).csv",
}
_KEY_COLUMNS = {"season", "lg"}
_IDENTITY_COLUMNS = {"player", "player_id"}
_PRE_SEASON_INFO = {"age", "pos", "experience", "ht_in_in", "wt", "birth_date", "colleges",
                    "from", "debut", "overall_pick", "round", "tm", "college", "abbreviation",
                    "arena"}

REASONS = {
    "key": "Join key (season / league). Not a performance signal.",
    "identity": "Player identity: needed as a join key but must NOT be a feature "
                "(a model could memorise past All-Stars by name/id).",
    "pre_season": "Known before the season starts (bio, draft, experience, position).",
    "team_code": "Team of the row. Value 'kTM' marks a traded player's combined row.",
    "season_stat": "Full-season aggregate: includes games played AFTER the All-Star selection "
                   "(made mid-season). SAFE only if we predict at end of regular season; "
                   "LEAKY if we predict at the All-Star break.",
    "games": "Full-season games/starts: also reflects injuries after selection. "
             "Same prediction-time dependency as other season stats.",
    "team_stat": "Team full-season aggregate (record, ratings, pace): same prediction-time "
                 "dependency; team success also influences coach votes.",
    "playoffs": "Whether the team made the playoffs: decided after the regular season, "
                "i.e. after the All-Star selection.",
    "post_season": "Post-season votes/awards (MVP shares, All-NBA, All-Defense): decided after "
                   "the season by voters who largely overlap with All-Star selection logic.",
    "career_future": "Uses information from future seasons (last season played, Hall of Fame "
                     "induction, which is heavily driven by All-Star selections).",
    "label_meta": "Exists only for selected players (All-Star team, injury-replaced flag): "
                  "encodes the label itself.",
    "attendance": "Full-season attendance: prediction-time dependent; weak, indirect signal.",
}


def classify_column(file_name: str, col: str) -> tuple[str, str]:
    """Return (verdict, reason key) for one column of one file. Rules are explicit."""
    if file_name == "All-Star Selections.csv":
        if col in ("team", "replaced"):
            return "LEAKY", "label_meta"
        return ("SUSPECT", "identity") if col in _IDENTITY_COLUMNS else ("SAFE", "key")
    if col in _KEY_COLUMNS:
        return "SAFE", "key"
    if col in _IDENTITY_COLUMNS:
        return "SUSPECT", "identity"
    if file_name in _POST_SEASON_FILES:
        return "LEAKY", "post_season"
    # Player Career Info: `to` = LAST season of the career (int year, always >= `from`;
    # e.g. Jordan 1985 -> 2003), NOT turnovers (turnovers are `tov`). `hof` = Hall of Fame.
    if file_name == "Player Career Info.csv" and col in ("to", "hof"):
        return "LEAKY", "career_future"
    if col == "playoffs":
        return "LEAKY", "playoffs"
    if col == "team":
        return "SAFE", "team_code"
    if col == "age" and file_name in _TEAM_STAT_FILES:
        return "SUSPECT", "team_stat"  # team age is weighted by minutes played that season
    if col in _PRE_SEASON_INFO:
        return "SAFE", "pre_season"
    if col in ("g", "gs") and file_name in _SEASON_STAT_FILES:
        return "SUSPECT", "games"
    if col in ("attend", "attend_g"):
        return "SUSPECT", "attendance"
    if file_name in _SEASON_STAT_FILES:
        return "SUSPECT", "season_stat"
    if file_name in _TEAM_STAT_FILES:
        return "SUSPECT", "team_stat"
    raise ValueError(f"No leakage rule for {file_name} / {col}: add one explicitly.")


def leakage_table(columns_by_file: dict[str, list[str]]) -> pd.DataFrame:
    """Classify every column of every file. Raises if any column has no rule."""
    rows = []
    for file_name, columns in columns_by_file.items():
        for col in columns:
            verdict, reason_key = classify_column(file_name, col)
            rows.append({"file": file_name, "column": col, "verdict": verdict,
                         "reason_key": reason_key, "reason": REASONS[reason_key]})
    return pd.DataFrame(rows)


def to_builtin(obj):
    """Convert numpy / pandas scalars inside nested dicts/lists to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {str(k): to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_builtin(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if obj is pd.NA:
        return None
    return obj
