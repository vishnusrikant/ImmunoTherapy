#!/usr/bin/env python3
"""Download + parse FAERS quarterly ASCII dumps, filter to immunotherapy drugs.

Source: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
URL pattern: https://fis.fda.gov/content/Exports/faers_ascii_{yyyy}q{n}.zip

Output schema matches datasets/faers/{checkpoint|cart}_adverse_events.csv so
rows can be merged with the existing openFDA-pulled data (de-duped by primaryid).
"""

import csv
import os
import sys
import urllib.request
import zipfile
from collections import defaultdict
from io import TextIOWrapper

# --- Configuration ---
QUARTERS = [
    ('2024', '1'), ('2024', '2'), ('2024', '3'), ('2024', '4'),
    ('2025', '1'), ('2025', '2'), ('2025', '3'), ('2025', '4'),
]
WORK_DIR = '/tmp/faers_quarterly'
OUT_DIR = '/home/vishnusrikant/ImmunoTherapy/datasets/faers_quarterly'

# Drug name substrings to match (case-insensitive) against DRUG.drugname or DRUG.prod_ai.
# Each tuple: (canonical_name, drug_class, targets_to_match)
DRUGS = [
    # Checkpoint inhibitors — existing 5
    ('Pembrolizumab', 'Checkpoint Inhibitor', ['pembrolizumab', 'keytruda', 'mk-3475', 'mk3475']),
    ('Nivolumab',     'Checkpoint Inhibitor', ['nivolumab', 'opdivo', 'bms-936558']),
    ('Ipilimumab',    'Checkpoint Inhibitor', ['ipilimumab', 'yervoy']),
    ('Atezolizumab',  'Checkpoint Inhibitor', ['atezolizumab', 'tecentriq', 'mpdl3280a']),
    ('Durvalumab',    'Checkpoint Inhibitor', ['durvalumab', 'imfinzi']),
    # Newer checkpoint inhibitors — added in this pull
    ('Cemiplimab',    'Checkpoint Inhibitor', ['cemiplimab', 'libtayo']),
    ('Dostarlimab',   'Checkpoint Inhibitor', ['dostarlimab', 'jemperli']),
    ('Relatlimab',    'Checkpoint Inhibitor', ['relatlimab', 'opdualag']),
    ('Tremelimumab',  'Checkpoint Inhibitor', ['tremelimumab', 'imjudo']),
    # CAR-T — existing 6
    ('Tisagenlecleucel',       'CAR-T', ['tisagenlecleucel', 'kymriah']),
    ('Axicabtagene ciloleucel','CAR-T', ['axicabtagene', 'yescarta']),
    ('Brexucabtagene autoleucel','CAR-T', ['brexucabtagene', 'tecartus']),
    ('Lisocabtagene maraleucel','CAR-T', ['lisocabtagene', 'breyanzi']),
    ('Idecabtagene vicleucel', 'CAR-T', ['idecabtagene', 'abecma']),
    ('Ciltacabtagene autoleucel','CAR-T', ['ciltacabtagene', 'carvykti']),
]

# Outcome codes → severity. Serious flags in the existing file are:
# seriousness_death / _hospitalization / _life_threatening / _disabling
OUTC_TO_FLAG = {
    'DE': 'seriousness_death',
    'LT': 'seriousness_life_threatening',
    'HO': 'seriousness_hospitalization',
    'DS': 'seriousness_disabling',
}


def drug_match(drugname, prod_ai):
    """Return (canonical_name, drug_class) if drug matches any immunotherapy; else (None, None)."""
    hay = f'{drugname} {prod_ai}'.lower()
    for canon, cls, keywords in DRUGS:
        for kw in keywords:
            if kw in hay:
                return canon, cls
    return None, None


