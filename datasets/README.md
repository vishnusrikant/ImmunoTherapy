# Datasets

## Organization

```
datasets/
├── README.md                  <- This file
├── faers/                     <- FDA Adverse Event Reporting System (real patient data)
│   ├── checkpoint_inhibitor_adverse_events.csv   (1,204 rows — 500 reports, 5 drugs)
│   └── cart_therapy_adverse_events.csv           (2,094 rows — 500 reports, 5 drugs)
└── reference/                 <- Reference/lookup tables
    ├── ctcae_severity_grades.csv        (CTCAE Grade 1-5 → Mild/Medium/Severe mapping)
    ├── immunotherapy_drugs.csv          (11 drugs — names, targets, approvals)
    ├── common_iraes_by_therapy.csv      (21 adverse events — incidence rates by therapy type)
    └── predictive_features.csv          (19 patient features — evidence strength, effect on severity)
```

## FAERS Data (Real Patient Reports)

Pulled from the [FDA Adverse Event Reporting System](https://open.fda.gov/data/faers/) via the openFDA API on April 15, 2026.

### Checkpoint Inhibitors (`checkpoint_inhibitor_adverse_events.csv`)

- **500 adverse event reports** across 5 drugs (100 per drug)
- **1,204 individual adverse event rows** (one row per reaction per report)
- Drugs: Pembrolizumab, Nivolumab, Atezolizumab, Durvalumab, Ipilimumab
- 91% of records have patient age; 60% have weight
- Top reactions: Pyrexia, Diarrhoea, Colitis, Fatigue, Pneumonitis

### CAR-T Therapies (`cart_therapy_adverse_events.csv`)

- **500 adverse event reports** across 5 products (100 per product)
- **2,094 individual adverse event rows**
- Products: Yescarta, Kymriah, Tecartus, Breyanzi, Abecma
- 82% of records have patient age; 55% have weight
- Top reactions: Cytokine Release Syndrome, Pyrexia, Neurotoxicity, Encephalopathy, Hypotension

### FAERS Fields

| Column | Description |
|--------|-------------|
| `drug_name` | Generic name of the immunotherapy drug |
| `drug_class` | Checkpoint Inhibitor or CAR-T |
| `patient_age` | Patient age at onset |
| `patient_age_unit` | Age unit (801=Year, 802=Month, 803=Day) |
| `patient_sex` | Male / Female / Unknown |
| `patient_weight_kg` | Patient weight in kg |
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

| Dataset | URL | What It Has | Registration |
|---------|-----|-------------|--------------|
| **ImmPort** | [immport.org/shared](https://www.immport.org/shared/) | Patient-level clinical trial data: demographics, adverse events, lab results from 145+ immunology trials | Free (NIH-funded) |
| **TCGA via cBioPortal** | [cbioportal.org](https://www.cbioportal.org/) | Cancer genomics + clinical data (age, gender, stage, mutations, treatment) for 10,000+ patients | Free download |
| **GEO (GSE91061)** | [ncbi.nlm.nih.gov/geo](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE91061) | Gene expression for melanoma patients on anti-PD-1 (responders vs non-responders) | Free download |
| **ClinicalTrials.gov** | [clinicaltrials.gov](https://clinicaltrials.gov/) | Trial results with adverse event rates by therapy | Free search |
| **VigiBase (WHO)** | [vigiaccess.org](https://www.vigiaccess.org/) | 28M+ global adverse event reports | Free (limited public access) |

## How to Expand the FAERS Data

The openFDA API limits responses to 100 records per query. To fetch more data:

```python
import urllib.request, json

# Paginate: use skip parameter (max skip=25000)
for skip in range(0, 1000, 100):
    url = f'https://api.fda.gov/drug/event.json?search=patient.drug.openfda.generic_name:"PEMBROLIZUMAB"&limit=100&skip={skip}'
    # ... fetch and parse
```

For the full FAERS quarterly data dumps (millions of records), download from:
[fda.gov/drugs/fdas-adverse-event-reporting-system-faers](https://www.fda.gov/drugs/fdas-adverse-event-reporting-system-faers)
