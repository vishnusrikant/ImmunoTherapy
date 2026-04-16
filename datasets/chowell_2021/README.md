# Chowell 2021 Pan-Cancer ICI Cohort

Public patient-level data from:

> Chowell et al. **"Improved prediction of immune checkpoint blockade efficacy across multiple cancer types."** *Nature Biotechnology*, 2021. DOI: [10.1038/s41587-021-01070-8](https://www.nature.com/articles/s41587-021-01070-8)

Downloaded from the paper's Supplementary Data (MOESM3) on 2026-04-16 via `scripts/chowell_download.py`.

## Files

| File | Rows | Cols | Description |
|------|------|------|-------------|
| `chowell_all.csv` | 1,479 | 29 | Training + Test concatenated, with `cohort` flag |
| `chowell_training.csv` | 1,184 | 29 | Multi-institution training cohort |
| `chowell_test_msk.csv` | 295 | 29 | MSK held-out test set |
| `supplementary_source.xlsx` | — | — | Original Nature Biotechnology supplementary xlsx |

## What's in it

**100% coverage on every clinical/lab feature** — no missingness.

| Feature | Type | Notes |
|---------|------|-------|
| `SAMPLE_ID` | int | MSK-scheme integer ID. **Does not join** to cBioPortal `P-0000###` patient IDs |
| `NLR` | numeric | Neutrophil-to-Lymphocyte Ratio (pretreatment) |
| `Albumin` | numeric | Serum albumin (g/dL) |
| `Platelets` | numeric | Platelet count |
| `HGB` | numeric | Hemoglobin |
| `BMI` | numeric | Body mass index |
| `Age` | numeric | Exact (years) — unlike Valero 2021 which bucketed |
| `Sex` | 1/0 | 1 = Male, 0 = Female |
| `Stage` | 1/0 | 1 = IV, 0 = I–III (also free-text `Stage at IO start`) |
| `Cancer_Type` | text | Mostly `NSCLC` (538), `Melanoma` (186), `Others` (755) |
| `Drug_class` | text | `PD1/PDL1` (1,221) / `Combo` (253) / `CTLA4` (5) |
| `Chemo_before_IO` | 1/0 | Prior chemotherapy |
| `TMB` | numeric | Tumor Mutation Burden (mutations/Mb) |
| `FCNA`, `HED`, `HLA_LOH`, `MSI`, `MSI_SCORE` | various | Genomic features |
| `Response` | 1/0 | 1 = Responder (CR/PR/SD≥6mo), 0 = Non-responder |
| `OS_Months`, `OS_Event` | numeric | Overall survival |
| `PFS_Months`, `PFS_Event` | numeric | Progression-free survival |
| `RF16_prob` | numeric | Random Forest 16-feature prediction from the paper (for comparison) |
| `cohort` | text | `training` or `test_msk` — added by our pipeline |

## Critical caveats for the ImmunoTherapy project

**This dataset does NOT contain irAE severity labels.** Outcomes are tumor response and survival, not Mild/Medium/Severe side effects. **Do not use for training the severity classifier.**

Appropriate uses:
1. **Feature-effect validation** — confirm our model's learned NLR / albumin / age effects align with published biomarker literature.
2. **Response-model sidecar** — optional second model predicting treatment response, presented alongside severity predictions.
3. **Cross-study sanity check** — compare feature distributions (age, cancer type, drug class) against our FAERS + cBioPortal cohorts to quantify population differences.

**No join to cBioPortal.** MSK uses different de-identification schemes — Chowell IDs are integers (e.g., `8384`), cBioPortal `nsclc_pd1_msk_2018` uses `P-0000###`. Do not attempt exact patient-level matching.

## Why this cohort over alternatives

See `docs/immunotherapy_side_effects_research.md` and `.claude/skills/expand-data/SKILL.md` for the feature-gap analysis. Summary:

- **Chowell 2021** is the richest *publicly downloadable* ICI cohort with NLR + albumin (1,479 patients, 0 missingness).
- Valero 2021 Nat Comm (1,714 MSK patients, includes ECOG) has NLR but no albumin — available as Supp Data of [10.1038/s41467-021-20935-9](https://www.nature.com/articles/s41467-021-20935-9).
- SCORPIO Nat Med 2024 (9,745 patients, 33 features incl. CMP/CBC) — not public.
- LORIS Nat Cancer 2024 (2,881 patients) — reproducibility code on GitHub, but raw MSK data still institutional.

## What we still can't get from public data

- **CRP** — no public ICI cohort ships CRP with patient-level labels
- **IL-6** — same story; always requires prospective collection under DUA
- **Autoimmune history** — exists in UK Biobank ICD codes but requires formal application
- **CTCAE grades for irAEs** — this is the core gap. FAERS has it but no labs; Chowell/Valero/SCORPIO have labs but no irAE grading.

This gap is acknowledged in the project's limitations section rather than papered over.
