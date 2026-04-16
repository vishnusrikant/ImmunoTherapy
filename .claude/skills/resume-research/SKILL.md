---
name: resume-research
description: Use when resuming work on the ImmunoTherapy side-effect severity project. Loads full context (datasets, research, prior decisions), verifies current state, and suggests next steps.
---

# Resume ImmunoTherapy Research

Re-establishes full context for the InspiritAI ImmunoTherapy project after a break.

## When This Skill Applies

- User says "let's continue the ImmunoTherapy project"
- User asks about next steps, current state, or where we left off
- User wants to pick up work on the severity prediction model
- User asks a question that assumes project context (e.g., "what did we decide about CAR-T?")

## What to Do (in order)

### Step 1: Load context

Read these files, in this order:
1. `CLAUDE.md` — project overview, scope, standards, conventions
2. `README.md` — TLDR and dataset summary
3. `docs/immunotherapy_side_effects_research.md` — 8-section research doc
4. `datasets/README.md` — dataset index and field descriptions
5. `datasets/immport/README.md` — ImmPort download details
6. `datasets/cbioportal/README.md` — cBioPortal consolidated patient table
7. `datasets/reference/predictive_features.csv` — 19 validated features
8. `datasets/reference/ctcae_severity_grades.csv` — severity mapping

### Step 2: Check current state

Run these quick checks:
```bash
# Recent commits — what's been done?
git log --oneline -10

# Uncommitted work?
git status

# Dataset row counts
wc -l datasets/faers/*.csv datasets/immport/SDY*/SDY*_patients_consolidated.csv datasets/cbioportal/all_patients_consolidated.csv
```

### Step 3: Confirm with the user

Summarize in ≤5 bullets:
- What project this is (immunotherapy severity classifier)
- What data we have (FAERS 124,982 rows + ImmPort 86 patients + cBioPortal 1,218 patients)
- Last meaningful progress (latest commits)
- What phase we're in (data collection done? model built?)
- Propose 2-3 next steps with short rationale

**Then pause for user direction.** Do not assume what they want next.

## Common Next-Step Patterns

| Current state | Likely next step |
|---------------|------------------|
| Data collected, no model yet | Invoke `build-model` skill |
| Model trained, no writeup | Generate model card / results document |
| User wants more data | Invoke `expand-data` skill |
| User wants a Colab notebook | Build notebook that loads FAERS + trains baseline |
| User wants slides / presentation | Summarize key findings for InspiritAI mentors |

## Do Not

- Do not rebuild datasets unless the user asks — the FAERS pull is expensive
- Do not re-fetch ImmPort data — credentials are not stored in the repo
- Do not re-explore GEO or irAExplorer — already evaluated and rejected (see `expand-data` skill for rationale)
- Do not introduce synthetic data — the project standard is real data only
- Do not replace the user's original README feature list — extend around it

## Key Facts to Remember

- **Severity mapping**: Mild = CTCAE 1-2, Medium = CTCAE 3, Severe = CTCAE 4-5
- **FAERS severity derivation**: Severe = death/life-threatening/disabling, Medium = hospitalization-only, Mild = everything else
- **Primary ImmPort study**: SDY1733 — 56 HCC patients, 10 on anti-PD-1 (5 Nivolumab + 5 Camrelizumab)
- **Prior art**: XGBoost AUC 0.99 on ePRO data (BMC Med Inform 2021); Logistic Regression AUC 0.83 for ICANS (Bone Marrow Transplant 2025)
- **Validated strong features**: Age ≥60 (OR 1.49), autoimmune disease (OR 2.09), combination therapy (70→90% irAE), CAR-T product type
- **Audience**: InspiritAI program — favor interpretable models, cite sources, avoid jargon without glossary
