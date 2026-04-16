# ImmunoTherapy — Predicting Side Effect Severity with AI

## TLDR

Using AI to predict the **severity of immunotherapy side effects** (Mild / Medium / Severe) for cancer patients, based on patient bio data. Covers both **PD-1/PD-L1 checkpoint inhibitors** and **CAR-T cell therapy**.

### The Problem

Immunotherapy has revolutionized cancer treatment, but side effects (immune-related adverse events) affect **70-90% of checkpoint inhibitor patients** and **50-93% of CAR-T recipients**. Severity ranges from mild rash to life-threatening organ failure. Predicting severity before treatment could help doctors prepare and personalize care.

### The Approach

Build a **classification model** that takes a patient's profile as input and predicts side effect severity:

| Input (Patient Features) | Output (Prediction) |
|--------------------------|---------------------|
| Cancer type | **Mild** — Grade 1-2, outpatient management |
| Age, Gender, BMI | **Medium** — Grade 3, hospitalization needed |
| Previous autoimmune conditions * | **Severe** — Grade 4-5, life-threatening or fatal |
| Family history of autoimmunity * | |
| Inflammatory markers (NLR, CRP*, IL-6*) | |
| Prior / simultaneous treatments | |

\* **Feature availability note:** NLR (+ Albumin, Platelets, HGB) is available from the Chowell 2021 cohort (1,479 ICI patients, 100% coverage). **CRP, IL-6, autoimmune history, and family history** are clinically validated predictors that are **not obtainable at patient level** from any public dataset with paired irAE labels — they require institutional DUA access (UK Biobank, SCORPIO, prospective trials). This is acknowledged in the model's documented limitations.

### Key Findings from Research

| Feature | Impact on Severity |
|---------|-------------------|
| **Age >= 60** | 1.49x higher odds of severe side effects |
| **Pre-existing autoimmune disease** | 2.09x higher odds of severe side effects |
| **Combination therapy (PD-1 + CTLA-4)** | Side effect rates jump from ~70% to ~90% |
| **CAR-T product type** | Neurotoxicity varies: Yescarta 33% vs Breyanzi 16% |
| **Female sex** | Higher overall side effect incidence |

### Two Therapy Types

| | Checkpoint Inhibitors | CAR-T Therapy |
|---|---|---|
| **How it works** | Blocks PD-1/CTLA-4 to "release brakes" on immune system | Patient's T-cells engineered to target cancer |
| **Key drugs** | Keytruda, Opdivo, Yervoy, Tecentriq | Yescarta, Kymriah, Breyanzi, Abecma |
| **Main side effects** | Organ inflammation (skin, gut, liver, lungs, thyroid) | Cytokine Release Syndrome, Neurotoxicity |
| **Side effect rate** | 70-90% (any grade) | 50-93% (CRS) |

---

## Datasets

**413,161 real patient adverse event rows** from FDA FAERS (124,982 via openFDA API + **288,179 from the 2024-2025 Quarterly Data Extract dumps**) + **86 patient-level records** from NIH ImmPort (cancer stage, comorbidities, tumor markers) + **1,218 immunotherapy patients** from cBioPortal (LDH, ECOG, TMB, metastasis sites, survival) + **1,479 pan-cancer ICI patients** from Chowell 2021 Nat Biotech (NLR, Albumin, Platelets, HGB, BMI, TMB — 100% coverage) + reference tables.

```
datasets/
├── faers/                                              <- FDA post-marketing data via openFDA API (initial pull)
│   ├── checkpoint_inhibitor_adverse_events.csv         (62,106 rows — 25,000 reports, 5 drugs)
│   └── cart_therapy_adverse_events.csv                 (62,876 rows — 17,469 reports, 6 CAR-T products)
├── faers_quarterly/                                    <- FDA Quarterly Data Extract dumps, 2024-2025 (full)
│   ├── checkpoint_inhibitor_adverse_events_2024_2025.csv   (253,366 rows — 82,507 reports, 9 drugs)
│   └── cart_therapy_adverse_events_2024_2025.csv           (34,813 rows — 11,110 reports, 6 CAR-T products)
├── immport/                                            <- NIH clinical trial data (small, rich features)
│   ├── SDY1733/                                        (56 HCC patients, 10 on anti-PD-1 + BCLC stage, cirrhosis, HBV/HCV, AFP)
│   ├── SDY1597/                                        (30 breast cancer + controls, TNM stages)
│   └── SDY1658/                                        (16 GBM tumor samples)
├── cbioportal/                                         <- 7 immunotherapy studies (melanoma / bladder / RCC / NSCLC)
│   ├── all_patients_consolidated.csv                   (1,218 patients × 29 harmonized columns — LDH, ECOG, TMB, OS/PFS)
│   └── {7 study folders}                               (mel_dfci_2019, blca_iatlas_imvigor210_2017, etc.)
├── chowell_2021/                                       <- Chowell 2021 Nat Biotech pan-cancer ICI cohort
│   ├── chowell_all.csv                                 (1,479 patients × 29 cols — NLR, Albumin, Platelets, HGB, BMI, TMB, Response, OS/PFS)
│   ├── chowell_training.csv                            (1,184 multi-institution)
│   └── chowell_test_msk.csv                            (295 MSK held-out)
└── reference/
    ├── ctcae_severity_grades.csv        (CTCAE Grade 1-5 → Mild/Medium/Severe mapping)
    ├── immunotherapy_drugs.csv          (11 drugs — names, targets, approvals)
    ├── common_iraes_by_therapy.csv      (21 adverse events with incidence rates)
    └── predictive_features.csv          (19 validated predictive patient features)
```

