# Immunotherapy Side Effects — Research & Analysis

## Executive Summary

Cancer immunotherapy has revolutionized oncology, but immune-related adverse events (irAEs) affect **70-90% of patients** on checkpoint inhibitors and **50-93% of CAR-T recipients**. This research explores what determines the **severity** of these side effects, what patient features predict outcomes, and what public datasets are available to build an AI model that classifies side effect severity as **Mild, Medium, or Severe**.

---

## 1. What Is Cancer Immunotherapy?

Cancer immunotherapy works by harnessing the patient's own immune system to fight cancer, rather than directly killing cancer cells (like chemotherapy or radiation).

### Two Main Approaches

| Approach | How It Works | Key Drugs |
|----------|-------------|-----------|
| **Checkpoint Inhibitors** | Block proteins (PD-1, PD-L1, CTLA-4) that prevent T-cells from attacking cancer. "Releases the brakes" on the immune system. | Keytruda (pembrolizumab), Opdivo (nivolumab), Yervoy (ipilimumab), Tecentriq (atezolizumab), Imfinzi (durvalumab) |
| **CAR-T Cell Therapy** | Patient's T-cells are extracted, genetically engineered to target cancer markers (CD19, BCMA), multiplied, and re-infused. | Yescarta, Kymriah, Tecartus, Breyanzi, Abecma, Carvykti |

### The Trade-Off

By supercharging the immune system, immunotherapy can attack cancer effectively — but the activated immune system may also attack **healthy tissues**, causing immune-related adverse events (irAEs).

---

## 2. Side Effects: What Happens and Why

### Checkpoint Inhibitor Side Effects (irAEs)

When checkpoint inhibitors "release the brakes" on T-cells, those T-cells don't just attack cancer — they can attack any organ. The most common irAEs:

| Organ System | Adverse Event | Incidence (any grade) | Grade 3+ (severe) |
|-------------|---------------|----------------------|-------------------|
| **Skin** | Rash, itching, vitiligo | 30-40% | 1-3% |
| **GI** | Diarrhea, colitis | 10-20% (PD-1), 30-50% (CTLA-4) | 1-15% |
| **Endocrine** | Thyroiditis, adrenal insufficiency, hypophysitis | 5-20% | 0.5-5% |
| **Liver** | Hepatitis (elevated ALT/AST) | 5-10% | 1-5% |
| **Lungs** | Pneumonitis (inflammation) | 3-10% | 1-3% |
| **Heart** | Myocarditis | 0.5-1.5% | 0.5-1% |
| **Kidneys** | Nephritis | 1-5% | 0.5-2% |
| **Muscles/Joints** | Arthralgia, myositis | 5-15% | 1-2% |

**Key pattern:** CTLA-4 inhibitors (ipilimumab) cause **more frequent and more severe** irAEs than PD-1/PD-L1 inhibitors. Combination therapy (PD-1 + CTLA-4) has the **highest irAE rates** (~90%).

### CAR-T Side Effects

CAR-T has its own distinctive toxicity profile:

| Side Effect | What Happens | Incidence | Severity Range |
|------------|-------------|-----------|----------------|
| **Cytokine Release Syndrome (CRS)** | Massive immune activation releases cytokines (IL-6, IFN-γ, TNF-α) → fever, hypotension, organ damage | 50-93% | Mild fever → multi-organ failure |
| **ICANS (Neurotoxicity)** | Immune cells cross blood-brain barrier → confusion, tremors, seizures, cerebral edema | 15-69% | Mild confusion → coma |
| **Cytopenias** | Low blood cell counts (neutropenia, thrombocytopenia, anemia) — can be prolonged for months | 30-60% | Mild → life-threatening infections |
| **Infections** | Due to immune suppression and low blood counts | 20-40% | Mild → sepsis |

**Key pattern:** CRS typically starts **1-14 days** after CAR-T infusion. Severity varies dramatically by CAR-T product — ICANS rates: Yescarta 33% vs Kymriah 22% vs Breyanzi 16%.

---

## 3. Severity Grading: CTCAE Scale

The medical standard for grading adverse event severity is the **Common Terminology Criteria for Adverse Events (CTCAE) version 5.0**, which uses a 5-grade system:

