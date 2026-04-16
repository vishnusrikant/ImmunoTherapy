# FAERS Quarterly Data — 2024 + 2025 (Full Year)

Expanded FAERS pull from the **FDA Quarterly Data Extract files** covering all 8 quarters from 2024 Q1 through 2025 Q4. Downloaded 2026-04-15.

## Why This Matters

The existing `datasets/faers/` files came from the openFDA REST API, which caps results at `skip=25000` per query (~5,000 reports per drug). The quarterly dumps are the same underlying database **without the API cap**, and they include 4 newer immunotherapy drugs we hadn't pulled.

| Metric | Existing (openFDA API) | Quarterly 2024-2025 | Combined potential |
|--------|-----------------------:|--------------------:|-------------------:|
| Unique reports | 42,469 | **93,617** | 136K+ |
| Total AE rows | 124,982 | **288,179** | 413K+ |
| Drugs covered | 11 | 15 | 15 |
| Time range | Mixed / cumulative | 2024-01 through 2025-12 | — |

## Files

| File | Rows | Reports | Size |
|------|-----:|--------:|-----:|
| `checkpoint_inhibitor_adverse_events_2024_2025.csv` | 253,366 | 82,507 | 36 MB |
| `cart_therapy_adverse_events_2024_2025.csv` | 34,813 | 11,110 | 5 MB |

Both files share the same schema, matching `datasets/faers/*.csv` plus 3 extra columns (`primaryid`, `caseid`, `source_year_quarter`) and a pre-computed `severity` label.

## Source

- URL pattern: `https://fis.fda.gov/content/Exports/faers_ascii_{yyyy}q{n}.zip`
- Landing page: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- Format: 7 pipe-delimited ASCII tables per quarter (DEMO, DRUG, REAC, OUTC, INDI, THER, RPSR)
- Total downloaded: ~515 MB zipped across 8 quarters
- No authentication required

## Drugs Matched

Matched case-insensitively against `DRUG.drugname` OR `DRUG.prod_ai`, restricted to `role_cod IN ('PS', 'SS')` (primary or secondary suspect — the drug to which the AE is attributed).

### Checkpoint Inhibitors (9 drugs)

| Drug | Target | Rows | Notes |
|------|--------|-----:|-------|
| Pembrolizumab (Keytruda) | PD-1 | 116,709 | |
| Nivolumab (Opdivo) | PD-1 | 51,043 | |
| Atezolizumab (Tecentriq) | PD-L1 | 36,189 | |
| Durvalumab (Imfinzi) | PD-L1 | 24,249 | |
| Ipilimumab (Yervoy) | CTLA-4 | 16,609 | |
| Cemiplimab (Libtayo) | PD-1 | 3,898 | **New** — not in existing pull |
| Dostarlimab (Jemperli) | PD-1 | 3,470 | **New** — not in existing pull |
| Tremelimumab (Imjudo) | CTLA-4 | 1,192 | **New** — not in existing pull |
| Relatlimab (Opdualag) | LAG-3 | 7 | **New** — approved 2022, few reports |

### CAR-T (6 products)

| Drug | Target | Rows |
|------|--------|-----:|
| Axicabtagene ciloleucel (Yescarta) | CD19 | 14,840 |
| Ciltacabtagene autoleucel (Carvykti) | BCMA | 8,466 |
| Tisagenlecleucel (Kymriah) | CD19 | 6,245 |
| Brexucabtagene autoleucel (Tecartus) | CD19 | 2,568 |
| Idecabtagene vicleucel (Abecma) | BCMA | 1,375 |
| Lisocabtagene maraleucel (Breyanzi) | CD19 | 1,319 |

## Derived Severity Distribution

| Class | Mild | Medium | Severe | Total rows |
|-------|-----:|-------:|-------:|-----------:|
| Checkpoint | 105,629 (42%) | 79,635 (31%) | 68,102 (27%) | 253,366 |
| CAR-T | 14,809 (43%) | 7,772 (22%) | 12,232 (35%) | 34,813 |

**Severity rule** (same as existing files):
- Severe = `seriousness_death` OR `seriousness_life_threatening` OR `seriousness_disabling`
- Medium = `seriousness_hospitalization` only
- Mild = everything else

## Schema (columns)

Matches `datasets/faers/*.csv` plus the bolded additions:

```
primaryid          ← NEW  (FAERS report ID; use for deduping vs. openFDA pull)
caseid             ← NEW  (case-level ID, spans multiple reports of same case)
drug_name          (canonical immunotherapy drug)
drug_class         ("Checkpoint Inhibitor" or "CAR-T")
patient_age
patient_age_unit   (YR / MON / WK / DY / HR / DEC)
patient_sex        (M / F / UNK)
patient_weight_kg  (converted from LBS if needed)
indication         (cancer type from INDI table; may be empty)
reaction           (MedDRA preferred term)
reaction_outcome   (empty in quarterly format — not in DEMO)
serious            ("Serious" if any outcome code present, else "Non-Serious")
seriousness_death            (0/1)
seriousness_hospitalization  (0/1)
seriousness_life_threatening (0/1)
seriousness_disabling        (0/1)
report_date        (FDA receipt date; YYYYMMDD)
country            (occr_country preferred; falls back to reporter_country)
source_year_quarter ← NEW  ("2024Q1" ... "2025Q4")
severity           ← NEW  ("Mild" / "Medium" / "Severe" derived label)
```

## How To Use With The Existing FAERS Data

**Option A — Replace:** Use the quarterly data alone. More volume, cleaner severity label, newer drugs.

**Option B — Merge + dedupe:** Combine with existing `datasets/faers/` data, dedupe by `primaryid` (equivalent to `safetyreportid` in openFDA format). The existing file uses the openFDA schema which does not expose `primaryid` directly — dedupe is practical only on the quarterly side.

**Option C — Keep separate:** Train on quarterly data, use existing for cross-validation. Cleanest comparison since time periods don't overlap.

**Recommended for modeling:** Option A. The quarterly data covers a bounded, recent time window (2024-2025) with complete report linkage and MedDRA-coded reactions.

## Reproducing

```bash
python3 scripts/faers_quarterly_pull.py
```

The script downloads missing quarterly zips to `/tmp/faers_quarterly/`, then parses each. Total runtime: ~5 min download + ~3 min parsing on a typical connection. Output: this directory.

## Limitations

- **Indication coverage is partial** — `INDI.indi_pt` populated for ~60% of reports; many have drug + AE but no cancer type listed
- **Age precision varies** — most values are in years, but some use decades ("age_cod=DEC") especially for older reports
- **Weight missingness ~40%** (same as openFDA pull)
- **No CTCAE grades** — severity derived from seriousness outcome codes, not clinician-assigned grades
- **Reaction → drug attribution imperfect** — FAERS is spontaneous reporting; co-administered drugs may be the true cause
- **Duplicate reporting** — same event reported by multiple parties (patient, doctor, manufacturer); dedupe by `caseid` collapses these
