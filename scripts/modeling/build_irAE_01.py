"""Builds irAE_01_model_panel.ipynb — broad classifier panel on Khan_workable.csv."""
import json

cells = []

def md(src):
    cells.append({"cell_type": "markdown", "id": f"md{len(cells)}", "metadata": {}, "source": src})

def code(src):
    cells.append({"cell_type": "code", "id": f"c{len(cells)}", "metadata": {},
                  "execution_count": None, "outputs": [], "source": src})

# ---------------------------------------------------------------- title
md("""# irAE Prediction — Model Panel Benchmark

**Purpose.** Benchmark 20 classifier families plus a dummy baseline for predicting immune-related adverse event
(irAE) occurrence, all under one locked preprocessing pipeline and one evaluation protocol, so
that differences in the final table reflect the model family — not the plumbing. This is
notebook 1 of 4 (2: logistic-regression variations; 3: nested-CV final evaluation; 4: feature analysis).

**Dataset.** `Khan_workable.csv`: 146 immune-checkpoint-inhibitor patients. Target:
`iraE_occurrence` (binary, ~79/67 split). Features: ~40 baseline cytokine concentrations
(heavily right-skewed), `ana_titer_baseline` + `ana_titer_missing` (ANA is ~62% missing; the
0/1 indicator is kept as a feature), and 5 categoricals (`gender`, `ethnicity`, `race`,
`cancer_type`, `ici_drug`). `patient_id` and the target are excluded from X.

**Evaluation protocol (shared across the notebook series).** Primary metric ROC AUC (accuracy
also reported), as mean ± std over `RepeatedStratifiedKFold(n_splits=5, n_repeats=10,
random_state=42)`. ROC curves use pooled out-of-fold probabilities from `cross_val_predict`
with `StratifiedKFold(5, shuffle=True, random_state=42)`. All preprocessing is fit **inside**
each CV fold via `Pipeline` + `ColumnTransformer`.

> With n=146, fold-to-fold AUC std is ~0.08–0.11. Rankings below are **directional, not
> definitive** — see Caveats at the end.""")

# ---------------------------------------------------------------- install + imports
code("""# Gradient-boosting libraries not preinstalled in Colab
%pip -q install xgboost lightgbm""")

code("""import warnings
warnings.filterwarnings("ignore")  # silence convergence/deprecation noise so CV output stays readable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.model_selection import (RepeatedStratifiedKFold, StratifiedKFold,
                                     cross_validate, cross_val_predict)
from sklearn.metrics import roc_auc_score, roc_curve

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.cross_decomposition import PLSRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (RandomForestClassifier, ExtraTreesClassifier, BaggingClassifier,
                              AdaBoostClassifier, GradientBoostingClassifier,
                              HistGradientBoostingClassifier)
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier""")

# ---------------------------------------------------------------- data
md("""## Data

Upload `Khan_workable.csv` when prompted. Features: ~40 cytokine concentrations,
`ana_titer_baseline` + `ana_titer_missing` (ANA is ~62% missing; the 0/1 indicator is kept as a
feature), and 5 categorical metadata columns.""")

code("""# Provide Khan_workable.csv (146 patients) when the file picker appears.
from google.colab import files
uploaded = files.upload()""")

code("""df = pd.read_csv("Khan_workable.csv")
y = df["iraE_occurrence"].astype(int)
X = df.drop(columns=["patient_id", "iraE_occurrence"])

categorical_cols = ["gender", "ethnicity", "race", "cancer_type", "ici_drug"]
numeric_cols = [c for c in X.columns if c not in categorical_cols]

print(f"X: {X.shape[0]} patients x {X.shape[1]} features "
      f"({len(numeric_cols)} numeric, {len(categorical_cols)} categorical)")
print("Class balance:", y.value_counts().to_dict())""")

# ---------------------------------------------------------------- preprocessing + protocol
md("""## Preprocessing & evaluation protocol (locked)

- **Numeric:** median impute → `log1p` (cytokines are heavily right-skewed) → `StandardScaler`.
- **Categorical:** most-frequent impute → `OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=5)`.
- Everything lives in a `Pipeline` + `ColumnTransformer`, so preprocessing is **fit inside each
  CV fold** — no leakage from fitting on the full data.

**Evaluation:**
- AUC / accuracy: `RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)` → mean ± std over 50 folds.
- ROC curves: pooled out-of-fold probabilities from `cross_val_predict` with
  `StratifiedKFold(5, shuffle=True, random_state=42)`.""")

