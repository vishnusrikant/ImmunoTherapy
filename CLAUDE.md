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
| Cancer type | FAERS `indication`, ImmPort `condition`, cBioPortal, Chowell `Cancer_Type` |
| Age | FAERS `patient_age` (74-76% coverage), ImmPort demographic, Chowell (100% exact age) |
| Gender | FAERS, ImmPort, cBioPortal, Chowell (100%) |
| BMI | FAERS derived from weight (40-43% coverage); Chowell 2021 has BMI at 100% coverage |
| Pre-existing autoimmune conditions | ImmPort only (partial) — **not in FAERS / cBioPortal / Chowell** (see Feature Gap below) |
| Family history of autoimmunity | Not in any public dataset — would need survey (see Feature Gap below) |
| Inflammatory markers: NLR | **Chowell 2021 (100% coverage)** — use for cross-study validation of effects |
| Inflammatory markers: Albumin, Platelets, HGB | **Chowell 2021 (100% coverage)** |
| Inflammatory markers: IL-6 + 39 other cytokines/chemokines | **Khan JITC 2025 (146/162 patients, baseline + 6-8wk, paired with irAE labels)** |
| Inflammatory markers: CRP | **Not obtainable** at patient level from any public dataset with paired irAE labels (see Feature Gap below) |
| Prior / simultaneous treatments | FAERS partial; ImmPort `intervention` (SDY1733 has this); Chowell `Chemo_before_IO` |
| Cancer stage | ImmPort SDY1733 (BCLC A/C), SDY1597 (TNM), Chowell `Stage` + `Stage at IO start` |
| Cirrhosis / comorbidity | ImmPort SDY1733 |
| HBV/HCV infection | ImmPort SDY1733 |
| Tumor markers (AFP) | ImmPort SDY1733 |
| Tumor Mutation Burden (TMB) | cBioPortal (81%), Chowell (100%) |
| Microsatellite Instability (MSI) | Chowell (100%) |

## Datasets (in `datasets/`)

### Primary: FDA FAERS (413,161 rows total)

**Via openFDA API (initial pull, 2026-04-15):**
- `datasets/faers/checkpoint_inhibitor_adverse_events.csv` — 62,106 rows, 25,000 reports, 5 drugs
- `datasets/faers/cart_therapy_adverse_events.csv` — 62,876 rows, 17,469 reports, 6 products
- Capped at `skip=25000` (~5,000 reports per drug) by the API

**Via FDA Quarterly Data Extract dumps (2026-04-15, covers 2024 Q1 - 2025 Q4):**
- `datasets/faers_quarterly/checkpoint_inhibitor_adverse_events_2024_2025.csv` — 253,366 rows, 82,507 reports, 9 drugs (adds Cemiplimab, Dostarlimab, Tremelimumab, Relatlimab)
- `datasets/faers_quarterly/cart_therapy_adverse_events_2024_2025.csv` — 34,813 rows, 11,110 reports, 6 products
- No API cap; pulled + joined directly from pipe-delimited DEMO / DRUG / REAC / OUTC / INDI tables
- Schema superset of openFDA version: adds `primaryid`, `caseid`, `source_year_quarter`, pre-computed `severity` label
- Pull script: `scripts/faers_quarterly_pull.py`

Severity label derived from `seriousness_death` / `seriousness_life_threatening` / `seriousness_disabling` / `seriousness_hospitalization` flags. Combined split (both sources): 40% Mild / 30% Medium / 30% Severe.

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

### Supplementary: Chowell 2021 pan-cancer ICI cohort (1,479 patients with NLR + albumin + CBC)
- `datasets/chowell_2021/chowell_all.csv` — 1,479 rows × 29 cols, **100% coverage** on NLR, Albumin, Platelets, HGB, BMI, Age, Sex, TMB, MSI, Drug_class, Cancer_Type, Response, OS/PFS
- Cohorts: 1,184 multi-institution training + 295 MSK held-out test
- Source: Supplementary Data 1 of Chowell et al. *Nature Biotechnology* 2021 (DOI 10.1038/s41587-021-01070-8)
- **No irAE labels** — outcomes are tumor response and survival, NOT side-effect severity
- **No direct join to cBioPortal** — MSK uses different de-identification (integer SAMPLE_ID vs `P-0000###`)
- Use for (1) pre-treatment feature enrichment, (2) feature-effect validation against published biomarkers, (3) optional sidecar response model. **Do not train the severity classifier on this.**
- Downloaded via `scripts/chowell_download.py` (public Nature supplementary, no auth)

