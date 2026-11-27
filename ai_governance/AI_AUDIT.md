# AI Audit

Record every flaw found in LLM-produced output (code, numbers, text, references), how it was
caught and how the fix was verified.

## Template

```
### A-XXX
- Date:
- Author:
- Module:
- Linked prompt: P-XXX
- Flaw caught:
- Root cause (why the LLM got it wrong):
- Fix:
- Verification (command / output / cell that proves the fix):
- Signed:
```

## Entries

> Drafted with the LLM (Claude); Basile must re-run each verification and sign.

### A-001
- Date: 2026-11-26
- Author: Basile Chabrel
- Module: 3-4 (prediction time, D2)
- Linked prompt: P-001
- Flaw caught: the LLM proposed the "end-of-season statistics" setup to simplify the project (calling it retrospective), while our goal is to forecast the selection, made in January: full-season statistics contain games played after it (target leakage).
- Root cause (why the LLM got it wrong): it optimised for "easiest to build" and did not tie the feature timestamp to the label timestamp of the stated goal.
- Fix: main model uses season s-1 statistics only (`build_model_table("prev")`); the leaky version is kept only to measure the effect.
- Verification: notebook 02, section 7 (`report/tables/week2_leakage_comparison.csv`): same pipeline, test PR-AUC 0.678 without leakage vs 0.852 with season-s statistics. The leaky number is optimistic by ~0.17.
- Signed: _(Basile)_

### A-002
- Date: 2026-11-26
- Author: Basile Chabrel
- Module: 4 (metrics)
- Linked prompt: P-002
- Flaw caught: the LLM recommended a "top-12 per conference" hit rate and a "rank within conference" feature. The Kaggle tables (Team Summaries, Team Abbrev) have no conference column, so neither can be computed from our data.
- Root cause: domain knowledge (All-Stars are picked per conference) was assumed to exist in the dataset without checking the columns.
- Fix: Hits@K per season, with K = number of real All-Stars that season (`src/evaluation/metrics.py::hits_at_k`).
- Verification: `pd.read_csv("data/raw/nba-aba-baa-stats_v57/Team Summaries.csv").columns` and `Team Abbrev.csv` columns: no conference field.
- Signed: _(Basile)_

### A-003
- Date: 2026-11-27
- Author: Basile Chabrel
- Module: 3 (pipeline v0.1)
- Linked prompt: P-003
- Flaw caught: the generated pipeline used `SelectKBest(mutual_info_classif)` without a random state. Mutual information uses random noise (k-NN estimator), so two runs could select different features: breaks the reproducibility rule (global SEED).
- Root cause: the LLM seeded the models but not the scoring function of the feature selector.
- Fix: `SelectKBest(partial(mutual_info_classif, random_state=SEED), ...)` in `src/models/automl_v01.py`.
- Verification: run notebook 02 twice: `report/tables/week2_automl_v01_validation.csv` is identical.
- Signed: _(Basile)_

### A-004
- Date: 2026-11-27
- Author: Basile Chabrel
- Module: 3 (hyperparameter tuning)
- Linked prompt: P-003
- Flaw caught: in the first grid, the best logistic-regression C (0.01) was the smallest value tried: the optimum could lie outside the grid, and the reported "best" model was not justified.
- Root cause: default-looking grid copied without checking where the optimum fell.
- Fix: grid extended to C in {0.001, 0.01, 0.1, 1}.
- Verification: notebook 02, section 5: best C is now 0.01, an interior point of the grid.
- Signed: _(Basile)_
