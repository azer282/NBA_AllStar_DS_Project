# NBA All-Star Prediction — ML-2026 (ESILV)

**Authors:** Augustin Nilsson, Basile Chabrel

Predict whether an NBA player is selected as an All-Star in a given season from his statistics.

- **Unit of analysis:** one row = one player-season
- **Target:** `all_star` (1 = selected that season, 0 otherwise)
- **Known difficulties:** strong class imbalance, temporal drift, leakage risk

## Status
Week 1 — project definition and dataset selection. No model is trained yet.

## Setup (Windows, Python 3.14)
```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m ipykernel install --user --name nba-allstar
```

## Reproduce the Week 1 outputs
```powershell
# 1. Download the pinned raw data (Kaggle sumitrodatta/nba-aba-baa-stats, version 57).
#    Verifies the zip SHA-256 and writes data/raw_manifest.json. No Kaggle key needed (checked 2026-11-25).
.venv\Scripts\python.exe -m src.data.download
# 2. Run the read-only audit: writes report/figures/, report/tables/, report/audit_numbers.json
.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_dataset_audit.ipynb
```

## Structure
```
data/raw/               raw downloads (not committed, rebuilt by src/data/download.py)
data/raw_manifest.json  source, version, checksums of the raw files (committed)
data/processed/         processed data (not committed)
notebooks/              01_dataset_audit.ipynb, ...
report/                 Week 1 PDF, figures/, tables/, audit_numbers.json
src/config.py           global SEED = 42, paths, pinned data version, imported everywhere
src/data/download.py    reproducible download (Module 1)
src/eda/audit.py        read-only audit helpers (Module 2)
ai_governance/          CONTRIBUTIONS.md, PROMPT_LOG.md, AI_AUDIT.md
```

## Reproducibility
All randomness uses `SEED` from `src/config.py`. Data are downloaded by script with a pinned
version and a checksum, never by manual clicks. Running the audit notebook twice gives
byte-identical figures, tables and JSON (checked 2026-11-25).

## Module ownership
| Module | Owner |
|--------|-------|
| 1. Data acquisition & cleaning | Augustin Nilsson |
| 2. EDA & statistical tests | Augustin Nilsson |
| 3. Modeling pipeline | Basile Chabrel |
| 4. Evaluation, uncertainty & drift | Basile Chabrel |
