# ImmunoTherapy — Predicting Side Effect Severity with AI

## TLDR

Using AI to predict the **severity of immunotherapy side effects** (Mild / Medium / Severe) for cancer patients, based on patient bio data. Covers both **PD-1/PD-L1 checkpoint inhibitors** and **CAR-T cell therapy**.

### The Problem

Immunotherapy has revolutionized cancer treatment, but side effects (immune-related adverse events) affect **70-90% of checkpoint inhibitor patients** and **50-93% of CAR-T recipients**. Severity ranges from mild rash to life-threatening organ failure. Predicting severity before treatment could help doctors prepare and personalize care.

### The Approach

Build a **classification model** that takes a patient's profile as input and predicts side effect severity:

| Input (Patient Features) | Output (Prediction) |
|--------------------------|---------------------|
| Cancer type | **Mild** — Grade 1-2, outpatient management |
| Age, Gender, BMI | **Medium** — Grade 3, hospitalization needed |
| Previous autoimmune conditions | **Severe** — Grade 4-5, life-threatening or fatal |
| Family history of autoimmunity | |
| Inflammatory markers (NLR, CRP, IL-6) | |
| Prior / simultaneous treatments | |

### Key Findings from Research

| Feature | Impact on Severity |
|---------|-------------------|
| **Age >= 60** | 1.49x higher odds of severe side effects |
| **Pre-existing autoimmune disease** | 2.09x higher odds of severe side effects |
| **Combination therapy (PD-1 + CTLA-4)** | Side effect rates jump from ~70% to ~90% |
| **CAR-T product type** | Neurotoxicity varies: Yescarta 33% vs Breyanzi 16% |
| **Female sex** | Higher overall side effect incidence |

### Two Therapy Types

| | Checkpoint Inhibitors | CAR-T Therapy |
|---|---|---|
| **How it works** | Blocks PD-1/CTLA-4 to "release brakes" on immune system | Patient's T-cells engineered to target cancer |
| **Key drugs** | Keytruda, Opdivo, Yervoy, Tecentriq | Yescarta, Kymriah, Breyanzi, Abecma |
| **Main side effects** | Organ inflammation (skin, gut, liver, lungs, thyroid) | Cytokine Release Syndrome, Neurotoxicity |
| **Side effect rate** | 70-90% (any grade) | 50-93% (CRS) |

---

## Datasets

Real patient adverse event data from the FDA FAERS database + reference tables.

```
datasets/
├── faers/
│   ├── checkpoint_inhibitor_adverse_events.csv   (1,204 rows — 5 drugs)
│   └── cart_therapy_adverse_events.csv           (2,094 rows — 5 CAR-T products)
└── reference/
    ├── ctcae_severity_grades.csv        (CTCAE Grade 1-5 → Mild/Medium/Severe mapping)
    ├── immunotherapy_drugs.csv          (11 drugs — names, targets, approvals)
    ├── common_iraes_by_therapy.csv      (21 adverse events with incidence rates)
    └── predictive_features.csv          (19 validated predictive patient features)
```

See [`datasets/README.md`](datasets/README.md) for field descriptions, data quality stats, and how to expand the dataset.

### Additional Datasets (require free registration)

| Dataset | What It Has | URL |
|---------|-------------|-----|
| **ImmPort** | Patient-level trial data with lab values & medical history | [immport.org](https://www.immport.org/shared/) |
| **TCGA / cBioPortal** | Cancer genomics + clinical data (10,000+ patients) | [cbioportal.org](https://www.cbioportal.org/) |
| **GEO (GSE91061)** | Gene expression for melanoma patients on anti-PD-1 | [ncbi.nlm.nih.gov/geo](https://www.ncbi.nlm.nih.gov/geo/) |
| **ClinicalTrials.gov** | Completed trial results with adverse event rates | [clinicaltrials.gov](https://clinicaltrials.gov/) |
| **FDA FAERS (full)** | Millions of adverse event reports (quarterly dumps) | [fda.gov/faers](https://www.fda.gov/drugs/fdas-adverse-event-reporting-system-faers) |

---

## Research

Full analysis in [`docs/immunotherapy_side_effects_research.md`](docs/immunotherapy_side_effects_research.md) covering:

1. What is cancer immunotherapy (checkpoint inhibitors vs CAR-T)
2. Side effects — what happens and why (irAEs, CRS, ICANS)
3. Severity grading (CTCAE scale → Mild/Medium/Severe mapping)
4. What patient features predict severity (19 validated features)
5. Available public datasets (FAERS, ImmPort, TCGA, GEO, ClinicalTrials.gov)
6. Existing ML models and prior art (AUC up to 0.99)
7. Proposed model design (Random Forest + XGBoost)
8. Medical terms glossary

---

## Project Context

- **Program:** InspiritAI
- **Tools:** Python, Google Colab, scikit-learn, pandas, matplotlib
- **Data:** Real patient data from public datasets (FDA FAERS primary)
- **Model:** Classification — Mild / Medium / Severe side effect severity
