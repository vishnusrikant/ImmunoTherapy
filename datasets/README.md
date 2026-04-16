# Datasets

## Organization

```
datasets/
├── README.md                  <- This file
├── faers/                     <- FDA Adverse Event Reporting System (real patient data, post-marketing)
│   ├── checkpoint_inhibitor_adverse_events.csv   (62,106 rows — 25,000 reports, 5 drugs)
│   └── cart_therapy_adverse_events.csv           (62,876 rows — 17,469 unique reports, 6 products)
├── immport/                   <- NIH ImmPort clinical trial data (patient-level with cancer stage + comorbidities)
│   ├── README.md
│   ├── SDY1733/               (56 HCC patients, 10 on anti-PD-1 — BCLC stage, cirrhosis, HBV/HCV, AFP)
│   ├── SDY1597/               (30 breast cancer patients — TNM stage, chemo regimens)
│   └── SDY1658/               (16 GBM tumor samples)
└── reference/                 <- Reference/lookup tables
    ├── ctcae_severity_grades.csv        (CTCAE Grade 1-5 → Mild/Medium/Severe mapping)
    ├── immunotherapy_drugs.csv          (11 drugs — names, targets, approvals)
    ├── common_iraes_by_therapy.csv      (21 adverse events — incidence rates by therapy type)
    └── predictive_features.csv          (19 patient features — evidence strength, effect on severity)
```

## FAERS Data (Real Patient Reports)

**124,982 total adverse event rows** pulled from the [FDA Adverse Event Reporting System](https://open.fda.gov/data/faers/) via the openFDA API on April 15, 2026.

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
| **ImmPort** | [immport.org/shared](https://www.immport.org/shared/) | Patient-level clinical trial data: demographics, labs, assessments | **Downloaded** (see `immport/` above) |
| **TCGA via cBioPortal** | [cbioportal.org](https://www.cbioportal.org/) | Cancer genomics + clinical data (age, gender, stage, mutations, treatment) for 10,000+ patients | Free download |
| **GEO (GSE91061)** | [ncbi.nlm.nih.gov/geo](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE91061) | Gene expression for melanoma patients on anti-PD-1 (responders vs non-responders) | Free download |
| **ClinicalTrials.gov** | [clinicaltrials.gov](https://clinicaltrials.gov/) | Trial results with adverse event rates by therapy | Free search |
| **VigiBase (WHO)** | [vigiaccess.org](https://www.vigiaccess.org/) | 28M+ global adverse event reports | Free (limited public access) |

## How to Expand the FAERS Data Further

The current dataset uses 5,000 reports per drug (the openFDA API max skip is 25,000). For even more data, download the full FAERS quarterly data dumps (millions of records):

[fda.gov/drugs/fdas-adverse-event-reporting-system-faers](https://www.fda.gov/drugs/fdas-adverse-event-reporting-system-faers)

The quarterly dumps are available as CSV files organized by tables (DEMO, DRUG, REAC, OUTC, THER) that can be joined on `primaryid`.