### Supplementary: Khan et al. JITC 2025 (162 ICI patients with cytokines AND irAE labels — added 2026-04-17)

- `datasets/khan_jitc_2025/khan_patients_consolidated.csv` — 162 patients × 54 columns (primary modeling file)
- 40-marker baseline cytokine panel (146/162 patients with BL data): IL-6, IFN-γ, TNF-α, IL-1β, IL-2, IL-4, IL-8, IL-10, IL-16, plus 32 chemokines (CCL/CXCL families, fractalkine, MIF, GM-CSF)
- **irAE labels: binary (Grade 0-1 vs Grade 2+), CTCAE grade 0/1/2/3, organ system (free text)** — paired with the same patient IDs as the cytokines
- ICI drug class covers all four: PD-1 (108), PD-L1 (26), CTLA-4 mono (1), combo (24)
- No CAR-T, no CRP, no CBC/CMP, no albumin
- Source: Khan et al. *J Immunother Cancer* 2025 [DOI 10.1136/jitc-2025-012414](https://doi.org/10.1136/jitc-2025-012414); data on Zenodo [10.5281/zenodo.17943391](https://zenodo.org/records/17943391); CC BY 4.0
- Pull script: `scripts/khan_jitc_2025_download.py` (uses curl — Zenodo blocks urllib's default UA)
- **Why it matters:** This is the only public dataset with patient-level cytokines paired with irAE outcomes. Closes the IL-6 + irAE-label half of the documented public-data gap. Use for: (1) baseline cytokine → irAE classifier (n=146), (2) cross-validation of FAERS-derived demographic feature effects, (3) limitations-section grounding showing exactly which gap features ARE accessible.

### Supplementary: UK Biobank Showcase catalog *(metadata only, added 2026-04-16)*
- `datasets/ukbiobank_catalog/` — **metadata only, no patient data** — publicly-downloadable UKB Showcase schemas
- `fields.tsv` (11,822 fields), `encodings.tsv` (859), `categories.tsv` (411), `encoding_values_hierstr.tsv` (46,928 incl. ICD-10), `encoding_values_hierint.tsv` (28,901)
- Derived: `gap_features_summary.csv` — CRP (Field 30710, 469K participants), IL-6 (Field 30900 Olink, 53K), Autoimmune ICD-10 (Field 41270, 448K)
- Derived: `autoimmune_icd10_codes.csv` — 304 codes across 24 irAE-relevant autoimmune blocks (M05/M06 RA, M32 SLE, E10 T1D, K50/K51 IBD, L40 psoriasis, G35 MS, etc.)
- Purpose: cite exact field IDs + coverage in the project's limitations section; NOT used as training data
- Access: patient-level UK Biobank data still requires institutional application + £500 student fee; catalog pull requires neither
- Script: `scripts/ukbiobank_catalog_download.py` (public, no auth)

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
│       ├── build-model/SKILL.md                 <- Build the classification model (next phase)
│       └── expand-data/SKILL.md                 <- Add more data (FAERS quarters, new sources)
├── datasets/
│   ├── README.md
│   ├── faers/                                   <- FDA adverse event reports via openFDA API
│   ├── faers_quarterly/                         <- FDA Quarterly Data Extract dumps (2024-2025)
│   ├── immport/                                 <- NIH clinical trial data (features FAERS lacks)
│   ├── cbioportal/                              <- 7 cBioPortal immunotherapy studies (1,218 patients)
│   ├── chowell_2021/                            <- Chowell 2021 Nat Biotech ICI cohort (1,479 patients, NLR/CBC)
│   ├── khan_jitc_2025/                          <- Khan JITC 2025 (162 patients with cytokines + irAE labels)
│   ├── ukbiobank_catalog/                       <- UKB Showcase metadata (no patient data) — gap-feature field refs
│   └── reference/                               <- CTCAE mapping, drug table, predictive features
├── scripts/
│   ├── faers_quarterly_pull.py                  <- Pull + parse FAERS quarterly dumps
│   ├── cbio_download.py                         <- cBioPortal REST API puller
│   ├── cbio_consolidate.py                      <- Build all_patients_consolidated.csv
│   ├── chowell_download.py                      <- Fetch + parse Chowell 2021 Supplementary Data 1
│   ├── khan_jitc_2025_download.py               <- Fetch + parse Khan JITC 2025 Zenodo deposit
│   └── ukbiobank_catalog_download.py            <- Pull UKB Showcase schemas + derive gap-feature + autoimmune CSVs
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
- **Date-stamp research** — current conventions assume 2026-04-15 baseline; Chowell 2021 + public-data-gap documentation added 2026-04-16
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

- Train and benchmark Random Forest + XGBoost on FAERS (next milestone — invoke `build-model` skill)
- Feature-engineer cirrhosis / stage from ImmPort SDY1733
- Feature-engineer TMB / LDH / ECOG / metastasis flags from cBioPortal consolidated table
- **Cross-validate learned feature effects on Chowell 2021 cohort** — fit a simple response model on NLR/Albumin/TMB/Age and check effect directions match our FAERS severity model
- **Optional response sidecar model** — train a tumor-response classifier on Chowell alongside the severity classifier (complementary clinical question)
- Google Colab notebook for InspiritAI presentation
- Optional: pull ClinicalTrials.gov v2 API for per-trial MedDRA AE rates as model-evaluation benchmarks
- **Access-gated features** — CRP / IL-6 / autoimmune-history would require institutional data access (UK Biobank, All of Us, prospective trial biobanks, SCORPIO). Acknowledged as out-of-scope for a student project; framed as honest future work rather than a capability of this model.

## Data Sources Explored and Rejected (2026-04-15 / 04-16)

- **GEO (Gene Expression Omnibus)** — zero AE coverage; flagship GSE91061 cohort is already in cBioPortal (`mel_iatlas_riaz_nivolumab_2017`). Heavy bioinformatics overhead for marginal feature gain.
- **irAExplorer** — aggregates ClinicalTrials.gov data but authors explicitly state no patient-level granularity; no API, no download. If we want what irAExplorer provides, pull ClinicalTrials.gov v2 API directly.
- **VigiBase / VigiAccess (WHO)** — VigiAccess public site is search-only (no CSV, no API). VigiBase Extract requires fee + DUA + WHO approval, and still excludes narratives/medical history/labs. Duplicates FAERS format without adding the clinical features we actually lack.
- **SCORPIO (Nat Med 2024)** — 9,745 patients with rich CBC + CMP + NLR, but institutional-only. No public download.
- **LORIS (Nat Cancer 2024) raw data** — 2,881 patients across 8 cohorts; reproducibility scripts on GitHub (`rootchang/LORIS`) + Zenodo, but MSK1/MSK2 raw data is institutional-only. The Chowell 2021 subset is publicly downloadable and is what we pulled.
- **UK Biobank (autoimmune history + CRP)** — has the right features (ICD-10 autoimmune codes, CRP, NLR) but requires formal institutional application. Out of scope for a student project timeline.

See `.claude/skills/expand-data/SKILL.md` for detailed evaluation notes.

## Public-Data Feature Gap (Partial Closure 2026-04-17)

Originally three clinically validated irAE-severity predictors were not obtainable at patient level with paired irAE labels. Khan et al. JITC 2025 closes the IL-6 (and broader cytokine) half of the gap:

| Feature | Evidence | Public patient-level source? |
|---------|----------|------------------------------|
| ~~**IL-6** (Interleukin-6)~~ | Predicts severe CRS/ICANS in CAR-T (Bone Marrow Transplant 2025) | **Khan JITC 2025 — 146 patients with paired BL + 6-8wk values + irAE labels (CC BY 4.0)** |
| **CRP** (C-reactive protein) | Nat Med 2024 ICI response predictor; elevated CRP associated with severe irAEs | None with irAE labels |
| **Autoimmune history** | OR 2.09 for Grade 3+ irAEs (Frontiers Immunology 2025, n=3,795) | UK Biobank has ICD codes but requires DUA. Khan JITC 2025 has ANA titer (65/162) as a partial proxy |

**The remaining limitation is documented honestly, not hidden.** The project's approach:
1. Train the FAERS severity model on what IS available there (demographics, drug, indication, outcome flags).
2. Use Chowell 2021 (NLR + albumin, no irAE labels) for cross-validation of demographic + drug-class feature effects.
3. **New:** train a parallel "any irAE" classifier on Khan JITC 2025 (n=146) using the cytokine panel including IL-6 — a complementary pre-treatment prediction task. Cross-validate demographic effects against FAERS.
4. State in the InspiritAI presentation that CRP and ICD-coded autoimmune history would still require institutional data access (UK Biobank, All of Us, prospective cohort studies) — a defined and tractable future-work statement, not a generic handwave.

Model performance should be interpreted accordingly: an irAE severity model trained only on FAERS is an honest prototype, not a clinical tool.
