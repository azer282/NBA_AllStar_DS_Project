"""Temporal train / validation / test split by target season (Module 3 - owner: Basile Chabrel).

Why not a random split? Rows of the same season share the same league context and the
same voters, and the game drifts across eras. A random split would let the model see 2020
rows while being tested on other 2020 rows: optimistic and not what happens in real use.
Here every test season comes strictly after every training season.
"""
import pandas as pd

from src.config import TARGET_COL, TRAIN_LAST_SEASON, VALIDATION_LAST_SEASON

ID_COLS = ["player_id", "season", "player"]


def feature_columns(table: pd.DataFrame) -> list[str]:
    """All columns except identifiers and the target."""
    return [c for c in table.columns if c not in ID_COLS + [TARGET_COL]]


def temporal_split(table: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return {"train", "validation", "test"} sub-tables split on the target season."""
    train = table[table["season"] <= TRAIN_LAST_SEASON]
    validation = table[table["season"].between(TRAIN_LAST_SEASON + 1, VALIDATION_LAST_SEASON)]
    test = table[table["season"] > VALIDATION_LAST_SEASON]
    # Guard: no season may appear in two sets.
    seasons = [set(part["season"]) for part in (train, validation, test)]
    assert not (seasons[0] & seasons[1] or seasons[0] & seasons[2] or seasons[1] & seasons[2])
    return {"train": train, "validation": validation, "test": test}


def describe_split(parts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One line per set: seasons, rows, positives, positive rate."""
    return pd.DataFrame([
        {
            "set": name,
            "seasons": f"{part.season.min()}-{part.season.max()}",
            "n_seasons": part.season.nunique(),
            "rows": len(part),
            "all_stars": int(part[TARGET_COL].sum()),
            "positive_rate": round(part[TARGET_COL].mean(), 4),
        }
        for name, part in parts.items()
    ])