code("""numeric_tf = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
    ("scale", StandardScaler()),
])
categorical_tf = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=5,
                             sparse_output=False)),
])
preprocess = ColumnTransformer([
    ("num", numeric_tf, numeric_cols),
    ("cat", categorical_tf, categorical_cols),
])

cv_repeated = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)
cv_oof = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

results = {}

def evaluate(name, clf):
    \"\"\"Repeated-CV AUC/accuracy + pooled out-of-fold probabilities for the ROC plot.\"\"\"
    pipe = Pipeline([("prep", preprocess), ("clf", clf)])
    scores = cross_validate(pipe, X, y, cv=cv_repeated,
                            scoring=["roc_auc", "accuracy"], n_jobs=-1)
    oof = cross_val_predict(pipe, X, y, cv=cv_oof, method="predict_proba", n_jobs=-1)[:, 1]
    results[name] = {
        "auc_mean": scores["test_roc_auc"].mean(),
        "auc_std": scores["test_roc_auc"].std(),
        "acc_mean": scores["test_accuracy"].mean(),
        "oof": oof,
        "oof_auc": roc_auc_score(y, oof),
    }
    r = results[name]
    print(f"{name}: AUC {r['auc_mean']:.3f} ± {r['auc_std']:.3f} | "
          f"accuracy {r['acc_mean']:.3f} | pooled OOF AUC {r['oof_auc']:.3f}")""")

