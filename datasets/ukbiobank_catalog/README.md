# UK Biobank Data Showcase Catalog (Metadata Only)

Publicly-available UK Biobank field metadata — **no patient-level data**. Used
to cite exact field IDs and population coverage when discussing the CRP /
IL-6 / autoimmune-history feature gap in our model's limitations section.

## What's here

| File | Source schema | Rows | Purpose |
|---|---|---|---|
| `fields.tsv` | Schema 1 (data dictionary) | 11,822 | Every UKB field with title, units, participant count, category |
| `encodings.tsv` | Schema 2 | 859 | Master list of encoding dictionaries |
| `categories.tsv` | Schema 3 | 411 | Category hierarchy labels |
| `encoding_values_hierint.tsv` | Schema 11 | 28,901 | Values for hierarchical integer encodings |
| `encoding_values_hierstr.tsv` | Schema 12 | 46,928 | Values for hierarchical string encodings (incl. ICD-10) |
| `gap_features_summary.csv` | derived | 34 | Subset of fields relevant to our documented gap features |
| `autoimmune_icd10_codes.csv` | derived | 304 | ICD-10 codes from 24 irAE-relevant autoimmune blocks |

## Key findings for the limitations section

| Gap feature | UKB entry point | Participants | Coverage of 502K cohort | Realistic availability |
|---|---|---|---|---|
| **C-reactive protein** | Field 30710 (mg/L) | **469,326** | 93% | Near-universal — strong candidate if access obtained |
| **Autoimmune history** | Field 41270 (ICD-10 diagnoses from HES), filtered to 304 codes across 24 blocks | **448,651** | 89% | Near-universal — strong candidate |
| **IL-6** | Field 30900 (Olink Explore 3072 panel, Data-Coding 143 indexes IL-6 as one assay) | **53,039** | 11% | Sub-study only — usable but small |
| **Albumin** | Field 30600 / 23479 | 431,857 / 488,455 | 86% / 97% | Already in Chowell 2021 — cross-validation possible |
| **Neutrophil / lymphocyte (NLR inputs)** | Fields 30120, 30140, etc. | ~477,948 | 95% | Already in Chowell 2021 — cross-validation possible |

## Access notes

- **This catalog (metadata) is public** — downloaded without login from `biobank.ndph.ox.ac.uk/ukb/scdown.cgi`
- **The underlying patient-level data is NOT public** — requires an approved research application from an affiliated institution, with a student reduced-fee rate of £500 + VAT (as of April 2026)
- For a high-school InspiritAI project without institutional sponsorship, UK Biobank access is **out of scope** — this catalog exists so the project can cite exact fields and coverage in the "future work" section

## Reproducing

```bash
python3 scripts/ukbiobank_catalog_download.py
```

Pulls the five schemas (idempotent — skips files already on disk) and regenerates
`gap_features_summary.csv` + `autoimmune_icd10_codes.csv`.

## Source URLs

- UKB Showcase index: https://biobank.ndph.ox.ac.uk/showcase/index.cgi
- Schema download pattern: `https://biobank.ndph.ox.ac.uk/ukb/scdown.cgi?fmt=txt&id={1,2,3,11,12}`
- ICD-10 encoding (id=19): 19,190 codes in `encoding_values_hierstr.tsv`
- Olink proteomics (Field 30900, UKB-PPP): 53,039 participants, 2,941 proteins on Olink Explore 3072 panel

## License / attribution

UK Biobank Showcase metadata is provided by UK Biobank under their public
terms. ICD-10 codes are © WHO, used under the permission terms stated in
encoding 19 of the UKB Showcase. Cite as:

> UK Biobank Showcase. https://biobank.ndph.ox.ac.uk/showcase/ (accessed 2026-04-16)