### Severity Distribution (derived from FAERS seriousness flags)

Combined across both FAERS sources (openFDA API + 2024-2025 quarterly dumps):

| | Checkpoint Inhibitors | CAR-T | Combined |
|---|---|---|---|
| **Mild** | 125,325 (40%) | 38,373 (39%) | 163,698 (40%) |
| **Medium** | 100,981 (32%) | 23,854 (24%) | 124,835 (30%) |
| **Severe** | 89,166 (28%) | 35,462 (36%) | 124,628 (30%) |

See [`datasets/README.md`](datasets/README.md) for field descriptions, data quality stats, and how to expand the dataset.

### Additional Datasets

| Dataset | What It Has | Status |
|---------|-------------|--------|
| **ImmPort** | Patient-level trial data (demographics, labs, assessments) | **Downloaded** — 86 patients across 3 studies in `datasets/immport/` |
| **TCGA / cBioPortal** | Cancer genomics + pre-treatment clinical features + survival outcomes | **Downloaded** — 7 immunotherapy studies (1,218 patients) in `datasets/cbioportal/` |
| **Chowell 2021 (Nat Biotech)** | Pan-cancer ICI: NLR + Albumin + Platelets + HGB + BMI + TMB + outcomes | **Downloaded 2026-04-16** — 1,479 patients in `datasets/chowell_2021/` (100% lab coverage) |
| **GEO (GSE91061 et al.)** | Gene expression / RNA-seq from ICI-treated patients | **Explored — skipped.** Zero AE coverage; same Riaz cohort already in cBioPortal |
| **irAExplorer** | Aggregate ICI AE rates across 343 trials (71,087 patients) | **Explored — no download.** Per-trial aggregates only, no API |
| **ClinicalTrials.gov v2 API** | Per-trial MedDRA-coded AE tables (JSON) | Available — candidate for benchmark/validation data (aggregate, not patient-level) |
| **FDA FAERS Quarterly Dumps** | Millions of adverse event reports without API cap | **Downloaded** — 2024 Q1 through 2025 Q4 (8 quarters) in `datasets/faers_quarterly/` |
| **UK Biobank / SCORPIO / LORIS raw** | CRP, IL-6, autoimmune ICD codes | **Not accessible** — institutional DUA / formal application required |

See [`.claude/skills/expand-data/SKILL.md`](.claude/skills/expand-data/SKILL.md) for full source-by-source notes including what was evaluated and why.

---

## Research

Full analysis in [`docs/immunotherapy_side_effects_research.md`](docs/immunotherapy_side_effects_research.md) covering:

1. What is cancer immunotherapy (checkpoint inhibitors vs CAR-T)
2. Side effects — what happens and why (irAEs, CRS, ICANS)
3. Severity grading (CTCAE scale → Mild/Medium/Severe mapping)
4. What patient features predict severity (19 validated features, with public-data availability notes)
5. Available public datasets (FAERS, ImmPort, cBioPortal, Chowell 2021, GEO, ClinicalTrials.gov, VigiBase) and documented public-data feature gap (CRP / IL-6 / autoimmune history)
6. Existing ML models and prior art (AUC up to 0.99)
7. Proposed model design (Random Forest + XGBoost; Chowell cross-validation; honest limitations slide)
8. Medical terms glossary

---

## Project Context

- **Program:** InspiritAI
- **Tools:** Python, Google Colab, scikit-learn, pandas, matplotlib
- **Data:** Real patient data from public datasets (FDA FAERS primary)
- **Model:** Classification — Mild / Medium / Severe side effect severity
