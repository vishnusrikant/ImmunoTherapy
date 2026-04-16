# ImmPort Data

Patient-level clinical data from NIH/NIAID-funded immunology studies, downloaded via the [ImmPort Shared Data API](https://docs.immport.org/apidocumentation/) on April 15, 2026.

## What's Here

```
immport/
├── README.md                                            <- This file
├── SDY1733/                                             <- PRIMARY: anti-PD-1 HCC study (56 patients, 10 on immunotherapy)
│   ├── SDY1733_patients_consolidated.csv                <- One row per patient (merged demographics + labs + assessments + interventions)
│   ├── SDY1733_metadata.json                            <- Study metadata
│   ├── SDY1733_demographic.csv                          <- Age, sex, race, country, arm
│   ├── SDY1733_intervention.csv                         <- Drug/surgery/chemo history (112 rows)
│   ├── SDY1733_assessment.csv                           <- BCLC cancer stage + cirrhosis status (112 rows)
│   ├── SDY1733_labtest.csv                              <- AFP (tumor marker) + HBV/HCV status (112 rows)
│   ├── SDY1733_immuneExposure.csv                       <- Disease exposure details (56 rows)
│   ├── SDY1733_biosample.csv                            <- Blood/tumor sample info (211 rows)
│   ├── SDY1733_arm.csv                                  <- Study arm definitions
│   ├── SDY1733_condition.csv                            <- Disease condition
│   ├── SDY1733_inclusionExclusion.csv                   <- Enrollment criteria
│   └── SDY1733_plannedVisit.csv                         <- Visit schedule
├── SDY1597/                                             <- COMPARATOR: breast cancer post-chemo (30 patients, 15 cases + 15 controls)
│   ├── SDY1597_patients_consolidated.csv                <- One row per patient
│   └── ...                                              <- Same layout as SDY1733
├── SDY1658/                                             <- GBM tumor samples (16 patients, tumor tissue only, no clinical assessments)
│   └── ...
└── download_summary.json                                <- Row counts per endpoint per study
```

## Why Only 3 Studies?

ImmPort's **primary focus is allergy, vaccines, and transplant research** — not cancer immunotherapy. Out of **210 cancer-adjacent studies**, only a handful are human cancer immunotherapy trials with usable clinical data. After filtering:

| Criterion | Studies |
|-----------|---------|
| Total ImmPort studies with "cancer" term | 149 |
| Human subjects with immunotherapy context | ~15 |
| Human + cancer + clinical assessment data | **3** (SDY1733, SDY1597, SDY1658) |

Most "immunotherapy" studies in ImmPort are **allergy immunotherapy** (peanut, egg, cockroach desensitization) — not cancer immunotherapy.

## Primary Study: SDY1733

**"Single-Cell immune signature for detecting early-stage HCC and early assessing PD-1 immunotherapy efficacy"**

- **56 patients** (15 hepatic hemangioma controls + 41 HCC patients)
- **10 patients received anti-PD-1 immunotherapy**: 5 Nivolumab + 5 Camrelizumab
- **PI:** Natural Science Foundation of Zhejiang Province
- **DOI:** [10.21430/M3HN665KSB](https://doi.org/10.21430/M3HN665KSB)

### Patient Features Available (per-patient)

| Feature | Coverage | Notes |
|---------|----------|-------|
| Age | 100% | 27-79 years, mean 55.2 |
| Gender | 100% | 38 Male / 18 Female |
| Race | 100% | All Asian (Chinese cohort) |
| BCLC stage | 73% | A (31), C (10), N/A for controls |
| Cirrhosis (Y/N) | 100% | 21 Yes / 35 No |
| HBV/HCV infection | 100% | 33 HBV / 23 uninfected |
| AFP (alpha-fetoprotein) | Partial | Tumor marker, continuous |
| Intervention | 100% | Surgery / Nivolumab / Camrelizumab / Sorafenib / Chemo |

### Why This Matters for the Model

Although SDY1733 is small (n=56), it provides features that **FAERS completely lacks**:
- **Cancer staging** (BCLC A/B/C) — strong severity predictor
- **Pre-existing liver disease** (cirrhosis) — a validated irAE risk factor
- **Viral infection status** (HBV/HCV) — modulates immune response
- **Tumor marker values** (AFP) — continuous feature

This study is a **high-quality small validation cohort** that can be used to:
1. Validate patterns learned from FAERS on ground-truth clinical data
2. Engineer new features that might generalize (cirrhosis flag, tumor stage)
3. Compare the model's predictions against real treatment decisions

## Secondary Study: SDY1597

**"Immune Cell Repertoires in Breast Cancer Patients after Adjuvant Chemotherapy"**

- **30 subjects** (15 breast cancer patients + 15 healthy controls)
- Treated with chemotherapy agents (Adriamycin, Cytoxan, Taxotere, Carboplatin, Herceptin)
- **Not immunotherapy**, but useful as a cancer-treatment comparator
- Cancer stages recorded: IA, IB, IIA, IIB, IIIA

## Tertiary Study: SDY1658

**"Comparative CyTOF analysis of resected-tumor samples from human GBM patients"**

- **16 patients** with glioblastoma (GBM)
- Tumor tissue samples only — no clinical assessments or lab values
- Low relevance for side-effect modeling; included for completeness

## What's Missing

- **No adverse event data** — ImmPort's `adverseEvent` endpoint returned 0 rows for all three studies. ImmPort's AE reporting is not a strength of these particular studies.
- **No CTCAE grades** — assessments are specific to cancer stage/cirrhosis, not adverse-event severity.
- **No inflammatory markers** — no NLR, CRP, IL-6, or D-dimer values in these studies.

## How to Use This Data Alongside FAERS

| Aspect | FAERS (124,982 rows) | ImmPort (86 patients) |
|--------|---------------------|------------------------|
| Sample size | Very large | Very small |
| Labeled severity | Derived from seriousness flags | Not directly labeled (no AE data) |
| Cancer stage | Missing | Yes (SDY1733 BCLC, SDY1597 TNM) |
| Pre-existing conditions | Missing | Yes (cirrhosis, HBV/HCV) |
| Lab values | Missing | Partial (AFP) |
| Cohort diversity | Global, 11+ drugs | Limited (mostly Chinese HCC + US breast cancer) |

**Recommended use:**
1. **Primary training** → FAERS
2. **Feature ideas / validation** → ImmPort (small cohort sanity check)
3. **Literature enrichment** → ImmPort metadata citations point to peer-reviewed studies

## Reproducing the Download

```python
import urllib.request, json

# 1. Get auth token
import urllib.parse
data = urllib.parse.urlencode({'username': 'YOUR_USER', 'password': 'YOUR_PASS'}).encode()
req = urllib.request.Request('https://www.immport.org/auth/token', data=data)
token = json.loads(urllib.request.urlopen(req).read())['access_token']

# 2. Download study data
url = f'https://www.immport.org/data/query/api/study/labtest/SDY1733'
req = urllib.request.Request(url, headers={'Authorization': f'bearer {token}'})
rows = json.loads(urllib.request.urlopen(req).read())
```

Available endpoints for each study (`/api/study/{endpoint}/{SDY}`):
`demographic`, `adverseEvent`, `assessment`, `labtest`, `intervention`, `condition`,
`inclusionExclusion`, `immuneExposure`, `arm`, `biosample`, `plannedVisit`

Full OpenAPI spec: https://www.immport.org/data/query/v3/api-docs
