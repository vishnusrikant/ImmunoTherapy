# Khan et al. JITC 2025 — ICI Cohort with Cytokines + irAE Labels

Patient-level public ICI dataset that **closes the FAERS feature gap on a key axis**: it pairs baseline cytokine measurements (40-marker multiplex panel including IL-6, IFN-γ, TNF-α, IL-1β, IL-10) with **irAE occurrence labels** in the same 162 cancer patients.

> Khan S, Malladi VS, von Itzstein MS, ..., Gerber DE. *"Innate and adaptive immune features associated with immune-related adverse events."* J Immunother Cancer 2025;13(9):e012414. DOI: [10.1136/jitc-2025-012414](https://doi.org/10.1136/jitc-2025-012414) · PMC: [PMC12506470](https://pmc.ncbi.nlm.nih.gov/articles/PMC12506470/)

Data: Zenodo record 17943391, deposited 2025-12-15. DOI [10.5281/zenodo.17943391](https://zenodo.org/records/17943391). License **CC BY 4.0**.

## Why this cohort matters for the project

The project's documented public-data feature gap (CRP / IL-6 / autoimmune history paired with irAE labels) is **partially closed** by this deposit:

| Gap feature | Closed by Khan 2025? | Notes |
|---|---|---|
| **IL-6** (baseline) | **Yes** | 146/162 patients with paired BL + 6-8wk values |
| Other cytokines (IFN-γ, TNF-α, IL-1β, IL-10, IL-2, IL-4, IL-8, IL-16) | **Yes** | Same 146-patient panel |
| 32 chemokines (CCL/CXCL families, fractalkine, MIF, GM-CSF) | **Yes** | Same panel |
| **ANA autoantibody titer** (autoimmune surrogate) | **Partial** | 65/162 patients, BL + 2-4wk + 6-8wk |
| irAE binary occurrence | **Yes** | 162/162 patients (Grade 0-1 vs Grade 2+) |
| irAE CTCAE grade (0/1/2/3) | **Yes** | 162/162 |
| irAE organ system | **Yes** | Free text (e.g. "Pneumonitis, hypothyroidism") |
| CRP | No | Not measured in this study |
| CBC / albumin | No | Not measured |
| Autoimmune-history ICD codes | No | Use the cytokine panel + ANA as proxies instead |

It is the **only public dataset we found** with patient-level (cytokines + irAE labels) in the same rows. Contrast with FAERS (irAE present, cytokines absent) and Chowell 2021 (cytokines/labs present, irAE labels absent).

## Files

| File | Rows | Cols | Description |
|---|---:|---:|---|
| `khan_metadata.csv` | 162 | 13 | One row per patient: demographics, cancer, ICI drug, irAE labels, assay flags |
| `khan_cytokine_long.csv` | 292 | 42 | One row per (patient × timepoint), 40 cytokines |
| `khan_ana_long.csv` | 181 | 3 | ANA titer per (patient × timepoint) |
| `khan_patients_consolidated.csv` | 162 | 54 | **Primary modeling file** — metadata + baseline cytokines + baseline ANA, one row per patient |
| `supplementary_metadata.xlsx` | — | — | Raw download |
| `supplementary_cytokine.xlsx` | — | — | Raw download |
| `supplementary_ana.xlsx` | — | — | Raw download |

## Cohort composition

**ICI drug class (covers all four):**

| Drug | n |
|---|---:|
| pembrolizumab (PD-1) | 56 |
| nivolumab (PD-1) | 49 |
| ipilimumab + nivolumab (CTLA-4 + PD-1 combo) | 21 |
| atezolizumab (PD-L1) | 15 |
| durvalumab (PD-L1) | 8 |
| cemiplimab (PD-1) | 3 |
| avelumab (PD-L1) | 3 |
| Other combos (nivo+cabiralizumab, nivo+FPA008, durva+monalizumab, avelumab+PF-05082566, ipilimumab mono) | 7 |

No CAR-T patients — this cohort is checkpoint-inhibitor only.

**Cancer types (top):** NSCLC 81 · Melanoma 38 · HNSCC 11 · RCC 9 · SCLC 6 · plus mesothelioma, HCC, cholangio, pancreatic, GBM, breast, sarcoma, urothelial, rectal, cSCC.

## irAE label distribution

| Highest grade | n | irAE occurrence label |
|---|---:|---|
| 0 (no irAE) | 66 | Grade 0-1 |
| 1 | 4 | Grade 0-1 |
| 2 | 56 | Grade 2+ |
| 3 | 36 | Grade 2+ |
| 4-5 | 0 | — |
| **Total** | **162** | 70 / 92 split |

Mapping into the project's Mild/Medium/Severe convention:

| Khan grade | Project severity label |
|---|---|
| 0 | (no irAE — exclude or use as negative class) |
| 1 | Mild |
| 2 | Mild *(per `datasets/reference/ctcae_severity_grades.csv` — CTCAE 1-2 → Mild)* |
| 3 | Medium |
| 4-5 | Severe (none in this cohort) |

The 70/92 binary split also lets us train a **simple "any irAE" classifier** on this cohort with cytokines as features — a complementary task to the FAERS Mild/Medium/Severe model.

## Cytokine panel (40 markers, baseline + 6-8wk timepoints)

The 40 markers measured at both BL and 6-8wks (146 paired patients):

```
Interleukins:     IL-1β, IL-2, IL-4, IL-6, IL-8/CXCL8, IL-10, IL-16
Interferons:      IFN-γ
TNF family:       TNF-α
Chemokines (CCL): CCL1 (I-309), CCL2 (MCP-1), CCL3 (MIP-1α), CCL7 (MCP-3),
                  CCL8 (MCP-2), CCL11 (Eotaxin), CCL13 (MCP-4), CCL15 (MIP-1δ),
                  CCL17 (TARC), CCL19 (MIP-3β), CCL20 (MIP-3α), CCL21 (6Ckine),
                  CCL22 (MDC), CCL23 (MPIF-1), CCL24 (Eotaxin-2),
                  CCL25 (TECK), CCL26 (Eotaxin-3), CCL27 (CTACK)
Chemokines (CXCL): CXCL1 (Gro-α), CXCL2 (Gro-β), CXCL5 (ENA-78),
                   CXCL6 (GCP-2), CXCL9 (MIG), CXCL10 (IP-10),
                   CXCL11 (I-TAC), CXCL12 (SDF-1α+β), CXCL13 (BCA-1),
                   CXCL16 (SCYB16)
CX3C / CSF / migration: CX3CL1 (Fractalkine), GM-CSF, MIF
```

For pre-treatment **severity prediction**, only the **BL (baseline)** timepoint is appropriate — post-treatment values are confounded with treatment effects. The consolidated file uses BL only. Use `khan_cytokine_long.csv` if you want both timepoints (e.g. for an early-response signal model).

## Critical caveats

1. **No CRP, CBC, or CMP** — the gap closure is on **cytokines** specifically. CRP / albumin / NLR remain unobtainable in this dataset; we still rely on Chowell 2021 for NLR/albumin (no irAE labels) and FAERS for irAE labels (no labs).
2. **Single institution.** The paper is from UT Southwestern; cohort selection biases apply. Treat as a validation / proof-of-concept layer, not a population-representative training set.
3. **N=162 is small.** Useful for fitting interpretable models (logistic regression with cytokine ratios) and validation; not for high-capacity models without regularization or pretraining.
4. **No CAR-T.** This dataset doesn't help on the CAR-T side of the project.
5. **CTCAE grades top out at 3.** No grade 4-5 fatal/life-threatening events in this cohort. The model trained on Khan can predict "any irAE" or "Grade 2+" but cannot directly learn the Severe class — for that, we still need FAERS.
6. **Cohort overlap with FAERS is unknown** — Khan IDs (`NM1` ... `NM162`) cannot be linked to FAERS `safetyreportid`s. Treat these as independent cohorts.

## Three appropriate uses of this dataset

1. **Train a binary "any irAE" classifier** on the 146 patients with baseline cytokines. Compare which cytokines drive predictions. Cite published literature: IL-6 day-3 post CAR-T predicts severe CRS/ICANS (Bone Marrow Transplant 2025) — does the equivalent baseline IL-6 effect appear in checkpoint inhibitors here?
2. **Cross-validate FAERS-derived feature effects.** The FAERS severity model will learn coefficients for age, sex, drug class, indication. Train a parallel model on Khan with the same demographic features (no cytokines), check effect directions match. If FAERS and Khan agree on age/sex/drug-class effects, that's evidence the FAERS model isn't just learning reporting bias.
3. **Limitations slide grounding.** "We could not get CRP / autoimmune history at patient level with irAE labels from any public source. The closest available cohort (Khan 2025, n=162) measures cytokines paired with irAE outcomes; we use it for cross-validation. UK Biobank Fields 30710/41270/30900 would close the remaining gap but require institutional access."

## Re-running the download

```bash
python3 scripts/khan_jitc_2025_download.py
```

The script:
1. Fetches the 3 small xlsx files via curl (Zenodo blocks urllib's default UA)
2. Pivots them into 4 CSVs in this directory
3. Skips downloads that already exist locally
4. Skips the 28.7 GB CyTOF .fcs zip — that's raw mass cytometry, not relevant for tabular ML

## Citation

If you use this data, cite both the paper and the Zenodo deposit:

> Khan S, Malladi VS, von Itzstein MS, ..., Gerber DE. Innate and adaptive immune features associated with immune-related adverse events. J Immunother Cancer 2025;13(9):e012414. doi:10.1136/jitc-2025-012414

> Khan S, et al. *Dataset for: Innate and adaptive immune features associated with immune-related adverse events.* Zenodo 2025. doi:10.5281/zenodo.17943391
