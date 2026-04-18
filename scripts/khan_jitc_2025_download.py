#!/usr/bin/env python3
"""Download Khan et al. JITC 2025 supplementary data — patient-level ICI cohort
with baseline + 6-8wk multiplex cytokine panel (40 markers incl. IL-6, IFN-y,
TNF-a, IL-10, IL-1b) PAIRED WITH irAE occurrence labels.

This is the only public dataset we found that combines patient-level baseline
labs/cytokines with binary irAE outcome flags. Closes the FAERS feature gap
on cytokines + irAE labels in a single cohort.

Paper: Khan S, Malladi VS, von Itzstein MS, ..., Gerber DE.
       "Innate and adaptive immune features associated with
        immune-related adverse events."
       J Immunother Cancer. 2025;13(9):e012414.
       DOI: 10.1136/jitc-2025-012414
       PMC: PMC12506470

Data:  Zenodo record 17943391, deposited 2025-12-15.
       DOI: 10.5281/zenodo.17943391
       License: CC BY 4.0

Files pulled (small xlsx; the 28.7 GB CyTOF .fcs zip is intentionally skipped):
  1. JITC metadata.xlsx        (21 KB, 162 patients - demographics + irAE labels)
  2. JITC cytokine Submit.xlsx (99 KB, 292 rows = 146 patients x BL + 6-8wks)
  3. JITC ANA Submit.xlsx      (16 KB, 181 rows of ANA autoantibody titers)

Output (in datasets/khan_jitc_2025/):
  - supplementary_metadata.xlsx
  - supplementary_cytokine.xlsx
  - supplementary_ana.xlsx
  - khan_metadata.csv             (162 patient records, one row per patient)
  - khan_cytokine_long.csv        (292 rows, one per patient x timepoint)
  - khan_ana_long.csv             (ANA titers in long format)
  - khan_patients_consolidated.csv (162 patients, baseline cytokines joined in)

irAE label conventions in the metadata file:
  - 'Highest grade of irAE': CTCAE grade 0/1/2/3 (no grade 4-5 in this cohort)
  - 'irAE occurrence':       'Grade 0-1' or 'Grade 2+' (the paper's primary label)
  - 'irAE based on organ affected': free-text organ list (e.g. 'Pneumonitis, hepatitis')

For severity-classifier compatibility (Mild/Medium/Severe per CTCAE Grade
1-2/3/4-5), our convention maps Khan's grades like this:
  Grade 0 -> no irAE (excluded from positive cases)
  Grade 1 -> Mild
  Grade 2 -> Mild   (CTCAE 2 maps to Mild in our project; see ctcae_severity_grades.csv)
  Grade 3 -> Medium
  Grade 4-5 -> Severe (none in this cohort)

Note: the column label in the source file is 'Highest grade  of irAE' (two
spaces). We rename to a single-space canonical form.
"""

import csv
import os
import subprocess

ZENODO_BASE = 'https://zenodo.org/api/records/17943391/files'
FILES = [
    ('JITC%20metadata.xlsx',         'supplementary_metadata.xlsx'),
    ('JITC%20cytokine%20Submit.xlsx', 'supplementary_cytokine.xlsx'),
    ('JITC%20ANA%20Submit.xlsx',     'supplementary_ana.xlsx'),
]

OUT_DIR = '/home/vishnusrikant/ImmunoTherapy/datasets/khan_jitc_2025'


def download_all():
    os.makedirs(OUT_DIR, exist_ok=True)
    for url_name, local_name in FILES:
        url = f'{ZENODO_BASE}/{url_name}/content'
        out = os.path.join(OUT_DIR, local_name)
        if os.path.exists(out):
            print(f'[skip] already downloaded: {out}')
            continue
        print(f'[download] {url}')
        # Zenodo rejects urllib's default UA; curl works cleanly.
        subprocess.run(
            ['curl', '-sSL', '--fail', '-o', out, url],
            check=True, timeout=120,
        )
        print(f'[saved]    {out} ({os.path.getsize(out):,} bytes)')


