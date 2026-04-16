---
name: build-model
description: Use when the user is ready to train the severity classification model. Guides feature engineering from FAERS seriousness flags, baseline → Random Forest → XGBoost training, and evaluation with per-class metrics.
---

# Build the Severity Classification Model

Trains a 3-class classifier (Mild / Medium / Severe) on FAERS data, optionally enriched with ImmPort features.

## When This Skill Applies

- User asks to train / build / start the model
- User asks for a Colab notebook
- User asks about model performance or feature importance
- User is ready to move from data → modeling phase

## Step 1 — Clarify Target and Scope

Before writing code, confirm with the user:

1. **Combined or split model?** One model for checkpoint + CAR-T, or two separate models?
2. **Colab notebook or local script?** InspiritAI typically uses Google Colab
3. **Metric priority?** Overall accuracy, macro-F1, or recall on Severe class (clinical safety prefers high Severe recall)
4. **Interpretability requirement?** For InspiritAI, favor Random Forest feature importance + SHAP plots

## Step 2 — Feature Engineering from FAERS

**Preferred training source: `datasets/faers_quarterly/`** (2024-2025 quarterly dumps, 288K rows, 93K reports, 15 drugs, pre-computed `severity` column). The older openFDA-API pull at `datasets/faers/` (125K rows, 11 drugs) is available for cross-validation or merge-and-dedupe on `primaryid`.

The severity label is not directly in FAERS — derive it (quarterly data has this pre-computed in the `severity` column):

```python
def derive_severity(row):
    # Severe = death OR life-threatening OR disabling
    if row['seriousness_death'] == 1 or row['seriousness_life_threatening'] == 1 or row['seriousness_disabling'] == 1:
        return 'Severe'
    # Medium = hospitalization only
    if row['seriousness_hospitalization'] == 1:
        return 'Medium'
    # Mild = everything else
    return 'Mild'
```

### Input Features (from FAERS)

| Feature | Column | Transform |
|---------|--------|-----------|
| Drug | `drug_name` | One-hot encode (11 drugs) |
| Drug class | `drug_class` | Binary: Checkpoint vs CAR-T |
| Drug target | Join with `reference/immunotherapy_drugs.csv` | One-hot: PD-1 / PD-L1 / CTLA-4 / CD19 / BCMA |
| Age | `patient_age` | Numeric; impute median (74-76% coverage) |
| Age bucket | `patient_age` | Categorical: <40, 40-60, ≥60 (captures OR 1.49 threshold) |
| Sex | `patient_sex` | One-hot |
| Weight | `patient_weight_kg` | Numeric; impute median (40-43% coverage — may need `has_weight` indicator) |
| Cancer indication | `indication` | Top-N one-hot (group rare indications) |
| Report country | `country` | Top-N one-hot |
| Adverse event | `reaction` | **WARNING: data leakage risk** — the reaction itself may correlate with severity. Use `reaction_category` (grouped by MedDRA SOC) instead, or exclude entirely for a pre-treatment predictor |

### Aggregation Strategy

FAERS is one row per `(report, reaction)`. To build patient-level features:
- **Option A (reaction-level):** Each row = one prediction. Features are patient + specific adverse event.
- **Option B (report-level):** Aggregate to one row per `safetyreportid`. Severity = max across reactions.

**Recommend Option B** for pre-treatment prediction, because reactions are outputs, not inputs.

## Step 3 — Train/Test Split

- Stratified split by severity label (70/15/15 train/val/test)
- Use `random_state=42` for reproducibility
- Hold out test set until final evaluation

## Step 4 — Models (in order)

### Baseline: Logistic Regression
```python
from sklearn.linear_model import LogisticRegression
baseline = LogisticRegression(multi_class='multinomial', max_iter=1000, class_weight='balanced')
```
Purpose: sanity check and coefficient interpretability.

### Primary: Random Forest
```python
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(n_estimators=500, max_depth=20, class_weight='balanced', random_state=42, n_jobs=-1)
```
Purpose: best interpretable performer, built-in feature importance.

### Comparison: XGBoost
```python
import xgboost as xgb
model = xgb.XGBClassifier(n_estimators=500, max_depth=6, learning_rate=0.1, objective='multi:softprob', num_class=3, random_state=42)
```
Purpose: strongest benchmark (matches prior art).

## Step 5 — Evaluation

Report all of:
- **Overall accuracy**
- **Macro-F1** (balanced across 3 classes)
- **Per-class precision, recall, F1** — especially recall on Severe
- **Confusion matrix** (3x3 plot)
- **ROC-AUC** (one-vs-rest, macro-averaged)
- **Feature importance** (Random Forest) + **SHAP values** (XGBoost)

Compare against prior art:
- Beats XGBoost AUC 0.99 (BMC Med Inform 2021) is ambitious — that study had only 34 patients
- AUC > 0.80 on FAERS would be a solid result given the noise

## Step 6 — ImmPort Enrichment (Optional)

If user wants to use ImmPort SDY1733:
- Load `datasets/immport/SDY1733/SDY1733_patients_consolidated.csv`
- New features available: `bclc_stage`, `cirrhosis`, `hbv_hcv_status`, `afp_ng_ml`, `on_immunotherapy`
- **Note**: Only 10 patients actually received anti-PD-1 — too small for training, but useful as a case-study validation
- Use for **qualitative sanity check**, not quantitative benchmarking

## Step 7 — Deliverable

For InspiritAI presentation, produce:
1. **Colab notebook** (`notebooks/model_training.ipynb`) with narrative markdown cells
2. **Model card** summarizing dataset, features, metrics, limitations
3. **Feature importance plot** (top 15 features)
4. **Confusion matrix** plot
5. **Short discussion** of limitations (FAERS voluntary reporting bias, no inflammatory markers, derived severity labels)

## Do Not

- Do not train on synthetic data — the project uses real public data only
- Do not include `reaction` as a feature in pre-treatment prediction models (data leakage)
- Do not oversample too aggressively — the FAERS severity split is already balanced (~35/30/35)
- Do not claim the model is clinically validated — it is a research prototype for InspiritAI

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Age column has age units in `patient_age_unit` (801=Year, 802=Month) | Filter to Years only, or convert everything to years |
| Weight has 40% missingness | Add `has_weight` indicator feature or impute + flag |
| One report may have many reactions | Decide aggregation strategy (Step 2) before modeling |
| Country and drug_name are high-cardinality | Use top-N + "Other" bucket |
| Class imbalance illusions | Always report per-class recall, not just accuracy |
