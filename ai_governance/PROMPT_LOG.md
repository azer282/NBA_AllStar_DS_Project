# Prompt Log

One entry per significant LLM interaction. Each entry is written and signed by its author.

## Template

```
### P-XXX
- Date:
- Author:
- Module:
- Goal:
- Bare prompt (what a naive request would look like):
- Constrained prompt (what we actually sent, or a faithful summary + key constraints):
- What the LLM got wrong / had to be corrected:
- What we changed / kept:
- Linked audit entries: A-XXX
- Signed:
```

## Entries

> Entries P-001 to P-004 were drafted with the LLM (Claude) itself from the conversation history
> and must be checked, corrected where needed and signed by Basile before submission.

### P-001
- Date: 2026-11-26
- Author: Basile Chabrel
- Module: 3-4 (decision D2, prediction time / leakage prevention)
- Goal: choose when the prediction is made, so that no feature contains information from after the All-Star selection.
- Bare prompt (what a naive request would look like): "Predict NBA All-Stars from player stats."
- Constrained prompt (faithful summary): "We want to predict the NEXT All-Star selection. Selections are made in January, the Kaggle data only has full-season statistics. Which features are known at prediction time? Compare: end-of-season stats, stats up to the All-Star break, previous-season stats. Give the leakage risk of each."
- What the LLM got wrong / had to be corrected: an earlier answer proposed the "end-of-season stats" setup as a way to simplify the project. It flagged it as retrospective, but this contradicts our stated goal (forecast the selection) and its effect was not measured (see A-001).
- What we changed / kept: main model = previous-season statistics only (D2 = c); the end-of-season version is kept only as a measured leakage demonstration (notebook 02, section 7).
- Linked audit entries: A-001
- Signed: _(Basile — to sign after review)_

### P-002
- Date: 2026-11-26
- Author: Basile Chabrel
- Module: 4 (metric choice under class imbalance)
- Goal: choose the evaluation metrics.
- Bare prompt: "What accuracy does the model get at detecting an All-Star?"
- Constrained prompt (faithful summary): "Positives are ~5.8 % of player-seasons. Which metrics are valid? Give the random baseline of each, and a metric a non-expert understands."
- What the LLM got wrong / had to be corrected: it first proposed a "top-12 per conference" metric; the dataset has no conference column, so the metric could not be computed as stated (see A-002).
- What we changed / kept: PR-AUC (random baseline = positive rate) as main metric, precision/recall/F1 at a threshold chosen on validation, Hits@K per season (K = real All-Stars that season), season-block bootstrap CIs. Accuracy is not used.
- Linked audit entries: A-002
- Signed: _(Basile — to sign after review)_

### P-003
- Date: 2026-11-27
- Author: Basile Chabrel
- Module: 3 (split, model selection, hyperparameter tuning)
- Goal: build the AutoML v0.1 pipeline without leakage.
- Bare prompt: "Do the Week 2 of the ML project."
- Constrained prompt (faithful summary): "Use the temporal split by season (train 1981-2010, validation 2011-2017, test 2018-2026). Fit imputation/scaling/feature selection inside a sklearn Pipeline. Select models and thresholds on validation only, score the test seasons once. Compare to non-learned baselines. Use SEED from src/config.py everywhere."
- What the LLM got wrong / had to be corrected: feature selection was not seeded (A-003); the first logistic-regression grid had its best value on the edge of the grid (A-004).
- What we changed / kept: seeded mutual information; extended the grid; `refit=False` + refit on train only so that the validation scores used for the threshold stay out-of-sample.
- Linked audit entries: A-003, A-004
- Signed: _(Basile — to sign after review)_

### P-004
- Date: 2026-11-27
- Author: Basile Chabrel
- Module: 3 (algorithm outside the course, Week 3)
- Goal: choose and justify an out-of-course algorithm with a scientific reference.
- Bare prompt: "Add a deep learning model."
- Constrained prompt (faithful summary): "Pick an algorithm outside the course, justify it with a real, checkable paper, state a hypothesis before running it, and compare it with the baseline and v0.1 under the same protocol."
- What the LLM got wrong / had to be corrected: _(to fill by Basile after checking the reference and the numbers himself)_
- What we changed / kept: MLP; reference Grinsztajn, Oyallon & Varoquaux, NeurIPS 2022, arXiv:2207.08815 (hypothesis: tree ensembles >= MLP on ~10K-row tabular data). Result: the hypothesis did NOT hold on validation (MLP best by a small margin, within noise) - reported as such.
- Linked audit entries: -
- Signed: _(Basile — to sign after review)_
