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

Current state:
- openFDA API: 124,982 rows / 42,469 reports / 11 drugs (`datasets/faers/`)
- Quarterly dumps 2024-2025: 288,179 rows / 93,617 reports / 15 drugs (`datasets/faers_quarterly/`)

### To pull older quarterly data (2004-2023):

Infrastructure already exists — just edit + re-run:

1. Open `scripts/faers_quarterly_pull.py`
2. Extend the `QUARTERS` list (e.g., add `('2023', '1') ... ('2023', '4')`)
3. Run `python3 scripts/faers_quarterly_pull.py`
4. The script skips already-downloaded zips in `/tmp/faers_quarterly/`
5. Output goes to `datasets/faers_quarterly/` — may want to rename outputs per time range

URL pattern: `https://fis.fda.gov/content/Exports/faers_ascii_{yyyy}q{n}.zip` — ~65 MB per quarter.
Available from 2004 Q1 at [fis.fda.gov/extensions/FPD-QDE-FAERS](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html).

### File format (for reference)

Each quarterly zip contains 7 pipe-delimited ASCII tables, joined on `primaryid`:
- `DEMO` — demographics (age, sex, weight, country, event date)
- `DRUG` — drug records (drugname, prod_ai, role_cod; filter to PS/SS for attribution)
- `REAC` — reactions (MedDRA preferred term)
- `OUTC` — outcomes (DE/LT/HO/DS/CA/RI/OT codes)
- `INDI` — indications (what the drug was given for)
- `THER` — therapy start/stop dates
- `RPSR` — report source

### Outcome → severity mapping

- `DE` (Died) → Severe
- `LT` (Life-Threatening) → Severe
- `DS` (Disability) → Severe
- `HO` (Hospitalization, if not also DE/LT/DS) → Medium
- Everything else → Mild

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

## Chowell 2021 Pan-Cancer ICI Cohort (downloaded 2026-04-16) — useful

**Already downloaded.** Pulled from Supplementary Data 1 of Chowell et al. *Nat Biotech* 2021 (DOI 10.1038/s41587-021-01070-8) via `scripts/chowell_download.py`.

- `datasets/chowell_2021/chowell_all.csv` — 1,479 patients × 29 cols, **100% feature coverage**
- Fields: NLR, Albumin, Platelets, HGB, BMI, exact Age, Sex, TMB, MSI, Drug_class, Cancer_Type, Response, OS/PFS
- Split: 1,184 training (multi-institution) + 295 MSK test

**Appropriate uses:**
- Cross-study validation of NLR / albumin / age / drug-class effects
- Pre-treatment feature enrichment when our model predicts response alongside severity
- Feature-distribution sanity check vs FAERS + cBioPortal

**Do NOT use for training the severity classifier.** This cohort has response + survival outcomes, not irAE severity. Our FAERS-derived Mild/Medium/Severe labels remain the training target.

**Do NOT try to join on patient ID to cBioPortal.** MSK uses different de-identification schemes (Chowell has integer `SAMPLE_ID` like `8384`; cBioPortal `nsclc_pd1_msk_2018` has `P-0000###`).

### Candidate extensions to the Chowell pull (not yet done)