def download_quarter(year, q):
    """Download the quarterly zip if not already present."""
    fname = f'faers_ascii_{year}q{q}.zip'
    path = os.path.join(WORK_DIR, fname)
    if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
        print(f'  already downloaded: {fname} ({os.path.getsize(path)//1024//1024} MB)')
        return path
    url = f'https://fis.fda.gov/content/Exports/{fname}'
    print(f'  downloading {url}')
    urllib.request.urlretrieve(url, path)
    print(f'    {os.path.getsize(path)//1024//1024} MB')
    return path


def open_quarter_member(zf, suffix, year, q):
    """Open an ASCII member file by type suffix (DEMO/DRUG/REAC/OUTC)."""
    yy = year[-2:]
    name = f'ASCII/{suffix}{yy}Q{q}.txt'
    # Some older quarters used lowercase / different casing
    try:
        return TextIOWrapper(zf.open(name), encoding='latin-1', errors='replace')
    except KeyError:
        for n in zf.namelist():
            if n.upper().endswith(f'{suffix}{yy}Q{q}.TXT'):
                return TextIOWrapper(zf.open(n), encoding='latin-1', errors='replace')
        raise


def process_quarter(path, year, q):
    """Parse one quarterly zip. Returns list of dict rows in output schema."""
    print(f'  parsing {year}Q{q}')
    rows_out = []

    with zipfile.ZipFile(path) as zf:
        # 1. DRUG — filter to immunotherapy drugs, primary/secondary suspect only
        matched_primaryids = {}  # primaryid -> (canonical_name, drug_class)
        with open_quarter_member(zf, 'DRUG', year, q) as f:
            reader = csv.DictReader(f, delimiter='$')
            for row in reader:
                role = (row.get('role_cod') or '').upper()
                if role not in ('PS', 'SS'):
                    continue
                canon, cls = drug_match(row.get('drugname') or '', row.get('prod_ai') or '')
                if canon:
                    pid = row.get('primaryid')
                    # If a report has multiple immunotherapy drugs, keep the first match
                    if pid and pid not in matched_primaryids:
                        matched_primaryids[pid] = (canon, cls)
        print(f'    matched {len(matched_primaryids)} reports with immunotherapy drugs')

        if not matched_primaryids:
            return []

        # 2. DEMO — patient demographics for matched reports
        demo = {}
        with open_quarter_member(zf, 'DEMO', year, q) as f:
            reader = csv.DictReader(f, delimiter='$')
            for row in reader:
                pid = row.get('primaryid')
                if pid in matched_primaryids:
                    demo[pid] = row

        # 3. REAC — reactions (may be multiple per report)
        reac = defaultdict(list)
        with open_quarter_member(zf, 'REAC', year, q) as f:
            reader = csv.DictReader(f, delimiter='$')
            for row in reader:
                pid = row.get('primaryid')
                if pid in matched_primaryids:
                    pt = row.get('pt')
                    if pt:
                        reac[pid].append(pt)

        # 4. OUTC — outcomes (may be multiple per report)
        outc = defaultdict(set)
        with open_quarter_member(zf, 'OUTC', year, q) as f:
            reader = csv.DictReader(f, delimiter='$')
            for row in reader:
                pid = row.get('primaryid')
                if pid in matched_primaryids:
                    c = row.get('outc_cod')
                    if c:
                        outc[pid].add(c)

        # 5. INDI — indications (cancer type the drug was given for); optional
        indi = {}
        try:
            with open_quarter_member(zf, 'INDI', year, q) as f:
                reader = csv.DictReader(f, delimiter='$')
                for row in reader:
                    pid = row.get('primaryid')
                    if pid in matched_primaryids and pid not in indi:
                        ind = row.get('indi_pt')
                        if ind:
                            indi[pid] = ind
        except KeyError:
            pass

    # Build output rows: one row per (report × reaction) to match the existing schema
    for pid, (canon, cls) in matched_primaryids.items():
        d = demo.get(pid, {})
        reactions = reac.get(pid, [])
        if not reactions:
            reactions = ['']  # keep the report even if no reaction (rare)
        o = outc.get(pid, set())
        ind = indi.get(pid, '')

        # Age conversion: FAERS uses age_cod YR/MON/WK/DY/HR/DEC
        age = d.get('age', '') or ''
        age_cod = d.get('age_cod', '') or ''
        # Weight
        wt = d.get('wt', '') or ''
        wt_cod = (d.get('wt_cod', '') or '').upper()
        wt_kg = ''
        if wt:
            try:
                v = float(wt)
                wt_kg = str(v if wt_cod in ('KG', 'KGS', '') else v * 0.453592)  # LBS→KG
            except ValueError:
                pass

        country = d.get('occr_country') or d.get('reporter_country') or ''
        rept_dt = d.get('fda_dt') or d.get('init_fda_dt') or ''

        serious_flag = 'Serious' if o else 'Non-Serious'

        for rx in reactions:
            rows_out.append({
                'primaryid': pid,
                'caseid': d.get('caseid', ''),
                'drug_name': canon,
                'drug_class': cls,
                'patient_age': age,
                'patient_age_unit': age_cod,
                'patient_sex': (d.get('sex') or '').strip(),
                'patient_weight_kg': wt_kg,
                'indication': ind,
                'reaction': rx,
                'reaction_outcome': '',  # not in quarterly format at row level
                'serious': serious_flag,
                'seriousness_death':           1 if 'DE' in o else 0,
                'seriousness_hospitalization': 1 if 'HO' in o else 0,
                'seriousness_life_threatening':1 if 'LT' in o else 0,
                'seriousness_disabling':       1 if 'DS' in o else 0,
                'report_date': rept_dt,
                'country': country,
                'source_year_quarter': f'{year}Q{q}',
            })

    return rows_out


