#!/usr/bin/env python3
"""Download cBioPortal clinical data for immunotherapy studies."""

import urllib.request
import json
import csv
import os
import time

BASE = 'https://www.cbioportal.org/api'
OUT_DIR = '/home/vishnusrikant/ImmunoTherapy/datasets/cbioportal'
os.makedirs(OUT_DIR, exist_ok=True)

STUDIES = [
    'mel_dfci_2019',                       # 144 melanoma — rich features
    'blca_iatlas_imvigor210_2017',         # 347 bladder atezolizumab
    'rcc_iatlas_immotion150_2018',         # 263 RCC atezolizumab
    'nsclc_pd1_msk_2018',                  # 240 NSCLC PD-1
    'mel_iatlas_liu_2019',                 # 122 melanoma
    'mel_iatlas_riaz_nivolumab_2017',      # 64  melanoma nivolumab
    'mel_ucla_2016',                       # 38  melanoma
]


def fetch(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)


def flatten_list_to_csv(data, path):
    if not data:
        return 0
    keys = []
    seen = set()
    for row in data:
        if not isinstance(row, dict):
            continue
        for k in row.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        w.writeheader()
        for row in data:
            if not isinstance(row, dict):
                continue
            clean = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in row.items()}
            w.writerow(clean)
    return len(data)


def pivot_clinical_to_wide(all_clinical_rows, id_key='patientId'):
    """Pivot long-form clinical data (one row per patient×attribute) to wide (one row per patient)."""
    by_id = {}
    for r in all_clinical_rows:
        pid = r.get(id_key)
        if not pid:
            continue
        if pid not in by_id:
            by_id[pid] = {id_key: pid}
        attr = r.get('clinicalAttributeId')
        val = r.get('value')
        if attr:
            by_id[pid][attr] = val
    return list(by_id.values())


def download_study(sid):
    print(f'\n=== {sid} ===')
    sdir = os.path.join(OUT_DIR, sid)
    os.makedirs(sdir, exist_ok=True)

    # 1. Study metadata
    meta = fetch(f'{BASE}/studies/{sid}')
    save_json(meta, os.path.join(sdir, f'{sid}_metadata.json'))
    print(f'  metadata: {meta.get("name", "?")[:60]}')

    # 2. Clinical attributes catalog
    attrs = fetch(f'{BASE}/studies/{sid}/clinical-attributes')
    flatten_list_to_csv(attrs, os.path.join(sdir, f'{sid}_clinical_attributes.csv'))
    print(f'  clinical attributes catalog: {len(attrs)}')

    # 3. Patients list
    patients = fetch(f'{BASE}/studies/{sid}/patients')
    flatten_list_to_csv(patients, os.path.join(sdir, f'{sid}_patients.csv'))
    print(f'  patients: {len(patients)}')

    # 4. Samples list
    samples = fetch(f'{BASE}/studies/{sid}/samples')
    flatten_list_to_csv(samples, os.path.join(sdir, f'{sid}_samples.csv'))
    print(f'  samples: {len(samples)}')

    # 5. Patient-level clinical data (bulk endpoint)
    try:
        p_clin = fetch(f'{BASE}/studies/{sid}/clinical-data?clinicalDataType=PATIENT')
        wide_p = pivot_clinical_to_wide(p_clin, id_key='patientId')
        flatten_list_to_csv(wide_p, os.path.join(sdir, f'{sid}_patient_clinical_data.csv'))
        print(f'  patient clinical data: {len(p_clin)} rows -> {len(wide_p)} patient rows')
    except Exception as e:
        print(f'  patient clinical data ERROR: {e}')

    # 6. Sample-level clinical data
    try:
        s_clin = fetch(f'{BASE}/studies/{sid}/clinical-data?clinicalDataType=SAMPLE')
        wide_s = pivot_clinical_to_wide(s_clin, id_key='sampleId')
        flatten_list_to_csv(wide_s, os.path.join(sdir, f'{sid}_sample_clinical_data.csv'))
        print(f'  sample clinical data: {len(s_clin)} rows -> {len(wide_s)} sample rows')
    except Exception as e:
        print(f'  sample clinical data ERROR: {e}')

    return {
        'study_id': sid,
        'patients': len(patients),
        'samples': len(samples),
        'clinical_attributes': len(attrs),
    }


all_summaries = []
for sid in STUDIES:
    try:
        all_summaries.append(download_study(sid))
        time.sleep(0.5)
    except Exception as e:
        print(f'FAILED {sid}: {e}')
        all_summaries.append({'study_id': sid, 'error': str(e)})

print('\n=== Summary ===')
for s in all_summaries:
    print(f'  {s}')

save_json(all_summaries, os.path.join(OUT_DIR, 'download_summary.json'))
