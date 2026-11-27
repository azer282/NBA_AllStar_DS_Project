"""Central project configuration.

Every script and notebook imports its constants from here so that the
random seed, paths and thresholds are defined exactly once.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42  # global random seed, used by numpy / sklearn / bootstrap everywhere

# ---------------------------------------------------------------------------
# Paths (all relative to the project root, resolved from this file)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
REPORT_DIR = PROJECT_ROOT / "report"
FIGURES_DIR = REPORT_DIR / "figures"
TABLES_DIR = REPORT_DIR / "tables"  # CSV tables produced by notebooks, used in the PDF
AUDIT_NUMBERS_PATH = REPORT_DIR / "audit_numbers.json"  # every number quoted in the PDF

# ---------------------------------------------------------------------------
# Data source (chosen in Week 1, Step 2 — see report/step2_dataset_selection.md)
# ---------------------------------------------------------------------------
KAGGLE_DATASET = "sumitrodatta/nba-aba-baa-stats"  # Kaggle "owner/slug"
KAGGLE_VERSION = 57  # pinned dataset version: the dataset is updated during the season
# SHA-256 of the v57 zip, measured on 2026-11-25 (3 downloads, identical bytes)
KAGGLE_ZIP_SHA256 = "a4e2baa37c837853cf10996168e70c6b93aca8bcb050da28bb7a304d36c4bc74"
RAW_ZIP_PATH = DATA_RAW_DIR / "nba-aba-baa-stats_v57.zip"
RAW_FILES_DIR = DATA_RAW_DIR / "nba-aba-baa-stats_v57"  # extracted CSV files
# Committed to git (outside data/raw/, which is ignored): proves what we downloaded
RAW_MANIFEST_PATH = PROJECT_ROOT / "data" / "raw_manifest.json"

# ---------------------------------------------------------------------------
# Problem definition
# ---------------------------------------------------------------------------
TARGET_COL = "all_star"  # binary target: 1 = selected as All-Star that season

# ---------------------------------------------------------------------------
# Week 2 decisions (proposed defaults, to be confirmed by the team)
# ---------------------------------------------------------------------------
# D4: target seasons. 1981 is the first season whose previous season (1980) has
# 3-point statistics. Seasons without a label (1999 lockout) are dropped automatically.
FIRST_TARGET_SEASON = 1981
LAST_TARGET_SEASON = 2026  # 2027 is in progress and has no label yet

# Temporal split by TARGET season (never random): the model is always evaluated on
# seasons that come after the ones it learned from.
TRAIN_LAST_SEASON = 2010        # train: 1981-2010
VALIDATION_LAST_SEASON = 2017   # validation: 2011-2017 (model and threshold selection)
# test: 2018-2026, touched once at the very end

N_BOOTSTRAP = 1000  # resamples for the 95% confidence intervals

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
FIGURE_DPI = 150  # resolution of saved figures (readable when embedded in the PDF)


def ensure_dirs() -> None:
    """Create the output directories if they do not exist yet."""
    for directory in (DATA_RAW_DIR, DATA_PROCESSED_DIR, FIGURES_DIR, TABLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)
