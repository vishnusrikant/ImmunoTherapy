# Colab notebooks

Latest versions of the irAE prediction notebooks from Google Colab.

Upload each notebook here with **Add file → Upload files** on GitHub, or in Colab use
**File → Save a copy in GitHub** and pick this repo and the `colab/` folder.

| Notebook | What it does |
|---|---|
| `irAE_01_model_panel.ipynb` | Benchmarks 21 classifier families under one fixed preprocessing pipeline (5-fold × 10-repeat stratified CV) |
| `irAE_02_logistic_variations.ipynb` | Logistic-regression variations: raw, composite cytokine scores, PLS |
| `irAE_03_nested_cv_finalists.ipynb` | Nested CV of the finalists, bootstrap 95% CI for the winning model's AUC |

Data: `ActionableData/Khan_workable.csv` (146 patients, 40 baseline cytokines + ANA titer;
public data from Khan et al., *J Immunother Cancer* 2025, CC BY 4.0).

This repository is public. Before uploading, make sure a notebook contains no API keys,
tokens or private file paths.
