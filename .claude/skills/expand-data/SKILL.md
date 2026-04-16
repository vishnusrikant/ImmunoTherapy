---
name: expand-data
description: Use when the user asks for more data — additional FAERS records, new ImmPort studies, or new data sources (TCGA, GEO, ClinicalTrials.gov).
---

# Expand the Dataset

Guide for safely adding more data to the ImmunoTherapy project.

## When This Skill Applies

- User asks to pull more FAERS records
- User asks to add a new ImmPort study
- User wants data from TCGA, cBioPortal, GEO, or ClinicalTrials.gov
- User asks how to get patient-level lab values (NLR, CRP, IL-6)

## FAERS — Expand Further

Current state: 5,000 reports per drug via openFDA API (API max `skip=25000`).

### To add more FAERS data:

1. **Quarterly dumps** have millions of records. Download from:
   https://fda.gov/drugs/fdas-adverse-event-reporting-system-faers
2. Data comes as pipe-delimited files: `DEMO`, `DRUG`, `REAC`, `OUTC`, `THER`, `INDI`, `RPSR`
3. Join on `primaryid` + `caseid`
4. Filter `DRUG` on our 11 immunotherapy drug names (see `datasets/reference/immunotherapy_drugs.csv`)
5. Merge with `REAC` (reactions) and `OUTC` (outcomes) for severity labels

### To add new immunotherapy drugs:

Edit `datasets/reference/immunotherapy_drugs.csv` and re-run the openFDA pull script. Candidates:
- **Cemiplimab** (Libtayo) — PD-1, approved 2018
- **Dostarlimab** (Jemperli) — PD-1, approved 2021
- **Relatlimab** (Opdualag, combo with nivolumab) — LAG-3, approved 2022
- **Tremelimumab** (Imjudo) — CTLA-4, approved 2022

## ImmPort — Add a New Study

### To add a new ImmPort study:

1. **Requires authenticated download.** User must have ImmPort credentials.
2. Authenticate:
   ```python
   import urllib.parse, urllib.request, json
   data = urllib.parse.urlencode({'username': USER, 'password': PW}).encode()
   req = urllib.request.Request('https://www.immport.org/auth/token', data=data)
   token = json.loads(urllib.request.urlopen(req).read())['access_token']
   ```
3. For each endpoint in `demographic`, `adverseEvent`, `assessment`, `labtest`, `intervention`, `condition`, `arm`, `biosample`, `plannedVisit`:
   ```python
   url = f'https://www.immport.org/data/query/api/study/{ep}/{SDY}'
   ```
4. Save to `datasets/immport/{SDY}/{SDY}_{endpoint}.csv`

### Candidate studies to add (discovered via API search):

| SDY | Subjects | Description | Priority |
|-----|----------|-------------|----------|
| SDY1108 | 13 | "Systemic Immunity for Cancer Immunotherapy" | Low (mouse study) |
| SDY901 | 8 | PD-1 pathway in EGFR lung tumors | Low (small) |
| SDY1658 | 16 | GBM tumor samples | **Already downloaded** |
| SDY1597 | 30 | Breast cancer post-chemo | **Already downloaded** |
| SDY1733 | 56 | Anti-PD-1 HCC | **Already downloaded (primary)** |

**Reality check:** ImmPort is mostly allergy/vaccine/transplant studies. Only ~3 usable cancer immunotherapy studies with clinical data. Not a scalable source.

## TCGA / cBioPortal — Cancer Genomics

10,000+ patients across 33 cancer types. Accessible without registration:
- Web: https://www.cbioportal.org/
- R package: `cBioPortalData`
- Python: `bravado` + cBioPortal Swagger API

**Useful for:**
- Cancer type + stage + TMB (tumor mutation burden)
- Demographic + treatment + survival
- **Not useful for:** adverse events, irAEs

## GEO — Gene Expression

`GSE91061` — melanoma patients on anti-PD-1, responders vs non-responders.
- Accessible via: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE91061
- Small sample sizes; requires bioinformatics skills
- Better suited for response prediction than severity prediction

## ClinicalTrials.gov — Aggregate AE Rates

For validated benchmark rates:
- Search: https://clinicaltrials.gov/search?term=pembrolizumab
- Pull "Adverse Events" tab from each trial's Results section
- Aggregate rates, not patient-level
- Good for comparing model predictions to real-world trial rates

## VigiBase (WHO) — Global AE Data

28M+ global adverse event reports. Public access is limited (aggregate only):
- https://www.vigiaccess.org/
- Not scrapable; would need data use agreement for raw data

## Do Not

- Do not scrape FDA or ImmPort — use documented APIs
- Do not commit credentials to the repo
- Do not mix FAERS reports with `safetyreportid` collisions — deduplicate by `safetyreportid + receiptdate`
- Do not assume a new data source will have CTCAE grades — most don't

## Priority Order for Next Expansion

If user asks "what's the best next data source?":
1. **FAERS quarterly dumps** — largest scale-up, easiest, same format we already process
2. **ClinicalTrials.gov AE tables** — validated benchmark rates for sanity-checking the model
3. **cBioPortal** — if user wants to add genomic features (TMB, mutation signatures)
4. **New ImmPort studies** — diminishing returns beyond SDY1733
