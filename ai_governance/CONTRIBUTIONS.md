# Contributions — Ownership Matrix

Team: **Augustin Nilsson**, **Basile Chabrel**. Each member owns 2 of the 4 pipeline modules.
"Owner" = accountable for the module's code, decisions and audit entries; the other member reviews.

| # | Module | Owner | Reviewer | Files | Status |
|---|--------|-------|----------|-------|--------|
| 1 | Data acquisition & cleaning | Augustin Nilsson | Basile Chabrel | `src/config.py`, `src/data/download.py`, `data/raw/` | In progress (Week 1: source selection) |
| 2 | EDA & statistical tests | Augustin Nilsson | Basile Chabrel | `src/eda/audit.py`, `notebooks/01_dataset_audit.ipynb`, `report/figures/`, `report/tables/`, `report/audit_numbers.json` | In progress (Week 1: light audit) |
| 3 | Modeling pipeline | Basile Chabrel | Augustin Nilsson | `src/features/build_dataset.py`, `src/models/`, `notebooks/02_*.ipynb`, `notebooks/03_*.ipynb` | v0.1 + v0.2 done, review pending |
| 4 | Evaluation, uncertainty & drift | Basile Chabrel | Augustin Nilsson | `src/evaluation/metrics.py`, `report/tables/week2_*`, `week3_*` | Done, review pending |

## Shared deliverables

| Deliverable | Lead | Status |
|-------------|------|--------|
| `report/Week1_Project_Definition.pdf` | Both | In progress |
| `ai_governance/PROMPT_LOG.md`, `AI_AUDIT.md` | Both (each signs own entries) | Started |

## Change log
| Date | Who | Change |
|------|-----|--------|
| 2026-11-25 | Both | Initial split confirmed: Augustin = modules 1+2, Basile = modules 3+4 |
| 2026-11-25 | Both | Added scipy (statistical tests), `src/data/download.py` stub, `report/figures/` |
| 2026-11-25 | Augustin | Step 3: `src/data/download.py` (pinned v57 + SHA-256 + `data/raw_manifest.json`), `src/eda/audit.py`, audit notebook |
| 2026-11-27 | Basile | Weeks 2-3: modelling table (D1-D4 proposed defaults), temporal split, metrics, baselines, AutoML v0.1, v0.2 (RF, HGB, MLP, ensemble), drift check. Code drafted with an LLM (Claude), declared in PROMPT_LOG P-001..P-004 and AI_AUDIT A-001..A-004. Reverted the accidental "test basile" notebook edit. |