def derive_severity(r):
    if r['seriousness_death'] or r['seriousness_life_threatening'] or r['seriousness_disabling']:
        return 'Severe'
    if r['seriousness_hospitalization']:
        return 'Medium'
    return 'Mild'


def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    all_rows = []
    for year, q in QUARTERS:
        print(f'\n=== {year} Q{q} ===')
        try:
            path = download_quarter(year, q)
            rows = process_quarter(path, year, q)
            all_rows.extend(rows)
            print(f'  + {len(rows)} rows (running total: {len(all_rows)})')
        except Exception as e:
            print(f'  FAILED {year}Q{q}: {e}')

    if not all_rows:
        print('No rows collected.')
        return

    # Split into checkpoint vs CAR-T
    ci = [r for r in all_rows if r['drug_class'] == 'Checkpoint Inhibitor']
    ct = [r for r in all_rows if r['drug_class'] == 'CAR-T']

    # Add derived severity label for convenience (existing files don't have this)
    fieldnames = list(all_rows[0].keys()) + ['severity']

    def write_split(rows, path):
        with open(path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                r['severity'] = derive_severity(r)
                w.writerow(r)

    ci_path = os.path.join(OUT_DIR, 'checkpoint_inhibitor_adverse_events_2024_2025.csv')
    ct_path = os.path.join(OUT_DIR, 'cart_therapy_adverse_events_2024_2025.csv')
    write_split(ci, ci_path)
    write_split(ct, ct_path)

    print(f'\n=== Summary ===')
    print(f'Checkpoint inhibitor rows: {len(ci):>7}  ({len(set(r["primaryid"] for r in ci))} unique reports)')
    print(f'CAR-T rows:                {len(ct):>7}  ({len(set(r["primaryid"] for r in ct))} unique reports)')
    print(f'Wrote {ci_path}')
    print(f'Wrote {ct_path}')

    # Per-drug + per-severity
    from collections import Counter
    print('\nReports per drug:')
    for cls, rows in [('Checkpoint', ci), ('CAR-T', ct)]:
        c = Counter(r['drug_name'] for r in rows)
        sev = Counter(r['severity'] for r in rows)
        print(f'  {cls}: {dict(c.most_common())}')
        print(f'  {cls} severity: {dict(sev)}')


if __name__ == '__main__':
    main()
