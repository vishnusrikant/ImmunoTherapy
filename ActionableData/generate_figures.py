"""Generate the figure set that accompanies ActionableData/README.md.

Run from ActionableData/:
    ~/.venvs/immuno-plots/bin/python generate_figures.py
"""

from pathlib import Path
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["savefig.dpi"] = 140

ROOT = Path(__file__).parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

SEVERITY_ORDER = ["Mild", "Medium", "Severe"]
SEVERITY_PAL = {"Mild": "#4C9F70", "Medium": "#E0A030", "Severe": "#C0392B"}


def save(fig, name):
    out = FIG / name
    fig.savefig(out)
    plt.close(fig)
    print(f"  wrote {out.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# FAERS
# ---------------------------------------------------------------------------
print("Loading FAERS...")
ci = pd.read_csv(ROOT / "faers" / "checkpoint_inhibitor_adverse_events_2024_2025.csv", low_memory=False)
ct = pd.read_csv(ROOT / "faers" / "cart_therapy_adverse_events_2024_2025.csv", low_memory=False)
faers = pd.concat([ci, ct], ignore_index=True)
print(f"  combined: {len(faers):,} rows / {faers['caseid'].nunique():,} unique reports")

# Report-level view (one row per case) for patient-attribute plots
report_level = faers.drop_duplicates(subset=["caseid"]).copy()
report_level["age_years"] = np.where(
    report_level["patient_age_unit"] == "YR",
    report_level["patient_age"],
    np.nan,
)


# 1. Severity x drug class
fig, ax = plt.subplots(figsize=(8, 5))
sev = (
    report_level.groupby(["drug_class", "severity"]).size().unstack().reindex(columns=SEVERITY_ORDER, fill_value=0)
)
sev_pct = sev.div(sev.sum(axis=1), axis=0) * 100
sev_pct.plot(kind="barh", stacked=True, ax=ax, color=[SEVERITY_PAL[c] for c in SEVERITY_ORDER], width=0.6)
for cls_idx, cls in enumerate(sev.index):
    cum = 0
    for col in SEVERITY_ORDER:
        val = sev_pct.loc[cls, col]
        if val > 4:
            ax.text(cum + val / 2, cls_idx, f"{val:.0f}%", va="center", ha="center", color="white", fontsize=11, weight="bold")
        cum += val
ax.set_xlabel("Share of reports (%)")
ax.set_ylabel("")
ax.set_xlim(0, 100)
ax.set_title("FAERS — severity mix by therapy class\n(report-level, 2024–2025)")
ax.legend(title="Severity", loc="lower right")
save(fig, "faers_severity_by_drug_class.png")


# 2. Drug-level case counts
fig, ax = plt.subplots(figsize=(9, 6))
drug_counts = report_level["drug_name"].value_counts()
colors = ["#1f6f8b" if c == "Checkpoint Inhibitor" else "#a23b72" for c in
          [report_level.loc[report_level["drug_name"] == d, "drug_class"].iloc[0] for d in drug_counts.index]]
drug_counts.plot(kind="barh", ax=ax, color=colors)
ax.invert_yaxis()
ax.set_xlabel("Unique reports")
ax.set_title("FAERS — reports per drug (2024–2025)")
handles = [plt.Rectangle((0, 0), 1, 1, color="#1f6f8b"), plt.Rectangle((0, 0), 1, 1, color="#a23b72")]
ax.legend(handles, ["Checkpoint inhibitor", "CAR-T"], loc="lower right")
for i, v in enumerate(drug_counts.values):
    ax.text(v + drug_counts.max() * 0.01, i, f"{v:,}", va="center", fontsize=10)
save(fig, "faers_reports_per_drug.png")


# 3. Age distribution by severity
fig, ax = plt.subplots(figsize=(9, 5))
age_df = report_level.dropna(subset=["age_years", "severity"]).copy()
age_df = age_df[(age_df["age_years"] > 0) & (age_df["age_years"] < 110)]
for sev_lbl in SEVERITY_ORDER:
    sub = age_df.loc[age_df["severity"] == sev_lbl, "age_years"]
    if len(sub):
        ax.hist(sub, bins=np.arange(0, 105, 5), alpha=0.55, label=f"{sev_lbl} (n={len(sub):,})", color=SEVERITY_PAL[sev_lbl])
ax.axvline(60, color="black", linestyle="--", linewidth=1, alpha=0.6)
ax.text(61, ax.get_ylim()[1] * 0.92, "age 60\n(OR 1.49 for Grade 3+)", fontsize=9)
ax.set_xlabel("Patient age (years)")
ax.set_ylabel("Reports")
ax.set_title("FAERS — patient age distribution, by severity")
ax.legend(title="Severity")
save(fig, "faers_age_by_severity.png")


# 4. Sex distribution by severity
fig, ax = plt.subplots(figsize=(7, 5))
sex_df = report_level[report_level["patient_sex"].isin(["M", "F"])]
sex_tab = sex_df.groupby(["patient_sex", "severity"]).size().unstack().reindex(columns=SEVERITY_ORDER, fill_value=0)
sex_pct = sex_tab.div(sex_tab.sum(axis=1), axis=0) * 100
sex_pct.plot(kind="bar", stacked=True, ax=ax, color=[SEVERITY_PAL[c] for c in SEVERITY_ORDER], width=0.55)
ax.set_xticklabels(["Female", "Male"], rotation=0)
ax.set_xlabel("")
ax.set_ylabel("Share of reports (%)")
ax.set_title("FAERS — severity mix by patient sex")
ax.legend(title="Severity", loc="lower right")
ax.set_ylim(0, 100)
save(fig, "faers_severity_by_sex.png")


# 5. Top 12 reactions
fig, ax = plt.subplots(figsize=(9, 6))
top_rx = faers["reaction"].value_counts().head(12)
top_rx[::-1].plot(kind="barh", ax=ax, color="#34495e")
ax.set_xlabel("Mentions across all reports")
ax.set_title("FAERS — top 12 reported reactions")
for i, v in enumerate(top_rx[::-1].values):
    ax.text(v + top_rx.max() * 0.01, i, f"{v:,}", va="center", fontsize=10)
save(fig, "faers_top_reactions.png")


# 6. Top 10 indications (cancer types being treated)
fig, ax = plt.subplots(figsize=(9, 6))
indic = (
    report_level["indication"].dropna().str.strip().replace("", np.nan).dropna()
    .value_counts().head(10)
)
indic[::-1].plot(kind="barh", ax=ax, color="#16a085")
ax.set_xlabel("Reports")
ax.set_title("FAERS — top 10 cancer indications")
for i, v in enumerate(indic[::-1].values):
    ax.text(v + indic.max() * 0.01, i, f"{v:,}", va="center", fontsize=10)
save(fig, "faers_top_indications.png")


# 7. Seriousness flags co-occurrence
fig, ax = plt.subplots(figsize=(8, 5))
flags = ["seriousness_death", "seriousness_life_threatening", "seriousness_disabling", "seriousness_hospitalization"]
flag_labels = ["Death", "Life-threatening", "Disabling", "Hospitalization"]
counts = [int(report_level[f].fillna(0).astype(int).sum()) for f in flags]
totals = pd.Series(counts, index=flag_labels)
totals.sort_values().plot(kind="barh", ax=ax, color=["#7f8c8d", "#e67e22", "#c0392b", "#2980b9"])
for i, v in enumerate(totals.sort_values().values):
    ax.text(v + max(counts) * 0.01, i, f"{v:,}", va="center", fontsize=11)
ax.set_xlabel("Reports flagged")
ax.set_title("FAERS — seriousness flags driving the severity label")
save(fig, "faers_seriousness_flags.png")


# 8. Geography (top 10 reporting countries)
fig, ax = plt.subplots(figsize=(8, 5))
geo = report_level["country"].dropna().value_counts().head(10)
geo[::-1].plot(kind="barh", ax=ax, color="#8e44ad")
ax.set_xlabel("Reports")
ax.set_title("FAERS — top 10 reporting countries")
save(fig, "faers_top_countries.png")


# ---------------------------------------------------------------------------
# Khan JITC 2025
# ---------------------------------------------------------------------------
print("Loading Khan JITC 2025...")
khan = pd.read_csv(ROOT / "khan_jitc_2025" / "khan_patients_consolidated.csv")
print(f"  patients: {len(khan)}")

# 1. Cohort overview — drug class, gender, irAE occurrence, irAE grade
fig, axes = plt.subplots(2, 2, figsize=(11, 8))

drug_simple = khan["ici_drug"].fillna("Unknown").str.replace("+", " + ", regex=False)
drug_top = drug_simple.value_counts().head(6)
axes[0, 0].barh(drug_top.index[::-1], drug_top.values[::-1], color="#1f6f8b")
axes[0, 0].set_title("ICI drug regimen")
axes[0, 0].set_xlabel("Patients")

gender = khan["gender"].fillna("Unknown").value_counts()
axes[0, 1].pie(gender.values, labels=gender.index, autopct="%1.0f%%", colors=["#5dade2", "#f1948a", "#bdc3c7"], startangle=90)
axes[0, 1].set_title("Sex")

irae = khan["iraE_occurrence"].fillna("Unknown").value_counts()
axes[1, 0].bar(irae.index, irae.values, color=["#c0392b", "#27ae60", "#bdc3c7"][:len(irae)])
axes[1, 0].set_title("irAE occurrence (label)")
axes[1, 0].set_ylabel("Patients")
for i, v in enumerate(irae.values):
    axes[1, 0].text(i, v + 2, f"{v}", ha="center", fontsize=11)

grade = khan["highest_grade_iraE"].fillna(0).astype(int).value_counts().sort_index()
axes[1, 1].bar(grade.index.astype(str), grade.values, color=["#7fb3d5", "#f7dc6f", "#e59866", "#cd6155"][:len(grade)])
axes[1, 1].set_title("Highest CTCAE grade")
axes[1, 1].set_xlabel("Grade")
axes[1, 1].set_ylabel("Patients")
for i, v in enumerate(grade.values):
    axes[1, 1].text(i, v + 1, f"{v}", ha="center", fontsize=11)

fig.suptitle("Khan JITC 2025 — cohort overview (n=162)", fontsize=15, y=1.02)
fig.tight_layout()
save(fig, "khan_cohort_overview.png")


# 2. Cancer types
fig, ax = plt.subplots(figsize=(9, 6))
cancer = khan["cancer_type"].fillna("Unknown").value_counts().head(10)
cancer[::-1].plot(kind="barh", ax=ax, color="#16a085")
ax.set_xlabel("Patients")
ax.set_title("Khan JITC 2025 — top 10 cancer types")
for i, v in enumerate(cancer[::-1].values):
    ax.text(v + 0.3, i, f"{v}", va="center", fontsize=10)
save(fig, "khan_cancer_types.png")


# 3. Assay coverage matrix
fig, ax = plt.subplots(figsize=(8, 4))
assays = ["assay_scrnaseq", "assay_cytof", "assay_cytokine", "assay_ana"]
assay_labels = ["scRNA-seq", "CyTOF", "40-cytokine panel", "ANA titer"]
covered = [int((khan[a].fillna("").astype(str).str.upper() == "X").sum()) for a in assays]
ax.barh(assay_labels[::-1], covered[::-1], color="#5d6d7e")
ax.set_xlabel("Patients with data")
ax.set_xlim(0, 170)
ax.set_title("Khan JITC 2025 — assay coverage")
for i, v in enumerate(covered[::-1]):
    ax.text(v + 2, i, f"{v}/{len(khan)}", va="center", fontsize=11)
save(fig, "khan_assay_coverage.png")


# 4. IL-6 baseline by irAE status (the headline cytokine result)
fig, ax = plt.subplots(figsize=(8, 5))
il6_col = "IL-6"
khan_il6 = khan[[il6_col, "iraE_occurrence"]].copy()
khan_il6[il6_col] = pd.to_numeric(khan_il6[il6_col].astype(str).str.replace("*", "", regex=False).replace("OOR <", np.nan), errors="coerce")
khan_il6 = khan_il6.dropna(subset=[il6_col, "iraE_occurrence"])
khan_il6 = khan_il6[khan_il6["iraE_occurrence"].isin(["Grade 0-1", "Grade 2+"])]
order = ["Grade 0-1", "Grade 2+"]
sns.boxplot(data=khan_il6, x="iraE_occurrence", y=il6_col, order=order, ax=ax,
            palette={"Grade 0-1": "#27ae60", "Grade 2+": "#c0392b"}, width=0.45, fliersize=3)
sns.stripplot(data=khan_il6, x="iraE_occurrence", y=il6_col, order=order, ax=ax, color="black", alpha=0.35, size=3, jitter=0.2)
ax.set_yscale("log")
ax.set_xlabel("")
ax.set_ylabel("IL-6 baseline (pg/mL, log scale)")
n0 = (khan_il6["iraE_occurrence"] == "Grade 0-1").sum()
n2 = (khan_il6["iraE_occurrence"] == "Grade 2+").sum()
ax.set_xticklabels([f"Grade 0–1\nn={n0}", f"Grade 2+\nn={n2}"])
ax.set_title("Khan JITC 2025 — baseline IL-6 by irAE outcome")
save(fig, "khan_il6_by_irae.png")


# 5. Cytokine panel heatmap (median per cytokine x irAE group)
panel_cols = [c for c in khan.columns if c not in
              {"patient_id", "gender", "ethnicity", "race", "cancer_type", "ici_drug",
               "iraE_organ_affected", "highest_grade_iraE", "iraE_occurrence",
               "assay_scrnaseq", "assay_cytof", "assay_cytokine", "assay_ana", "ana_titer_baseline"}]


def to_num(s):
    return pd.to_numeric(s.astype(str).str.replace("*", "", regex=False).replace({"OOR <": np.nan, "OOR >": np.nan}), errors="coerce")


numeric = khan[panel_cols].apply(to_num)
numeric["iraE_occurrence"] = khan["iraE_occurrence"]
numeric = numeric.dropna(subset=["iraE_occurrence"])
numeric = numeric[numeric["iraE_occurrence"].isin(["Grade 0-1", "Grade 2+"])]
medians = numeric.groupby("iraE_occurrence").median().T
medians = medians.dropna(how="any")
ratio = np.log2(medians["Grade 2+"] / medians["Grade 0-1"]).sort_values()

fig, ax = plt.subplots(figsize=(7, 12))
colors = ["#c0392b" if v > 0 else "#1f6f8b" for v in ratio.values]
ax.barh(range(len(ratio)), ratio.values, color=colors)
ax.set_yticks(range(len(ratio)))
ax.set_yticklabels(ratio.index, fontsize=8)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("log2(median Grade 2+ / median Grade 0–1)")
ax.set_title("Khan — baseline cytokine differential\nby irAE outcome (40-marker panel)")
save(fig, "khan_cytokine_log2_diff.png")


print("\nDone.")
