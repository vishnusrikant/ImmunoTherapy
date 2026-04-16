# ImmunoTherapy — Project Context

## Project Overview

AI research project for the **InspiritAI program**. Goal: build a **classification model** that predicts the **severity** of side effects (Mild / Medium / Severe) a cancer patient will experience on immunotherapy, based on their bio-data and treatment.

Covers **both types of cancer immunotherapy**:
1. **Checkpoint inhibitors** (PD-1, PD-L1, CTLA-4) — Keytruda, Opdivo, Yervoy, Tecentriq, Imfinzi
2. **CAR-T cell therapy** — Yescarta, Kymriah, Tecartus, Breyanzi, Abecma, Carvykti

## Target Audience
- **Primary:** InspiritAI program mentors and peers (high-school / early-college AI research)
- **Bar:** Publishable / presentable — real public datasets, cited research, interpretable model

## Problem Statement

Immunotherapy side effects (irAEs) affect 70-90% of checkpoint-inhibitor patients and 50-93% of CAR-T patients. Severity ranges from mild rash to fatal organ failure. **Predicting severity before treatment** could help doctors personalize care.

## Classification Target (3 classes)

| Label | CTCAE Grade | Clinical Description |
|-------|-------------|---------------------|
| **Mild** | Grade 1-2 | Outpatient; observe or hold treatment |
| **Medium** | Grade 3 | Hospitalization; discontinue treatment |
| **Severe** | Grade 4-5 | Life-threatening or fatal |

## Patient Features (Inputs)

| Feature | Source |
|---------|--------|
| Cancer type | FAERS `indication`, ImmPort `condition` |
| Age | FAERS `patient_age` (74-76% coverage), ImmPort demographic |
| Gender | Both |
| BMI | Derived from weight (FAERS 40-43% coverage) |
| Pre-existing autoimmune conditions | ImmPort only (partial) |
| Family history of autoimmunity | Not in public datasets — would need survey |
| Inflammatory markers (NLR, CRP, IL-6) | Not in FAERS; not in downloaded ImmPort studies |
| Prior / simultaneous treatments | FAERS partial; ImmPort `intervention` (SDY1733 has this) |
| Cancer stage | ImmPort SDY1733 (BCLC A/C), SDY1597 (TNM) |
| Cirrhosis / comorbidity | ImmPort SDY1733 |
| HBV/HCV infection | ImmPort SDY1733 |
| Tumor markers (AFP) | ImmPort SDY1733 |

## Datasets (in `datasets/`)

### Primary: FDA FAERS (124,982 rows)
- `datasets/faers/checkpoint_inhibitor_adverse_events.csv` — 62,106 rows, 25,000 reports, 5 drugs
- `datasets/faers/cart_therapy_adverse_events.csv` — 62,876 rows, 17,469 reports, 6 products
- Pulled via openFDA API on 2026-04-15
- Severity label derived from `seriousness_death` / `seriousness_life_threatening` / `seriousness_disabling` / `seriousness_hospitalization` flags
- Split: ~35% Mild / 30% Medium / 35% Severe (well-balanced)

### Supplementary: NIH ImmPort (86 patients)
- `datasets/immport/SDY1733/` — **56 HCC patients, 10 on anti-PD-1** (Nivolumab, Camrelizumab). Has BCLC stage, cirrhosis, HBV/HCV, AFP. **Consolidated file**: `SDY1733_patients_consolidated.csv`
- `datasets/immport/SDY1597/` — 30 breast cancer + controls, post-chemo. TNM stages recorded
- `datasets/immport/SDY1658/` — 16 GBM tumor samples (no clinical assessments)
- Downloaded via authenticated ImmPort API (requires registered account)

### Supplementary: cBioPortal (1,218 patients across 7 immunotherapy studies)
- `datasets/cbioportal/all_patients_consolidated.csv` — cross-study harmonized table, 29 columns
- Studies: `mel_dfci_2019` (144), `blca_iatlas_imvigor210_2017` (347), `rcc_iatlas_immotion150_2018` (263), `nsclc_pd1_msk_2018` (240), `mel_iatlas_liu_2019` (122), `mel_iatlas_riaz_nivolumab_2017` (64), `mel_ucla_2016` (38)
- Pre-treatment features: LDH (melanoma DFCI only), ECOG, TMB (81% coverage), metastasis sites, steroid use, prior therapy lines
- Outcomes: OS / PFS months, response labels (mix of binary TRUE/FALSE and RECIST categories — normalize before modeling)
- **No adverse-event columns** — use for pre-treatment feature enrichment, keep FAERS for severity labels
- Downloaded via public cBioPortal REST API (no auth). Scripts in `scripts/cbio_download.py` + `scripts/cbio_consolidate.py`