def write_metadata_csv(xlsx_path, csv_path):
    """One row per patient, 162 rows. Source xlsx has a junk first row."""
    import pandas as pd
    df = pd.read_excel(xlsx_path, header=1)
    df = df.rename(columns={
        'Highest grade  of irAE': 'highest_grade_iraE',
        'irAE based on organ affected': 'iraE_organ_affected',
        'irAE occurrence': 'iraE_occurrence',
        'NM ID': 'patient_id',
        'Cancer type': 'cancer_type',
        'ICI type': 'ici_drug',
        'Gender': 'gender',
        'Ethnicity': 'ethnicity',
        'Race': 'race',
        'ScRNA-seq': 'assay_scrnaseq',
        'CyTOF': 'assay_cytof',
        'Cytokine': 'assay_cytokine',
        'ANA': 'assay_ana',
    })
    df.to_csv(csv_path, index=False)
    print(f'[wrote] {csv_path} - {len(df)} rows x {len(df.columns)} cols')
    return df


def write_cytokine_long_csv(xlsx_path, csv_path):
    """One row per (patient x timepoint), 292 rows. Strip '(##)' assay codes
    from cytokine column names so they're readable: 'IL-6 (19)' -> 'IL-6'."""
    import pandas as pd
    df = pd.read_excel(xlsx_path)
    rename = {'NM ID': 'patient_id', 'Timepoint': 'timepoint'}
    for c in df.columns:
        if c not in rename and ' (' in c:
            rename[c] = c.split(' (', 1)[0].strip()
    df = df.rename(columns=rename)
    df.to_csv(csv_path, index=False)
    print(f'[wrote] {csv_path} - {len(df)} rows x {len(df.columns)} cols')
    return df


def write_ana_long_csv(xlsx_path, csv_path):
    """One row per (patient x timepoint), 181 rows."""
    import pandas as pd
    df = pd.read_excel(xlsx_path).rename(columns={
        'NM ID': 'patient_id',
        'Khan timepoint': 'timepoint',
        'Sample Value ANA': 'ana_titer',
    })
    df.to_csv(csv_path, index=False)
    print(f'[wrote] {csv_path} - {len(df)} rows x {len(df.columns)} cols')
    return df


def write_consolidated_csv(meta_df, cyto_df, ana_df, csv_path):
    """One row per patient with baseline cytokines + baseline ANA joined in.

    For modeling pre-treatment severity prediction, only the BL (baseline)
    timepoint is appropriate. Post-treatment values are confounded with
    treatment effects.
    """
    import pandas as pd
    cyto_bl = cyto_df[cyto_df['timepoint'] == 'BL'].drop(columns=['timepoint'])
    ana_bl = (
        ana_df[ana_df['timepoint'] == 'BL']
        .drop(columns=['timepoint'])
        .rename(columns={'ana_titer': 'ana_titer_baseline'})
    )
    out = meta_df.merge(cyto_bl, on='patient_id', how='left')
    out = out.merge(ana_bl, on='patient_id', how='left')
    out.to_csv(csv_path, index=False)
    print(f'[wrote] {csv_path} - {len(out)} rows x {len(out.columns)} cols')

    # quick sanity print
    bl_cyto_present = out.iloc[:, len(meta_df.columns):-1].notna().any(axis=1).sum()
    print(f'        {bl_cyto_present} patients have any baseline cytokine data')
    print(f'        {out["ana_titer_baseline"].notna().sum()} patients have baseline ANA')


def main():
    download_all()

    meta_csv = os.path.join(OUT_DIR, 'khan_metadata.csv')
    cyto_csv = os.path.join(OUT_DIR, 'khan_cytokine_long.csv')
    ana_csv = os.path.join(OUT_DIR, 'khan_ana_long.csv')
    consol_csv = os.path.join(OUT_DIR, 'khan_patients_consolidated.csv')

    meta_df = write_metadata_csv(
        os.path.join(OUT_DIR, 'supplementary_metadata.xlsx'), meta_csv,
    )
    cyto_df = write_cytokine_long_csv(
        os.path.join(OUT_DIR, 'supplementary_cytokine.xlsx'), cyto_csv,
    )
    ana_df = write_ana_long_csv(
        os.path.join(OUT_DIR, 'supplementary_ana.xlsx'), ana_csv,
    )
    write_consolidated_csv(meta_df, cyto_df, ana_df, consol_csv)

    print('\n[done] Khan et al. JITC 2025 cohort downloaded.')


if __name__ == '__main__':
    main()
