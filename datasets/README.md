# Datasets

## Organization

```
datasets/
├── README.md                  <- This file
├── faers/                     <- FDA Adverse Event Reporting System via openFDA API (initial pull, 2026-04-15)
│   ├── checkpoint_inhibitor_adverse_events.csv   (62,106 rows — 25,000 reports, 5 drugs)
│   └── cart_therapy_adverse_events.csv           (62,876 rows — 17,469 unique reports, 6 products)
├── faers_quarterly/           <- FDA FAERS Quarterly Data Extract dumps, 2024-2025 (no API cap)
│   ├── README.md
│   ├── checkpoint_inhibitor_adverse_events_2024_2025.csv   (253,366 rows — 82,507 reports, 9 drugs)
│   └── cart_therapy_adverse_events_2024_2025.csv           (34,813 rows — 11,110 reports, 6 products)
├── immport/                   <- NIH ImmPort clinical trial data (patient-level with cancer stage + comorbidities)
│   ├── README.md
│   ├── SDY1733/               (56 HCC patients, 10 on anti-PD-1 — BCLC stage, cirrhosis, HBV/HCV, AFP)
│   ├── SDY1597/               (30 breast cancer patients — TNM stage, chemo regimens)
│   └── SDY1658/               (16 GBM tumor samples)
├── cbioportal/                <- cBioPortal immunotherapy studies (1,218 patients with pre-treatment features + outcomes)
│   ├── README.md
│   ├── all_patients_consolidated.csv        (cross-study harmonized table)
│   └── {7 study folders}      (mel_dfci_2019, blca_iatlas_imvigor210_2017, rcc_iatlas_immotion150_2018,
│                               nsclc_pd1_msk_2018, mel_iatlas_liu_2019, mel_iatlas_riaz_nivolumab_2017, mel_ucla_2016)
└── reference/                 <- Reference/lookup tables
    ├── ctcae_severity_grades.csv        (CTCAE Grade 1-5 → Mild/Medium/Severe mapping)
    ├── immunotherapy_drugs.csv          (11 drugs — names, targets, approvals)
    ├── common_iraes_by_therapy.csv      (21 adverse events — incidence rates by therapy type)
    └── predictive_features.csv          (19 patient features — evidence strength, effect on severity)
```

## FAERS Data (Real Patient Reports)

