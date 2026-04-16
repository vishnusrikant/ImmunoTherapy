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
| Previous autoimmune conditions | **Severe** — Grade 4-5, life-threatening or fatal |
| Family history of autoimmunity | |
| Inflammatory markers (NLR, CRP, IL-6) | |
| Prior / simultaneous treatments | |

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

**124,982 real patient adverse event rows** from FDA FAERS + **86 patient-level records** from NIH ImmPort (cancer stage, comorbidities, tumor markers) + **1,218 immunotherapy patients** from cBioPortal (LDH, ECOG, TMB, metastasis sites, survival) + reference tables.

```
datasets/
├── faers/                                              <- FDA post-marketing data (large, good for training)
│   ├── checkpoint_inhibitor_adverse_events.csv         (62,106 rows — 25,000 reports, 5 drugs)
│   └── cart_therapy_adverse_events.csv                 (62,876 rows — 17,469 reports, 6 CAR-T products)
├── immport/                                            <- NIH clinical trial data (small, rich features)
│   ├── SDY1733/                                        (56 HCC patients, 10 on anti-PD-1 + BCLC stage, cirrhosis, HBV/HCV, AFP)
│   ├── SDY1597/                                        (30 breast cancer + controls, TNM stages)
│   └── SDY1658/                                        (16 GBM tumor samples)
├── cbioportal/                                         <- 7 immunotherapy studies (melanoma / bladder / RCC / NSCLC)
│   ├── all_patients_consolidated.csv                   (1,218 patients × 29 harmonized columns — LDH, ECOG, TMB, OS/PFS)
│   └── {7 study folders}                               (mel_dfci_2019, blca_iatlas_imvigor210_2017, etc.)
└── reference/
    ├── ctcae_severity_grades.csv        (CTCAE Grade 1-5 → Mild/Medium/Severe mapping)
    ├── immunotherapy_drugs.csv          (11 drugs — names, targets, approvals)
    ├── common_iraes_by_therapy.csv      (21 adverse events with incidence rates)
    └── predictive_features.csv          (19 validated predictive patient features)
```

### Severity Distribution (derived from FAERS seriousness flags)

| | Checkpoint Inhibitors | CAR-T | Combined |
|---|---|---|---|
| **Mild** | 19,696 (32%) | 23,564 (37%) | 43,260 (35%) |
| **Medium** | 21,346 (34%) | 16,082 (26%) | 37,428 (30%) |
| **Severe** | 21,064 (34%) | 23,230 (37%) | 44,294 (35%) |

See [`datasets/README.md`](datasets/README.md) for field descriptions, data quality stats, and how to expand the dataset.

### Additional Datasets

| Dataset | What It Has | Status |
|---------|-------------|--------|
| **ImmPort** | Patient-level trial data (demographics, labs, assessments) | **Downloaded** — 86 patients across 3 studies in `datasets/immport/` |
| **TCGA / cBioPortal** | Cancer genomics + pre-treatment clinical features + survival outcomes | **Downloaded** — 7 immunotherapy studies (1,218 patients) in `datasets/cbioportal/` |
| **GEO (GSE91061 et al.)** | Gene expression / RNA-seq from ICI-treated patients | **Explored — skipped.** Zero AE coverage; same Riaz cohort already in cBioPortal |
| **irAExplorer** | Aggregate ICI AE rates across 343 trials (71,087 patients) | **Explored — no download.** Per-trial aggregates only, no API |
| **ClinicalTrials.gov v2 API** | Per-trial MedDRA-coded AE tables (JSON) | Available — candidate for benchmark/validation data (aggregate, not patient-level) |
| **FDA FAERS (full)** | Millions of adverse event reports (quarterly dumps) | Available — [fda.gov/faers](https://www.fda.gov/drugs/fdas-adverse-event-reporting-system-faers) for further scale-up |

See [`.claude/skills/expand-data/SKILL.md`](.claude/skills/expand-data/SKILL.md) for full source-by-source notes including what was evaluated and why.

---

## Research

Full analysis in [`docs/immunotherapy_side_effects_research.md`](docs/immunotherapy_side_effects_research.md) covering:

1. What is cancer immunotherapy (checkpoint inhibitors vs CAR-T)
2. Side effects — what happens and why (irAEs, CRS, ICANS)
3. Severity grading (CTCAE scale → Mild/Medium/Severe mapping)
4. What patient features predict severity (19 validated features)
5. Available public datasets (FAERS, ImmPort, TCGA, GEO, ClinicalTrials.gov)
6. Existing ML models and prior art (AUC up to 0.99)
7. Proposed model design (Random Forest + XGBoost)
8. Medical terms glossary

---

## Project Context

- **Program:** InspiritAI
- **Tools:** Python, Google Colab, scikit-learn, pandas, matplotlib
- **Data:** Real patient data from public datasets (FDA FAERS primary)
- **Model:** Classification — Mild / Medium / Severe side effect severity
