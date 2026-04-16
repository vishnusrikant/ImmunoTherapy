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

**Already downloaded** (2026-04-15): 7 immunotherapy studies, 1,218 patients — see `datasets/cbioportal/` and `scripts/cbio_download.py`.

10,000+ patients across 33 cancer types. Accessible without registration:
- Web: https://www.cbioportal.org/
- REST API: https://www.cbioportal.org/api (we use this — see `scripts/cbio_download.py` for the pattern)
- R package: `cBioPortalData`
- Python: `bravado` + cBioPortal Swagger API

**Useful for:**
- Cancer type + stage + TMB (tumor mutation burden)
- Pre-treatment features: LDH, ECOG, metastasis sites, steroids, prior therapies
- Demographic + treatment + survival (OS/PFS)
- **Not useful for:** adverse events, irAEs (no AE columns in any cBioPortal study)

### To add more cBioPortal studies:

1. Find candidate studies at https://www.cbioportal.org/datasets (filter for immunotherapy cohorts)
2. Add the study ID to the `STUDIES` list in `scripts/cbio_download.py`
3. Re-run `python3 scripts/cbio_download.py`
4. Re-run `python3 scripts/cbio_consolidate.py` to rebuild `all_patients_consolidated.csv`
5. If the new study uses drug names not in `DRUG_MAP` in `cbio_consolidate.py`, extend the map

Candidate studies not yet pulled (discovered during exploration):
- `skcm_mskcc_2014` — melanoma ipilimumab (64)
- `skcm_dfci_2015` — melanoma combo (110)
- `nsclc_mskcc_2018` — NSCLC anti-PD-1/PD-L1 (75)

## GEO — Gene Expression (Low Priority — explored 2026-04-15)

NCBI Gene Expression Omnibus stores RNA-seq / microarray data, NOT clinical data.

**Access (free, no auth):**
- E-Utilities API: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` (esearch / esummary / efetch, `db=gds`)
- FTP: `ftp.ncbi.nlm.nih.gov/geo/series/GSEnnn/GSE*/` (SOFT / SeriesMatrix / MINiML / supplementary)
- Python: `GEOparse` package

**Verdict: SKIP for severity prediction.** Confirmed via direct API queries:
- `checkpoint inhibitor toxicity`: **0** GSE results
- `immune related adverse event`: 8 results, none with CTCAE/AE labels
- `cytokine release syndrome CAR-T`: **0** results

GEO does not track irAEs. Features would be gene expression values (requires heavy bioinformatics), not standard clinical variables. Cannot merge with FAERS.

**GSE91061** (Riaz et al. Cell 2017, melanoma anti-PD-1, 65 patients, 109 RNA-seq samples) is the flagship ICI study — but it's **the same cohort we already have from cBioPortal** as `mel_iatlas_riaz_nivolumab_2017`, just with added expression.

**If user insists on GEO:** use `GEOparse` to pull GSE91061, compute a TIL / IFN-γ signature score per patient, join back to the cBioPortal Riaz cohort on sample ID. Experimental, marginal payoff.

**Better alternatives discovered during exploration:**
- **irAExplorer** — pan-cancer database, 71,087 ICI patients × 293 harmonized irAE categories. Purpose-built for this project. Check access next.
- **VigiBase (WHO)** — ~150K ICI AEs 2008-2023, complements FAERS; access may require DUA.

## ClinicalTrials.gov — Aggregate AE Rates (Recommended next source)

**Modern v2 JSON API, no auth required** (verified 2026-04-15):
- `https://clinicaltrials.gov/api/v2/studies?query.intr=pembrolizumab&pageSize=100`
- `https://clinicaltrials.gov/api/v2/studies/{NCT_ID}` — full study record

Trials with `hasResults=true` expose a rich `resultsSection.adverseEventsModule`:

```
adverseEventsModule:
  eventGroups: [{id, title, deathsNumAffected, seriousNumAffected, seriousNumAtRisk, ...}]
  seriousEvents: [{term, organSystem, sourceVocabulary=MedDRA, stats: [{groupId, numEvents, numAffected, numAtRisk}]}]
  otherEvents:   [...]
```

Example: NCT02362594 (adjuvant pembrolizumab melanoma) returned 148 serious AEs, 25 deaths / 514 pembro-arm patients.

**How to use:** Pull all ICI trials with results → build benchmark table of irAE rates by drug × cancer × MedDRA term. Useful for **model evaluation** (comparing FAERS-trained predictions to real trial rates), not for training (data is aggregate, not patient-level).

### irAExplorer (checked 2026-04-15) — NOT useful

- https://irae.tanlab.org/ aggregates ClinicalTrials.gov into a viz portal
- **No patient-level data** — authors explicitly state: *"granularity of adverse event incidence was not reported at the individual level… This prevents further comorbidity analysis."*
- **No API, no CSV download** — only the interactive website + an R parsing script on GitHub
- Their 71,087-patient figure is a sum across 343 trials, not individual records
- If we want what irAExplorer provides, pull ClinicalTrials.gov v2 API directly (see above) — same data, our format

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