**413,161 total adverse event rows** pulled from the [FDA Adverse Event Reporting System](https://open.fda.gov/data/faers/) in two passes:
1. **openFDA API** — 124,982 rows across 42,469 reports, 11 drugs (2026-04-15, `datasets/faers/`)
2. **Quarterly Data Extract dumps** — 288,179 rows across 93,617 reports covering 2024 Q1 through 2025 Q4, 15 drugs including newer agents Cemiplimab, Dostarlimab, Tremelimumab, Relatlimab (2026-04-15, `datasets/faers_quarterly/` — see [its README](faers_quarterly/README.md) for full details)

The openFDA API caps at `skip=25000` (~5,000 reports/drug). The quarterly dumps have no cap. Both sources feed from the same FDA database, so rows can be deduped by `primaryid` if combined.

### openFDA API pull (below) covers all-time cumulative data up to the pull date

### Checkpoint Inhibitors (`checkpoint_inhibitor_adverse_events.csv`)

- **25,000 adverse event reports** across 5 drugs (5,000 per drug)
- **62,106 individual adverse event rows** (one row per reaction per report)
- 74% have patient age; 40% have weight; 88% have cancer indication
- **Derived severity split: Mild 19,696 / Medium 21,346 / Severe 21,064** (well-balanced)

| Drug | Rows | Target |
|------|------|--------|
| Pembrolizumab (Keytruda) | 14,028 | PD-1 |
| Durvalumab (Imfinzi) | 12,244 | PD-L1 |
| Nivolumab (Opdivo) | 12,104 | PD-1 |
| Ipilimumab (Yervoy) | 12,098 | CTLA-4 |
| Atezolizumab (Tecentriq) | 11,632 | PD-L1 |

### CAR-T Therapies (`cart_therapy_adverse_events.csv`)

- **17,469 unique reports** (deduplicated across generic/brand name queries) across 6 products
- **62,876 individual adverse event rows**
- 76% have patient age; 43% have weight; 95% have cancer indication
- **Derived severity split: Mild 23,564 / Medium 16,082 / Severe 23,230**

| Product | Rows | Target |
|---------|------|--------|
| Tisagenlecleucel (Kymriah) | 23,311 | CD19 |
| Axicabtagene ciloleucel (Yescarta) | 19,099 | CD19 |
| Ciltacabtagene autoleucel (Carvykti) | 8,980 | BCMA |
| Brexucabtagene autoleucel (Tecartus) | 5,630 | CD19 |
| Idecabtagene vicleucel (Abecma) | 3,689 | BCMA |
| Lisocabtagene maraleucel (Breyanzi) | 2,167 | CD19 |

### FAERS Fields

| Column | Description |
|--------|-------------|
| `drug_name` | Generic name of the immunotherapy drug |
| `drug_class` | Checkpoint Inhibitor or CAR-T |
| `patient_age` | Patient age at onset |
| `patient_age_unit` | Age unit (801=Year, 802=Month, 803=Day) |
| `patient_sex` | Male / Female / Unknown |
| `patient_weight_kg` | Patient weight in kg |
| `indication` | Cancer type / condition the drug was prescribed for |
| `reaction` | Adverse event (MedDRA preferred term) |
| `reaction_outcome` | Recovered / Recovering / Not Recovered / Fatal / Unknown |
| `serious` | Serious / Non-Serious |
| `seriousness_death` | 1 if resulted in death |
| `seriousness_hospitalization` | 1 if resulted in hospitalization |
| `seriousness_life_threatening` | 1 if life-threatening |
| `seriousness_disabling` | 1 if resulted in disability |
| `report_date` | Date report was received by FDA |
| `country` | Country where event occurred |

### Deriving Severity Labels from FAERS

FAERS does not include CTCAE grades directly. Severity can be derived from the seriousness flags:

| Derived Label | FAERS Criteria |
|---------------|----------------|
| **Mild** | Non-Serious OR (Serious + Recovered + no hospitalization/death/life-threatening) |
| **Medium** | Serious + Hospitalization (but not life-threatening or fatal) |
| **Severe** | Life-threatening OR Fatal OR Disabling |

### Severity Distribution

| | Checkpoint Inhibitors | CAR-T | Combined |
|---|---|---|---|
| **Mild** | 19,696 (32%) | 23,564 (37%) | 43,260 (35%) |
| **Medium** | 21,346 (34%) | 16,082 (26%) | 37,428 (30%) |
| **Severe** | 21,064 (34%) | 23,230 (37%) | 44,294 (35%) |

## ImmPort Data (NIH Clinical Trials, Patient-Level)

Downloaded via authenticated ImmPort API on April 15, 2026. Primary purpose: supplement FAERS with **patient-level cancer stage, comorbidities, and tumor markers** that FAERS lacks.

### SDY1733 — anti-PD-1 HCC Study (Primary)

- **56 patients** (15 controls + 41 hepatocellular carcinoma), of whom **10 received anti-PD-1 immunotherapy** (5 Nivolumab + 5 Camrelizumab)
- Chinese cohort, age 27-79 (mean 55.2), 68% male
- **Features available:** BCLC cancer stage (A/C), cirrhosis (21 Yes / 35 No), HBV/HCV status (33 HBV / 23 uninfected), AFP tumor marker, intervention history

### SDY1597 — Breast Cancer Post-Chemo (Comparator)

- **30 patients** (15 breast cancer + 15 healthy controls)
- US cohort; TNM stages IA, IB, IIA, IIB, IIIA
- Treatment: various chemotherapy regimens (not immunotherapy)

### SDY1658 — GBM Tumor Samples (Tertiary)

- **16 glioblastoma patients**, tumor tissue samples only
- No clinical assessment or lab data

### Limitations

- **No adverse event data** — ImmPort's `adverseEvent` endpoint returned empty for all three studies
- **No CTCAE severity grading** in the data
- **Small sample** — 86 patients total vs 124,982 rows in FAERS
- See [`immport/README.md`](immport/README.md) for full details

## cBioPortal Data (Cancer Genomics + Clinical Trials)

Downloaded via the public [cBioPortal REST API](https://www.cbioportal.org/api) on April 15, 2026. Primary purpose: supplement FAERS with **pre-treatment clinical features** (LDH, ECOG, TMB, metastasis sites, steroid use, prior therapies) plus **survival and response outcomes** for 1,218 immunotherapy patients across 7 studies.

### Studies (1,218 patients total)

| Study | Cancer | Drug | Patients |
|-------|--------|------|---------:|
| `blca_iatlas_imvigor210_2017` | Bladder | Atezolizumab | 347 |
| `rcc_iatlas_immotion150_2018` | Renal Cell Carcinoma | Atezolizumab ± Bevacizumab | 263 |
| `nsclc_pd1_msk_2018` | NSCLC | Pembro / Nivo | 240 |
| `mel_dfci_2019` | Melanoma | anti-PD-1 / anti-CTLA-4 / combo | 144 |
| `mel_iatlas_liu_2019` | Melanoma | PD-1 | 122 |
| `mel_iatlas_riaz_nivolumab_2017` | Melanoma | Nivolumab | 64 |
| `mel_ucla_2016` | Melanoma | Pembrolizumab | 38 |

### Primary File

`cbioportal/all_patients_consolidated.csv` — 1,218 rows × 29 harmonized columns including drug (100%), cancer type (100%), TMB (81%), response (71%), PFS (63%), OS (58%), and melanoma-specific LDH / ECOG / metastasis detail (12%).

### Limitations

- **No adverse-event columns** — cBioPortal records response, not irAEs. Use to enrich features; keep FAERS for severity labels.
- **LDH / ECOG / metastasis-site detail is concentrated in `mel_dfci_2019`** — treat as optional features with missingness indicators for cross-study models.
- **Response vocabulary mixes binary (`TRUE`/`FALSE`) and RECIST categories** — normalize before modeling.
- See [`cbioportal/README.md`](cbioportal/README.md) for full details.

## Reference Data

### `ctcae_severity_grades.csv`
Maps CTCAE Grades 1-5 to the 3-class model labels (Mild / Medium / Severe) with clinical action descriptions.

### `immunotherapy_drugs.csv`
Reference table of 11 immunotherapy drugs covering both checkpoint inhibitors (PD-1, PD-L1, CTLA-4) and CAR-T products (CD19, BCMA targets).

### `common_iraes_by_therapy.csv`
21 common immune-related adverse events with incidence rates (any grade and grade 3+) by therapy type, sourced from published clinical literature.

### `predictive_features.csv`
19 patient features validated in published studies as predictive of immunotherapy side effect severity, with evidence strength ratings and source citations.

## Additional Datasets (Require Registration)

These datasets contain richer patient-level data but require free account registration:

| Dataset | URL | What It Has | Status |
|---------|-----|-------------|--------|
| **ImmPort** | [immport.org/shared](https://www.immport.org/shared/) | Patient-level clinical trial data: demographics, labs, assessments | **Downloaded** — 86 patients, 3 studies (see `immport/`) |
| **TCGA via cBioPortal** | [cbioportal.org/api](https://www.cbioportal.org/api) | Cancer genomics + clinical data (10,000+ patients across 33 cancer types) | **Downloaded** — 7 ICI studies, 1,218 patients (see `cbioportal/`) |
| **GEO (GSE91061)** | [ncbi.nlm.nih.gov/geo](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE91061) | Gene expression / RNA-seq for ICI-treated patients | **Explored 2026-04-15 — skipped.** No AE coverage; GSE91061 is the same cohort as cBioPortal `mel_iatlas_riaz_nivolumab_2017` |
| **irAExplorer** | [irae.tanlab.org](https://irae.tanlab.org/) | Aggregated ICI AE rates from 343 trials (71,087 patients) | **Explored 2026-04-15 — no download.** Authors aggregate per-trial only; no patient-level data, no API |
| **ClinicalTrials.gov v2 API** | [clinicaltrials.gov/api/v2/studies](https://clinicaltrials.gov/api/v2/studies) | Per-trial MedDRA-coded AE tables (JSON, no auth) | **Verified 2026-04-15** — candidate for benchmark/evaluation data (aggregate, not patient-level) |
| **VigiBase (WHO)** | [vigiaccess.org](https://www.vigiaccess.org/) | 28M+ global adverse event reports (~150K ICI reports 2008-2023) | Free aggregate access only; raw data requires DUA |

See [`.claude/skills/expand-data/SKILL.md`](../.claude/skills/expand-data/SKILL.md) for exploration notes, decision rationale, and candidate studies for each source.

## How to Expand the FAERS Data Further

**Already done (2026-04-15):** Quarterly dumps for 2024 Q1 - 2025 Q4 — see [`datasets/faers_quarterly/`](faers_quarterly/).

**To add older years (2020-2023 or further back):**
1. Edit the `QUARTERS` list in `scripts/faers_quarterly_pull.py` to include the desired year/quarter pairs
2. Re-run `python3 scripts/faers_quarterly_pull.py`
3. The script skips already-downloaded quarterly zips in `/tmp/faers_quarterly/`

Quarterly dumps are available back to **2004 Q1** at [fis.fda.gov/extensions/FPD-QDE-FAERS](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html) as 7 pipe-delimited ASCII tables (DEMO, DRUG, REAC, OUTC, INDI, THER, RPSR) joined on `primaryid`.