- **Valero et al. 2021 Nat Comm** — 1,714 MSK ICI patients with NLR + TMB + **ECOG PS** (Chowell doesn't have ECOG). Supp data at [10.1038/s41467-021-20935-9](https://www.nature.com/articles/s41467-021-20935-9). Overlaps with Chowell test set — deduplicate on SAMPLE_ID if merging.
- **LORIS Zenodo release** — `zenodo.org/records/11186449`. Repo has scripts + some cohort data; raw MSK1/MSK2 is institutional.

## Khan et al. JITC 2025 (downloaded 2026-04-17) — closes the IL-6 + irAE-label gap

**Already downloaded.** Pulled from Zenodo deposit 17943391 (CC BY 4.0) via `scripts/khan_jitc_2025_download.py`.

- `datasets/khan_jitc_2025/khan_patients_consolidated.csv` — 162 patients × 54 cols (primary modeling file)
- 146/162 with baseline 40-cytokine panel: IL-6, IFN-γ, TNF-α, IL-1β, IL-2, IL-4, IL-8, IL-10, IL-16 + 32 chemokines
- 162/162 with **irAE binary (Grade 0-1 vs 2+) + CTCAE grade (0-3) + organ system** — paired with the cytokines in the same patient rows
- Drug class: PD-1 (108), PD-L1 (26), combo (24), CTLA-4 mono (1). No CAR-T.
- Source: Khan et al. *J Immunother Cancer* 2025 [DOI 10.1136/jitc-2025-012414](https://doi.org/10.1136/jitc-2025-012414)

**Appropriate uses:**
- Train a baseline-cytokine → "any irAE" binary classifier (n=146)
- Cross-validate demographic + drug-class feature effects against FAERS
- Limitations-section grounding: shows exactly which gap features ARE accessible

**Do NOT use for training the FAERS severity classifier as-is** — different label vocabulary (Grade 0-1/2+ vs Mild/Medium/Severe), different patient population (single institution, n=162). Train it as a parallel sidecar model.

**Critical caveat:** the Zenodo file column for grade has two spaces — `Highest grade  of irAE` — the script renames it to `highest_grade_iraE`. Don't re-introduce the typo.

## The Remaining Public-Data Feature Gap (post-Khan 2025)

After Khan JITC 2025, two of the three originally-flagged predictors are still not obtainable at patient level with paired irAE labels:

- **CRP** — SCORPIO (Nat Med 2024) uses it, but dataset is institutional-only. Khan does NOT include CRP.
- **Autoimmune history (ICD-10 codes)** — UK Biobank has them but requires formal application + affiliation. Khan includes ANA titer for 65/162 patients as a partial autoimmune-tendency surrogate, not the gold-standard ICD list.

**IL-6 is now closed** by Khan JITC 2025 (146 patients). Do NOT re-search for IL-6 + irAE label datasets.

**Do NOT keep re-exploring CRP and autoimmune-history.** Confirmed across FAERS, ImmPort, cBioPortal, Chowell, Valero, LORIS, GEO, irAExplorer, ClinicalTrials.gov, VigiBase, plus the round of Zenodo/Figshare/Mendeley/PhysioNet/Project Data Sphere/Vivli scanning that produced Khan. If the user asks, the honest answer is: documented in the project's limitations section; future work needs UK Biobank / All of Us / prospective trial access.

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

## VigiBase (WHO) — NOT useful (checked 2026-04-16)

56M+ global adverse event reports / ~40M unique cases (as of Dec 31, 2024), managed by WHO Uppsala Monitoring Centre.

**VigiAccess public site (https://www.vigiaccess.org/)**
- Web UI, search by substance only, returns aggregate AE counts
- **No CSV export, no bulk download, no public API** for the site itself
- Cannot train a model from it

**VigiBase Extract (the real dataset)**
- Flat text files for local analysis — requires application + Data Use Agreement
- **Fee-based** for researchers / universities / pharma. Free only to WHO Programme member organisations (national pharmacovigilance centres).
- "Strict evaluation process" — no guaranteed approval, timeline not designed for student projects
- **Even if approved, the extract excludes** narratives, medical history, and lab tests (stated in `who_vigibase_data_access_conditions.pdf`) — the exact patient-level detail we actually lack
- Contact: https://who-umc.org/contact-information/ · Docs: https://who-umc.org/vigibase-data-access/

**Verdict: SKIP for this project.** VigiBase is spontaneous-report format like FAERS — it would duplicate what we already have (413K rows, 15 drugs) without adding the clinical variables that FAERS lacks. The approval + fee process is not proportional to an InspiritAI student project.

## Do Not

- Do not scrape FDA or ImmPort — use documented APIs
- Do not commit credentials to the repo
- Do not mix FAERS reports with `safetyreportid` collisions — deduplicate by `safetyreportid + receiptdate`
- Do not assume a new data source will have CTCAE grades — most don't

## Priority Order for Next Expansion

If user asks "what's the best next data source?":
1. **FAERS quarterly dumps (extend to 2020-2023)** — largest scale-up, easiest, same format we already process
2. **ClinicalTrials.gov AE tables** — validated benchmark rates for sanity-checking the model
3. **Valero 2021 Nat Comm supplementary** — adds ECOG PS to the Chowell features (both MSK, need dedup)
4. **cBioPortal** — already broad; adding more studies has diminishing returns
5. **New ImmPort studies** — diminishing returns beyond SDY1733

**Do NOT pursue (already evaluated, dead-end):** GEO, irAExplorer, VigiBase/VigiAccess, UK Biobank/SCORPIO/LORIS raw data (all institutional-only). Also already pulled / no second pass needed: Khan JITC 2025 (the cytokines + irAE labels cohort).