| CTCAE Grade | Severity | Our Model Label | Description | Clinical Action |
|-------------|----------|-----------------|-------------|-----------------|
| **Grade 1** | Mild | **Mild** | Asymptomatic or mild symptoms; observation only | Continue immunotherapy; monitor |
| **Grade 2** | Moderate | **Mild** | Moderate symptoms; minimal intervention needed | Hold immunotherapy; oral steroids |
| **Grade 3** | Severe | **Medium** | Severe symptoms; hospitalization required | Discontinue; IV steroids; hospitalize |
| **Grade 4** | Life-threatening | **Severe** | Life-threatening; urgent intervention | Permanently stop; ICU; high-dose steroids |
| **Grade 5** | Death | **Severe** | Death related to adverse event | N/A |

### Mapping to Our 3-Class Model

For the AI classification model:
- **Mild** = CTCAE Grade 1-2 (outpatient management, continue or hold treatment)
- **Medium** = CTCAE Grade 3 (hospitalization, discontinue treatment)
- **Severe** = CTCAE Grade 4-5 (life-threatening or fatal)

---

## 4. What Patient Features Predict Severity?

Published research has identified these features as predictive of irAE severity:

### Strong Evidence (validated in multiple studies)

| Feature | Effect | Evidence |
|---------|--------|----------|
| **Age ≥ 60 years** | 1.49x higher odds of Grade 3+ irAEs | Frontiers in Immunology, 2025 (n=3,795) |
| **Pre-existing autoimmune disease** | 2.09x higher odds of Grade 3+ irAEs | Frontiers in Immunology, 2025 (n=3,795) |
| **Combination therapy (PD-1 + CTLA-4)** | irAE rates jump from ~70% to ~90% | ASCO Clinical Practice Guideline |
| **Cancer type** | irAE profiles vary significantly across cancers | npj Precision Oncology, 2021 (n=85.97M claims) |
| **CAR-T product type** | ICANS: Yescarta 33% > Kymriah 22% > Breyanzi 16% | ASH Blood, 2024 |
| **IL-6 level (day 3 post CAR-T)** | Early IL-6 peak predicts severe CRS and ICANS | Bone Marrow Transplantation, 2025 |

### Moderate Evidence

| Feature | Effect | Evidence |
|---------|--------|----------|
| **Female sex** | Higher irAE incidence overall | Multiple studies |
| **BMI** | Predictive of irAE severity | Multiple studies |
| **Baseline NLR** (neutrophil-to-lymphocyte ratio) | Higher NLR → worse irAEs | Frontiers in Immunology, 2025 |
| **Baseline CRP** (C-reactive protein) | Elevated CRP predicts severe irAEs | Multiple studies |
| **Pre-infusion D-dimer** | Part of ICANS prediction model (AUC = 0.83) | Bone Marrow Transplantation, 2025 |
| **Number of prior treatments** | More prior therapies → different irAE profile | Multiple studies |
| **Antibiotic use** | Associated with higher irAE incidence | Frontiers in Immunology, 2025 |
| **Cirrhosis / liver disease** | Independent risk factor for irAEs | Frontiers in Immunology, 2025 |

### Feature Mapping to Our Model Inputs

| Your README Feature | Mapped Clinical Feature | Available in FAERS? | Available in ImmPort/TCGA? |
|--------------------|-----------------------|--------------------|-----------------------------|
| Type of Cancer | Cancer type / indication | Partial (from drug indication) | Yes |
| Age | Patient onset age | Yes (91% coverage) | Yes |
| Gender | Patient sex | Yes | Yes |
| BMI | Derived from weight/height | Weight only (60%) | Varies by study |
| Previous Autoimmune Conditions | Pre-existing autoimmune disease | No | Yes (medical history) |
| Family History of Autoimmunity | Family autoimmune history | No | Varies |
| Health Markers | NLR, CRP, IL-6, LDH, D-dimer | No | Yes (lab results) |
| Prior Treatments | Concomitant medications, prior therapies | Partial | Yes |

---

## 5. Available Public Datasets

### Primary Dataset: FDA FAERS

