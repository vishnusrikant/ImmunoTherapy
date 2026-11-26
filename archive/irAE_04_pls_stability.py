"""irAE_04 — PLS-DA loading stability + permutation importance (Khan JITC 2025, n=146).

Fits the locked pipeline (median-impute → log1p → z-score → 3-component PLS on the 40 cytokines,
+ ANA + one-hot metadata → L2 logistic) inside RepeatedStratifiedKFold(5x4) and reports:
  * fold-averaged, sign-aligned PLS weights per cytokine (+ sign stability across folds)
  * fold-averaged, sign-aligned logistic coefficients on the PLS scores
  * per-fold test AUC (the baseline the permutation drops are measured against)
  * permutation importance (AUC drop) for every column the pipeline actually reads

Corrections vs the first draft (2026-09-20):
  1. PLS component signs are arbitrary per fit. The weights were being flipped but the logistic
     coefficients were not, so their fold average cancelled (PLS1 0.106 raw vs 0.47 aligned).
     Both are now flipped by the same per-component sign vector.
  2. Sign alignment now uses the dot product with the first fold's weight vector (robust for
     PLS2/3, where the single-cytokine Eotaxin-2 anchor is weak). PLS1 sign is then fixed so the
     Eotaxin-2 weight is positive, matching the original convention.
  3. Permutation importance runs only over columns the pipeline reads (patient_id, cancer_type,
     ici_drug and the label were dead rows in the table).
  4. Baseline test AUC per fold is printed so the drops have context.
  5. Input is coerced to numeric: works with the raw Khan_workable.csv (label strings,
     'OOR <' censoring) and the cleaned 0/1 version alike.
Interpretive note: with a binary y the first PLS weight vector is proportional to X'y, i.e. it is
exactly the vector of univariate correlations of each standardized log-cytokine with irAE
(checked: fold-wise correlation = 1.0). Treat the PLS1 ranking as a univariate ranking.
"""
import sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.cross_decomposition import PLSRegression
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance

SEED = 42
CSV = sys.argv[1] if len(sys.argv) > 1 else "Khan_workable.csv"
df = pd.read_csv(CSV)

# ---- locked cleaning ---------------------------------------------------------------------
lab = df["iraE_occurrence"]
if not pd.api.types.is_numeric_dtype(lab):  # raw file: 'Grade 0-1' / 'Grade 2+'
    lab = lab.map({"Grade 0-1": 0, "Grade 2+": 1})
y = lab.astype(int).values

df["mech"]  = df["ici_drug"].str.lower().map(
    lambda s: "CTLA4_or_combo" if ("ipilimumab" in s or "+" in s) else "PD1_PDL1_mono")
df["histo"] = df["cancer_type"].map(
    lambda s: "Lung" if "Lung" in s else ("Melanoma" if s == "Melanoma" else "Other"))

meta_cat = ["gender", "ethnicity", "race", "histo", "mech"]
ana_cols = ["ana_titer_baseline", "ana_titer_missing"]
cyto = [c for c in df.columns if c not in
        ["gender", "ethnicity", "race", "cancer_type", "ici_drug",
         "patient_id", "iraE_occurrence", "mech", "histo"] + ana_cols]
for c in cyto + ana_cols:                                 # 'OOR <' etc. → NaN → median-imputed
    df[c] = pd.to_numeric(df[c], errors="coerce")
used_cols = cyto + ana_cols + meta_cat                    # everything the pipeline reads

# ---- pipeline -----------------------------------------------------------------------------
def num_pipe():
    return Pipeline([("i", SimpleImputer(strategy="median")),
                     ("t", FunctionTransformer(np.log1p)),
                     ("s", StandardScaler())])

class PLSF(BaseEstimator, TransformerMixin):
    def __init__(self, n=3): self.n = n
    def fit(self, X, y=None):
        self.pls_ = PLSRegression(n_components=self.n).fit(np.asarray(X), np.asarray(y, float))
        return self
    def transform(self, X): return self.pls_.transform(np.asarray(X))