### Reference Tables (in `datasets/reference/`)
- `ctcae_severity_grades.csv` — CTCAE 1-5 → Mild/Medium/Severe mapping
- `immunotherapy_drugs.csv` — 11 drugs (generic, brand, target, approval year)
- `common_iraes_by_therapy.csv` — 21 adverse events with incidence rates by therapy type
- `predictive_features.csv` — 19 validated patient features with evidence strength

## Repo Structure

```
ImmunoTherapy/
├── CLAUDE.md                                    <- This file (project context)
├── README.md                                    <- TLDR with problem, approach, dataset summary
├── .claude/
│   └── skills/
│       ├── resume-research/SKILL.md             <- Load context when resuming the project
│       └── build-model/SKILL.md                 <- Build the classification model (next phase)
├── datasets/
│   ├── README.md
│   ├── faers/                                   <- FDA adverse event reports (primary training data)
│   ├── immport/                                 <- NIH clinical trial data (features FAERS lacks)
│   └── reference/                               <- CTCAE mapping, drug table, predictive features
└── docs/
    └── immunotherapy_side_effects_research.md   <- 8-section research document
```

## Key Research Findings (see `docs/immunotherapy_side_effects_research.md`)

| Feature | Effect on Severity | Evidence |
|---------|-------------------|----------|
| Age ≥ 60 | **OR 1.49** for Grade 3+ irAEs | Frontiers in Immunology 2025 (n=3,795) |
| Pre-existing autoimmune disease | **OR 2.09** for Grade 3+ irAEs | Frontiers in Immunology 2025 |
| Combination therapy (PD-1 + CTLA-4) | 70% → 90% irAE rate | ASCO Clinical Practice Guideline |
| CAR-T product type | ICANS: Yescarta 33% > Kymriah 22% > Breyanzi 16% | ASH Blood 2024 |
| IL-6 day 3 post CAR-T | Predicts severe CRS/ICANS | Bone Marrow Transplantation 2025 |

Prior art achieved **AUC 0.99** with XGBoost on ePRO data (BMC Med Inform 2021) and **AUC 0.83** with logistic regression for ICANS prediction (Bone Marrow Transplant 2025).

## Proposed Modeling Approach

1. **Start with FAERS** (largest, cleanest severity labels)
2. **Engineer severity labels** from seriousness flags
3. **Baseline:** Logistic Regression (interpretable)
4. **Primary:** Random Forest (handles mixed features, feature importance)
5. **Comparison:** XGBoost (best published results)
6. **Optional enrichment:** Add ImmPort features (cirrhosis flag, cancer stage) for SDY1733 validation

Tools: Python, Google Colab, scikit-learn, pandas, matplotlib, XGBoost

## Standards / Conventions

- **Real patient data only** — no synthetic data generation
- **Cite every claim** with peer-reviewed source or regulatory document
- **Interpretable over opaque** — for InspiritAI, favor models whose decisions can be explained
- **Date-stamp research** — current conventions assume 2026-04-15 baseline
- **Preserve user's README structure** — the user wrote the original feature list; enhancements go around it, not over it

## Key Terminology

| Term | Definition |
|------|-----------|
| **irAE** | Immune-Related Adverse Event |
| **CRS** | Cytokine Release Syndrome (CAR-T) |
| **ICANS** | Immune effector Cell-Associated Neurotoxicity Syndrome (CAR-T) |
| **CTCAE** | Common Terminology Criteria for Adverse Events (5-grade scale) |
| **PD-1 / PD-L1** | Programmed Death receptor / ligand (checkpoint proteins) |
| **CTLA-4** | Cytotoxic T-Lymphocyte Associated protein 4 |
| **CAR-T** | Chimeric Antigen Receptor T-cell therapy |
| **FAERS** | FDA Adverse Event Reporting System |
| **ImmPort** | NIH/NIAID immunology data repository |
| **MedDRA** | Medical Dictionary for Regulatory Activities (standardized AE terminology) |
| **BCLC** | Barcelona Clinic Liver Cancer staging (A/B/C/D) |
| **NLR** | Neutrophil-to-Lymphocyte Ratio |
| **TMB** | Tumor Mutation Burden |

## Future Work

- Train and benchmark Random Forest + XGBoost on FAERS
- Feature-engineer cirrhosis / stage from ImmPort SDY1733
- Google Colab notebook for InspiritAI presentation
- Add ClinicalTrials.gov aggregate adverse event rates as reference benchmarks
- Explore GEO (GSE91061) gene expression for melanoma PD-1 responders