| Aspect | Detail |
|--------|--------|
| **What** | Post-marketing adverse event reports submitted to FDA |
| **Size** | Millions of reports; we pulled **42,469 unique reports (124,982 adverse event rows)** |
| **Access** | Free — [open.fda.gov API](https://open.fda.gov/data/faers/) or [quarterly downloads](https://www.fda.gov/drugs/fdas-adverse-event-reporting-system-faers) |
| **Strengths** | Real patient data; large scale; demographics + adverse events + outcomes + cancer indication; easy API access |
| **Limitations** | No CTCAE grades (must derive severity from seriousness flags); no lab values; no autoimmune history; voluntary reporting (underreporting bias) |
| **Our data** | `datasets/faers/` — 62,106 checkpoint inhibitor rows (25,000 reports, 5 drugs) + 62,876 CAR-T rows (17,469 reports, 6 products). Severity split: 35% Mild / 30% Medium / 35% Severe |

### Supplementary Dataset: ImmPort

| Aspect | Detail |
|--------|--------|
| **What** | Patient-level clinical trial data from NIH/NIAID-funded studies |
| **Size** | 145+ clinical trials with individual-level data |
| **Access** | Free registration — [immport.org/shared](https://www.immport.org/shared/) |
| **Strengths** | Rich patient-level data: demographics, medical history, adverse events, lab results (flow cytometry, ELISA) |
| **Limitations** | Requires registration; data formats vary across studies; not all studies are immunotherapy-specific |

### Supplementary Dataset: TCGA / cBioPortal

| Aspect | Detail |
|--------|--------|
| **What** | Cancer genomics + clinical data across 33 cancer types |
| **Size** | 10,000+ patients |
| **Access** | Free — [cbioportal.org](https://www.cbioportal.org/) |
| **Strengths** | Cancer type, mutations (TMB), demographics, treatment, survival |
| **Limitations** | Limited adverse event data; focused on genomics rather than side effects |

### Supplementary Dataset: GEO (Gene Expression Omnibus)

| Aspect | Detail |
|--------|--------|
| **What** | Gene expression data from immunotherapy-treated patients |
| **Key dataset** | GSE91061 — melanoma patients on anti-PD-1 (responders vs non-responders) |
| **Access** | Free — [ncbi.nlm.nih.gov/geo](https://www.ncbi.nlm.nih.gov/geo/) |
| **Strengths** | Molecular-level features; well-curated; published studies |
| **Limitations** | Small sample sizes; requires bioinformatics skills; focused on response rather than side effects |

### Supplementary Dataset: ClinicalTrials.gov

| Aspect | Detail |
|--------|--------|
| **What** | Results from completed clinical trials including adverse event tables |
| **Access** | Free — [clinicaltrials.gov](https://clinicaltrials.gov/) |
| **Strengths** | Structured adverse event data by therapy; aggregate rates |
| **Limitations** | Aggregate data (not patient-level); manual extraction needed |

---

## 6. Existing ML Models (Prior Art)

| Study | Approach | Dataset | Performance |
|-------|----------|---------|-------------|
| **ePRO + ML for irAE prediction** (BMC Med Inform, 2021) | Extreme gradient boosting on patient-reported outcomes | 34 patients, 820 questionnaires | Accuracy 0.97, AUC 0.99 |
| **ICANS prediction model** (Bone Marrow Transplant, 2025) | Multivariate logistic regression using cytokine + clinical features | CD19 CAR-T patients | AUC 0.83 (any ICANS), AUC 0.80 (Grade 2-4) |
| **irAE severity predictors** (Frontiers in Immunology, 2025) | Multivariate logistic regression | 3,795 cancer patients | Age ≥60 OR=1.49, Autoimmune OR=2.09 |
| **90-day acute care prediction** (JCO CCI, 2022) | ML on structured EHR data | Routine clinical data | Robust interpretable predictions |
| **Pharmacovigilance toxicity** (Nature Comp Sci, 2024) | Population-scale modeling on FAERS | FAERS database | Predicted population toxicity profiles |

---

## 7. Proposed Model Design

### Classification Task

**Input:** Patient bio data (demographics, medical history, cancer type, treatment type, lab markers)
**Output:** Side effect severity prediction — **Mild** / **Medium** / **Severe**

### Feature Engineering from FAERS

Since FAERS doesn't include CTCAE grades, we derive severity labels:

```
Severe  = seriousness_death=1 OR seriousness_life_threatening=1 OR seriousness_disabling=1
Medium  = seriousness_hospitalization=1 AND NOT Severe
Mild    = everything else (Non-Serious OR Serious but recovered without hospitalization)
```

### Suggested Model Architectures (for InspiritAI)

| Model | Complexity | Why |
|-------|-----------|-----|
| **Logistic Regression** | Low | Interpretable baseline; good for understanding feature importance |
| **Random Forest** | Medium | Handles mixed feature types; feature importance built-in |
| **XGBoost** | Medium-High | Best published results for irAE prediction (AUC 0.99 in prior study) |
| **Neural Network (simple)** | High | If dataset is large enough; useful for learning non-linear patterns |

### Recommended Approach

1. Start with **FAERS data** (largest, easiest to access)
2. Engineer severity labels from seriousness flags
3. Train **Random Forest** as primary model (interpretable, good performance)
4. Use **XGBoost** as comparison model
5. If time allows, enrich with **ImmPort** data for lab values / medical history

---

## 8. Key Medical Terms Glossary

| Term | Definition |
|------|-----------|
| **irAE** | Immune-Related Adverse Event — side effect caused by immune system attacking healthy tissue |
| **CRS** | Cytokine Release Syndrome — massive immune activation after CAR-T infusion |
| **ICANS** | Immune Effector Cell-Associated Neurotoxicity Syndrome — brain toxicity after CAR-T |
| **CTCAE** | Common Terminology Criteria for Adverse Events — standard 5-grade severity scale |
| **PD-1/PD-L1** | Programmed Death receptor/ligand — checkpoint proteins that block T-cell activity |
| **CTLA-4** | Cytotoxic T-Lymphocyte Associated protein 4 — another checkpoint protein |
| **CAR-T** | Chimeric Antigen Receptor T-cell therapy — genetically engineered T-cells |
| **NLR** | Neutrophil-to-Lymphocyte Ratio — inflammatory marker from blood test |
| **CRP** | C-Reactive Protein — inflammatory marker; elevated in infections and irAEs |
| **IL-6** | Interleukin-6 — cytokine; key driver of CRS severity |
| **TMB** | Tumor Mutation Burden — number of mutations in a tumor; linked to immunotherapy response |
| **MedDRA** | Medical Dictionary for Regulatory Activities — standardized adverse event terminology |
| **FAERS** | FDA Adverse Event Reporting System — US post-marketing safety database |

---

## Sources

- [ASCO Guideline — Management of irAEs (2021 Update)](https://ascopubs.org/doi/10.1200/JCO.21.01440)
- [Frontiers in Immunology — irAEs of Checkpoint Inhibitors: A Review (2023)](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2023.1167975/full)
- [Frontiers in Immunology — Predictors of Severity and Onset Timing (2025)](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2025.1508512/full)
- [npj Precision Oncology — Real-World irAEs Across Cancer Types (2021)](https://www.nature.com/articles/s41698-021-00223-x)
- [Nature Reviews Clinical Oncology — Adverse Effects of ICIs (2019)](https://www.nature.com/articles/s41571-019-0218-0)
- [BMC Med Inform — ePRO + ML for irAE Prediction (2021)](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-021-01564-0)
- [Bone Marrow Transplantation — ICANS Risk Model in CD19 CAR-T (2025)](https://www.nature.com/articles/s41409-025-02679-y)
- [Nature Computational Science — Pharmacovigilance Toxicity Profiles (2024)](https://www.nature.com/articles/s43588-024-00748-8)
- [JCO CCI — Prediction of ICI Effectiveness and Toxicities (2023)](https://ascopubs.org/doi/10.1200/CCI.23.00207)
- [ASH Blood — CRS and ICANS Incidence Across CAR-T Products (2024)](https://ashpublications.org/blood/article/146/Supplement%201/8012/552391/)
- [FDA FAERS — openFDA API](https://open.fda.gov/data/faers/)
- [ImmPort — Shared Immunology Data](https://www.immport.org/shared/)
- [cBioPortal — Cancer Genomics](https://www.cbioportal.org/)
- [VigiAccess — WHO Global Adverse Event Database](https://www.vigiaccess.org/)

---

*Research conducted April 15, 2026 — ImmunoTherapy Side Effects AI Project (InspiritAI)*