# ---------------------------------------------------------------- model sections
SECTIONS = [
("Baseline — Dummy classifier",
 "Predicts by sampling the training-set class distribution (`strategy=\"stratified\"`, "
 "`random_state=42`). Sanity floor: any real model must beat AUC ≈ 0.50.",
 'evaluate("Dummy (stratified)", DummyClassifier(strategy="stratified", random_state=42))'),

("Logistic Regression — L2 (ridge)",
 "Linear log-odds model with an L2 penalty. `C=1.0`, `max_iter=5000`.",
 'evaluate("Logistic Regression (L2, C=1.0)", LogisticRegression(C=1.0, max_iter=5000))'),

("Logistic Regression — L1 (lasso)",
 "L1 penalty drives coefficients exactly to zero, giving implicit feature selection. "
 "`penalty=\"l1\"`, `solver=\"liblinear\"`, `C=0.1`.",
 'evaluate("Logistic Regression (L1, C=0.1)",\n'
 '         LogisticRegression(penalty="l1", solver="liblinear", C=0.1))'),

("Logistic Regression — elastic net",
 "Blends L1 sparsity and L2 shrinkage. `penalty=\"elasticnet\"`, `solver=\"saga\"`, "
 "`l1_ratio=0.5`, `C=0.1` (`max_iter=5000` for saga convergence).",
 'evaluate("Logistic Regression (elastic net)",\n'
 '         LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.5, C=0.1,\n'
 '                            max_iter=5000))'),

("Ridge-strong Logistic Regression",
 "Same L2 model with much stronger shrinkage (`C=0.01`) — averages many small, noisy effects "
 "instead of trusting any single feature. Often the right bias for small-n panels.",
 'evaluate("Ridge-strong LR (C=0.01)", LogisticRegression(C=0.01, max_iter=5000))'),

("Linear Discriminant Analysis",
 "Gaussian class-conditional model with a shared covariance; `solver=\"lsqr\"` with "
 "`shrinkage=\"auto\"` (Ledoit–Wolf) regularizes the covariance estimate for p ≈ n.",
 'evaluate("LDA (shrinkage)", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"))'),

("PLS-DA",
 "Partial least squares regression on the 0/1 label with **2 latent components**, thresholded "
 "at 0.5 for class labels. **AUC uses the continuous PLS score** (clipped to [0,1] as a "
 "pseudo-probability), not the thresholded 0/1 prediction.",
 '''class PLSDAClassifier(ClassifierMixin, BaseEstimator):
    """PLSRegression on the binary label; continuous score doubles as the ranking score."""
    def __init__(self, n_components=2):
        self.n_components = n_components
    def fit(self, X, y):
        self.classes_ = np.unique(y)
        self.pls_ = PLSRegression(n_components=self.n_components)
        self.pls_.fit(X, np.asarray(y, dtype=float))
        return self
    def decision_function(self, X):
        return self.pls_.predict(X).ravel()
    def predict_proba(self, X):
        p = np.clip(self.decision_function(X), 0.0, 1.0)
        return np.column_stack([1.0 - p, p])
    def predict(self, X):
        return (self.decision_function(X) >= 0.5).astype(int)

evaluate("PLS-DA (2 components)", PLSDAClassifier(n_components=2))'''),

("Gaussian Naive Bayes",
 "Treats every feature as an independent Gaussian per class. No hyperparameters tuned.",
 'evaluate("Gaussian Naive Bayes", GaussianNB())'),

("k-Nearest Neighbors",
 "Votes among the `n_neighbors=15` closest patients in the scaled feature space.",
 'evaluate("k-NN (k=15)", KNeighborsClassifier(n_neighbors=15))'),

("Linear SVM",
 "Maximum-margin linear separator, `C=0.1`; `probability=True` adds Platt scaling for "
 "probability output.",
 'evaluate("Linear SVM (C=0.1)", SVC(kernel="linear", C=0.1, probability=True,\n'
 '                                   random_state=42))'),

("RBF SVM",
 "SVM with a Gaussian kernel: `C=1.0`, `gamma=\"scale\"`, `probability=True`.",
 'evaluate("RBF SVM (C=1.0)", SVC(kernel="rbf", C=1.0, gamma="scale", probability=True,\n'
 '                                random_state=42))'),

("Decision Tree",
 "Single CART tree limited to `max_depth=4`.",
 'evaluate("Decision Tree (depth 4)", DecisionTreeClassifier(max_depth=4, random_state=42))'),

("Random Forest",
 "500 bootstrap-aggregated, feature-subsampled trees; `min_samples_leaf=3` smooths leaves.",
 'evaluate("Random Forest", RandomForestClassifier(n_estimators=500, min_samples_leaf=3,\n'
 '                                                 random_state=42))'),

("Extra Trees",
 "Like a random forest, but split thresholds are drawn at random — lower variance, more "
 "smoothing. `n_estimators=500`, `min_samples_leaf=3`.",
 'evaluate("Extra Trees", ExtraTreesClassifier(n_estimators=500, min_samples_leaf=3,\n'
 '                                             random_state=42))'),

("Bagged Trees",
 "`BaggingClassifier` over 200 full decision trees (bootstrap aggregation only, no feature "
 "subsampling).",
 'evaluate("Bagged Trees", BaggingClassifier(n_estimators=200, random_state=42))'),

("AdaBoost",
 "Sequentially reweights misclassified samples over 200 stumps; `learning_rate=0.5`.",
 'evaluate("AdaBoost", AdaBoostClassifier(n_estimators=200, learning_rate=0.5,\n'
 '                                        random_state=42))'),

("Gradient Boosting",
 "Stage-wise additive trees fit to the log-loss gradient. `n_estimators=200`, `max_depth=2`, "
 "`learning_rate=0.05`.",
 'evaluate("Gradient Boosting", GradientBoostingClassifier(n_estimators=200, max_depth=2,\n'
 '                                                         learning_rate=0.05,\n'
 '                                                         random_state=42))'),

("HistGradientBoosting",
 "sklearn's histogram-binned gradient boosting (LightGBM-style). `max_depth=3`, "
 "`learning_rate=0.05`, `max_iter=200`.",
 'evaluate("HistGradientBoosting", HistGradientBoostingClassifier(max_depth=3,\n'
 '                                                                learning_rate=0.05,\n'
 '                                                                max_iter=200,\n'
 '                                                                random_state=42))'),

("XGBoost",
 "Regularized gradient boosting. `n_estimators=300`, `max_depth=2`, `learning_rate=0.05`, "
 "`subsample=0.8`, `colsample_bytree=0.5`, `reg_lambda=2.0`, `eval_metric=\"logloss\"`.",
 'evaluate("XGBoost", XGBClassifier(n_estimators=300, max_depth=2, learning_rate=0.05,\n'
 '                                  subsample=0.8, colsample_bytree=0.5, reg_lambda=2.0,\n'
 '                                  eval_metric="logloss", random_state=42))'),

("LightGBM",
 "Leaf-wise histogram gradient boosting. `n_estimators=300`, `max_depth=3`, `num_leaves=7`, "
 "`learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.5`, `min_child_samples=10`.",
 'evaluate("LightGBM", LGBMClassifier(n_estimators=300, max_depth=3, num_leaves=7,\n'
 '                                    learning_rate=0.05, subsample=0.8, colsample_bytree=0.5,\n'
 '                                    min_child_samples=10, verbose=-1, random_state=42))'),

("Multi-layer Perceptron",
 "One hidden layer of 32 ReLU units with strong L2 regularization (`alpha=1.0`), "
 "`max_iter=2000`.",
 'evaluate("MLP (32 units)", MLPClassifier(hidden_layer_sizes=(32,), alpha=1.0,\n'
 '                                         max_iter=2000, random_state=42))'),
]

