# Contributions — Ownership Matrix

Team: **Augustin Nilsson**, **Basile Chabrel**. Each member owns 2 of the 4 pipeline modules.
"Owner" = accountable for the module's code, decisions and audit entries; the other member reviews.

| # | Module | Owner | Reviewer | Files | Status |
|---|--------|-------|----------|-------|--------|
| 1 | Data acquisition & cleaning | Augustin Nilsson | Basile Chabrel | `src/config.py`, `src/data/download.py`, `data/raw/` | In progress (Week 1: source selection) |
| 2 | EDA & statistical tests | Augustin Nilsson | Basile Chabrel | `src/eda/audit.py`, `notebooks/01_dataset_audit.ipynb`, `report/figures/`, `report/tables/`, `report/audit_numbers.json` | In progress (Week 1: light audit) |
| 3 | Modeling pipeline | Basile Chabrel | Augustin Nilsson | `src/models/` (TBD), `notebooks/` (TBD) | Not started (Week 2) |
| 4 | Evaluation, uncertainty & drift | Basile Chabrel | Augustin Nilsson | `src/evaluation/` (TBD), `notebooks/` (TBD) | Planned (Week 1: protocol preview in report) |

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