def make_pipe(C=0.1):
    pre = ColumnTransformer([
        ("cyto", Pipeline([("num", num_pipe()), ("pls", PLSF(3))]), cyto),
        ("ana",  num_pipe(), ana_cols),
        ("meta", Pipeline([("i", SimpleImputer(strategy="most_frequent")),
                           ("o", OneHotEncoder(handle_unknown="infrequent_if_exist",
                                               min_frequency=5, sparse_output=False))]), meta_cat)])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=5000, C=C))])

# ---- repeated CV ----------------------------------------------------------------------------
cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=4, random_state=SEED)
ref_cyto = cyto.index("Eotaxin-2/ CCL24")
W, coefs, perm, aucs, ref_w = [], [], [], [], None

for tr, te in cv.split(df, y):
    m = make_pipe().fit(df.iloc[tr], y[tr])
    pls = m.named_steps["pre"].named_transformers_["cyto"].named_steps["pls"].pls_
    w = pls.x_weights_.copy()                              # (n_cyto, 3)

    if ref_w is None:                                      # first fold defines the orientation
        ref_w = w.copy()
        if ref_w[ref_cyto, 0] < 0: ref_w[:, 0] *= -1      # PLS1: Eotaxin-2 positive
    s = np.sign((w * ref_w).sum(axis=0)); s[s == 0] = 1    # per-component sign vs reference
    W.append(w * s)
    coefs.append(m.named_steps["clf"].coef_.ravel()[:3] * s)   # SAME flip on the coefficients

    aucs.append(roc_auc_score(y[te], m.predict_proba(df.iloc[te])[:, 1]))
    r = permutation_importance(m, df.iloc[te][used_cols], y[te], scoring="roc_auc",
                               n_repeats=15, random_state=SEED, n_jobs=-1)
    perm.append(r.importances_mean)

W, Cf, P, aucs = np.array(W), np.array(coefs), np.array(perm), np.array(aucs)

# ---- report -------------------------------------------------------------------------------
pd.set_option("display.width", 200)
print(f"Test AUC over {len(aucs)} folds: {aucs.mean():.3f} ± {aucs.std():.3f}")
print("Logistic coef on PLS1/2/3 (sign-aligned): mean", np.round(Cf.mean(0), 3),
      " sd", np.round(Cf.std(0), 3))

load = pd.DataFrame({"cytokine": cyto,
                     "PLS1_mean": W[:, :, 0].mean(0), "PLS1_sd": W[:, :, 0].std(0),
                     "PLS2_mean": W[:, :, 1].mean(0), "PLS2_sd": W[:, :, 1].std(0)})
load["PLS1_stable"] = np.abs(np.sign(W[:, :, 0]).mean(0)) == 1   # same sign in every fold
load["PLS2_stable"] = np.abs(np.sign(W[:, :, 1]).mean(0)) == 1
top = load.reindex(load.PLS1_mean.abs().sort_values(ascending=False).index).reset_index(drop=True)

pi = pd.DataFrame({"feature": used_cols,
                   "auc_drop_mean": P.mean(0), "auc_drop_sd": P.std(0)}
                  ).sort_values("auc_drop_mean", ascending=False).reset_index(drop=True)

print(f"\nPLS1 sign-stable cytokines: {load.PLS1_stable.sum()}/{len(load)}"
      f"   PLS2: {load.PLS2_stable.sum()}/{len(load)}")
print("\nTop PLS1 weights (fold mean ± sd):\n", top.head(15).round(3).to_string())
print("\nPermutation importance, AUC drop (fold mean ± sd):\n", pi.head(15).round(4).to_string())

top.to_csv("irAE_04_pls_loadings.csv", index=False)
pi.to_csv("irAE_04_permutation_importance.csv", index=False)