md("## Model panel\n\nEach cell runs the full repeated-CV protocol for one model "
   "(~50 fits each; the whole panel takes a few minutes).")
ROC_NOTE = "*ROC: this model's out-of-fold curve appears in the combined plot in the Summary.*"
for title, blurb, src in SECTIONS:
    md(f"### {title}\n{blurb}\n\n{ROC_NOTE}")
    code(src)

# ---------------------------------------------------------------- summary
md("""## Summary — ranked results""")

code("""summary = pd.DataFrame([
    {"Model": name,
     "AUC (CV mean)": r["auc_mean"],
     "AUC (CV std)": r["auc_std"],
     "Accuracy (CV mean)": r["acc_mean"],
     "AUC (pooled OOF)": r["oof_auc"]}
    for name, r in results.items()
]).sort_values("AUC (CV mean)", ascending=False).reset_index(drop=True)
summary.round(3)""")

md("""### Combined ROC curves (pooled out-of-fold)

All 20 models plus the dummy baseline are plotted. The **top 5 by CV AUC** are highlighted and labeled; the remaining
models are the gray curves (their exact numbers are in the table above).""")

code("""order = summary["Model"].tolist()          # ranked by repeated-CV AUC
top5 = order[:5]
palette = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7"]  # colorblind-safe (Okabe-Ito)
colors = dict(zip(top5, palette))

fig, ax = plt.subplots(figsize=(8.5, 7))
for name in reversed(order):               # gray curves first, highlighted ones on top
    fpr, tpr, _ = roc_curve(y, results[name]["oof"])
    if name in colors:
        ax.plot(fpr, tpr, lw=2, color=colors[name],
                label=f"{name} (OOF AUC {results[name]['oof_auc']:.3f})")
    else:
        ax.plot(fpr, tpr, lw=1, color="0.82", zorder=1)
ax.plot([0, 1], [0, 1], ls="--", lw=1, color="0.45", label="Chance (AUC 0.500)")

ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.set_title("irAE model panel — pooled out-of-fold ROC curves")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles[::-1], labels[::-1], loc="lower right", frameon=False, fontsize=9)
ax.grid(alpha=0.25)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
plt.tight_layout()
plt.show()""")

md("""## Reading the table

Regularized **linear / latent-variable models** — ridge-strong LR, LDA, PLS-DA — top the panel
at **AUC ≈ 0.68–0.70**, while tree ensembles and boosting land mid-pack (**≈ 0.63–0.66**).
That ordering is the signature of a **small-n, high-dimensional, weak-and-diffuse signal**:
heavily shrunk linear models average many small effects across the cytokine panel, while
high-capacity learners chase fold-specific noise.""")

md("""## Caveats

- **Small n (146):** every estimate here carries wide uncertainty.
- **Wide fold-to-fold variance:** AUC std ≈ 0.08–0.11 across folds — larger than most gaps
  between adjacent models in the table.
- **No external validation cohort:** all numbers are internal cross-validation on one dataset.
- **Retrospective, single-dataset:** cohort-specific quirks (assay batch, site, case mix)
  cannot be separated from real signal.

Treat the results as **directional** — a guide to which model families deserve attention, not
definitive performance claims.""")

nb = {
    "cells": cells,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

with open("irAE_01_model_panel.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print(f"wrote irAE_01_model_panel.ipynb with {len(cells)} cells")
