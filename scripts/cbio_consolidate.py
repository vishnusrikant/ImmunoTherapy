#!/usr/bin/env python3
"""Build a consolidated cross-study cBioPortal patient CSV with harmonized features."""

import csv
import os
import json
from collections import defaultdict, Counter

ROOT = '/home/vishnusrikant/ImmunoTherapy/datasets/cbioportal'

STUDIES = {
    'mel_dfci_2019': 'Melanoma (DFCI 2019)',
    'blca_iatlas_imvigor210_2017': 'Bladder (IMvigor210 2017)',
    'rcc_iatlas_immotion150_2018': 'RCC (IMmotion150 2018)',
    'nsclc_pd1_msk_2018': 'NSCLC (MSK 2018)',
    'mel_iatlas_liu_2019': 'Melanoma (Liu 2019)',
    'mel_iatlas_riaz_nivolumab_2017': 'Melanoma (Riaz Nivolumab 2017)',
    'mel_ucla_2016': 'Melanoma (UCLA 2016)',
}

# Map drug strings to canonical agent + target
DRUG_MAP = {
    'mk3475': ('Pembrolizumab', 'PD-1'),
    'pembrolizumab': ('Pembrolizumab', 'PD-1'),
    'pembro': ('Pembrolizumab', 'PD-1'),
    'nivolumab': ('Nivolumab', 'PD-1'),
    'nivo': ('Nivolumab', 'PD-1'),
    'bms-936558': ('Nivolumab', 'PD-1'),
    'ipilimumab': ('Ipilimumab', 'CTLA-4'),
    'ipi': ('Ipilimumab', 'CTLA-4'),
    'atezolizumab': ('Atezolizumab', 'PD-L1'),
    'atezo': ('Atezolizumab', 'PD-L1'),
    'mpdl3280a': ('Atezolizumab', 'PD-L1'),
    'durvalumab': ('Durvalumab', 'PD-L1'),
    'anti-pd-1': ('anti-PD-1', 'PD-1'),
    'anti-pd1': ('anti-PD-1', 'PD-1'),
    'anti-ctla-4': ('anti-CTLA-4', 'CTLA-4'),
    'anti-ctla4': ('anti-CTLA-4', 'CTLA-4'),
    'combo': ('Combo PD-1+CTLA-4', 'PD-1+CTLA-4'),
    'pd-1/pdl-1': ('anti-PD-1/PD-L1', 'PD-1/PD-L1'),
    'pd-1': ('anti-PD-1', 'PD-1'),
    'pd-l1': ('anti-PD-L1', 'PD-L1'),
    'ctla-4': ('anti-CTLA-4', 'CTLA-4'),
    'ctla4': ('anti-CTLA-4', 'CTLA-4'),
}


def norm_drug(s):
    if not s:
        return ('', '')
    s = s.strip().lower()
    # Try full match first
    if s in DRUG_MAP:
        return DRUG_MAP[s]
    # Try substring match
    for k, v in DRUG_MAP.items():
        if k in s:
            return v
    return (s, 'Unknown')


def yn(v):
    if v is None:
        return ''
    v = str(v).strip().lower()
    if v in ('yes', 'y', 'true', '1'):
        return 'Yes'
    if v in ('no', 'n', 'false', '0'):
        return 'No'
    return ''


def load_study_patients(sid):
    """Load wide-format patient clinical data for a study."""
    path = os.path.join(ROOT, sid, f'{sid}_patient_clinical_data.csv')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def load_sample_clinical(sid):
    """Load wide-format sample clinical data, indexed by sampleId with patient linked via samples.csv."""
    # First load samples.csv to get sample -> patient mapping
    s_path = os.path.join(ROOT, sid, f'{sid}_samples.csv')
    sample_to_patient = {}
    if os.path.exists(s_path):
        with open(s_path) as f:
            for row in csv.DictReader(f):
                sample_to_patient[row['sampleId']] = row.get('patientId', '')
    # Load sample clinical
    sc_path = os.path.join(ROOT, sid, f'{sid}_sample_clinical_data.csv')
    if not os.path.exists(sc_path):
        return {}, sample_to_patient
    with open(sc_path) as f:
        samples = {row['sampleId']: row for row in csv.DictReader(f)}
    return samples, sample_to_patient


# Build harmonized rows
out_rows = []

for sid, label in STUDIES.items():
    patients = load_study_patients(sid)
    sample_clin, sample_to_patient = load_sample_clinical(sid)

    # Build patient -> best sample clinical
    patient_sample_clin = defaultdict(dict)
    for sample_id, sc in sample_clin.items():
        pid = sample_to_patient.get(sample_id, '')
        if pid and pid not in patient_sample_clin:
            patient_sample_clin[pid] = sc

    for p in patients:
        pid = p['patientId']
        sc = patient_sample_clin.get(pid, {})

        # Age: multiple fields across studies
        age = (p.get('AGE') or p.get('AGE_AT_DIAGNOSIS') or p.get('AGE_AT_SEQ_REPORT')
               or p.get('AGE_GROUP') or sc.get('AGE') or '')

        sex = (p.get('SEX') or p.get('GENDER') or sc.get('SEX') or '')

        # Cancer type
        cancer_type = (sc.get('CANCER_TYPE') or p.get('CANCER_TYPE')
                       or sc.get('CANCER_TYPE_DETAILED') or p.get('CANCER_TYPE_DETAILED') or '')

        # Drug/treatment
        drug_raw = (p.get('IO_THERAPY') or p.get('ICI_RX') or p.get('DRUG_TYPE')
                    or p.get('TREATMENT') or p.get('TREATMENT_TYPE') or sc.get('ICI_RX') or '')
        drug_name, drug_target = norm_drug(drug_raw)

        # Prior therapies
        num_prior = (p.get('NUM_PRIOR_THERAPIES') or p.get('LINES_OF_TX')
                     or p.get('NUMBER_OF_PRIOR_THERAPIES') or '')
        prior_ctla4 = yn(p.get('PRIOR_CTLA4') or p.get('PRIOR_ICI_RX'))
        prior_mapk = yn(p.get('PRIOR_MAPK_TX') or p.get('PREVIOUS_MAPKI'))

        # Lab / status markers
        ldh = (p.get('TX_START_LDH') or p.get('LDH') or '')
        ldh_elevated = yn(p.get('LDH_ELEVATED'))
        ecog = (p.get('TX_START_ECOG') or p.get('ECOG') or '')
        steroids = yn(p.get('STEROIDS_GT_10MG_DAILY'))

        # Metastasis
        met_brain = yn(p.get('MET_BRAIN'))
        met_liver = yn(p.get('LIVER_VISC_MET'))
        met_lung = yn(p.get('LUNG_MET'))
        met_bone = yn(p.get('MET_BONE'))
        met_ln = yn(p.get('LN_MET'))
        met_subq = yn(p.get('CUT_SUBQ_MET'))
        m_stage = (p.get('M_STAGE') or '')

        # TMB / mutation burden
        tmb = (sc.get('TMB_NONSYNONYMOUS') or p.get('TMB_NONSYNONYMOUS')
               or sc.get('MUTATION_COUNT') or p.get('MUTATION_COUNT') or '')

        # Response
        response = (p.get('RESPONSE') or p.get('RESPONDER') or p.get('BR')
                    or p.get('TREATMENT_RESPONSE') or p.get('CLINICAL_BENEFIT') or '')

        # Survival
        os_months = p.get('OS_MONTHS') or ''
        os_status = p.get('OS_STATUS') or ''
        pfs_months = p.get('PFS_MONTHS') or ''
        pfs_status = p.get('PFS_STATUS') or ''

        out_rows.append({
            'study_id': sid,
            'study_label': label,
            'patient_id': pid,
            'age_or_group': age,
            'sex': sex,
            'cancer_type': cancer_type,
            'io_drug_raw': drug_raw,
            'io_drug_canonical': drug_name,
            'io_drug_target': drug_target,
            'num_prior_therapies': num_prior,
            'prior_ctla4': prior_ctla4,
            'prior_mapk': prior_mapk,
            'tx_start_ldh': ldh,
            'ldh_elevated': ldh_elevated,
            'tx_start_ecog': ecog,
            'steroids_gt_10mg_daily': steroids,
            'met_brain': met_brain,
            'met_liver_visceral': met_liver,
            'met_lung': met_lung,
            'met_bone': met_bone,
            'met_ln': met_ln,
            'met_cut_subq': met_subq,
            'm_stage': m_stage,
            'tmb_nonsynonymous': tmb,
            'response': response,
            'os_months': os_months,
            'os_status': os_status,
            'pfs_months': pfs_months,
            'pfs_status': pfs_status,
        })


out_path = os.path.join(ROOT, 'all_patients_consolidated.csv')
with open(out_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    w.writeheader()
    w.writerows(out_rows)

print(f'Wrote {len(out_rows)} patients to {out_path}')

# Summary stats
print('\n=== Coverage Summary ===')
print(f'Total patients: {len(out_rows)}')
studies = Counter(r['study_id'] for r in out_rows)
print('\nPer study:')
for k, v in studies.most_common():
    print(f'  {v:<4}  {k}')

print('\nFeature coverage (non-empty):')
fields = [f for f in out_rows[0].keys() if f not in ('study_id', 'study_label', 'patient_id')]
for f in fields:
    n = sum(1 for r in out_rows if r[f] not in ('', None))
    pct = 100.0 * n / len(out_rows)
    print(f'  {f:<30} {n:>5} / {len(out_rows)}  ({pct:>5.1f}%)')

print('\nDrug distribution:')
drugs = Counter(r['io_drug_canonical'] for r in out_rows if r['io_drug_canonical'])
for k, v in drugs.most_common(10):
    print(f'  {v:<4} {k}')

print('\nTarget distribution:')
tgts = Counter(r['io_drug_target'] for r in out_rows if r['io_drug_target'])
for k, v in tgts.most_common():
    print(f'  {v:<4} {k}')

print('\nCancer types:')
cts = Counter(r['cancer_type'] for r in out_rows if r['cancer_type'])
for k, v in cts.most_common(10):
    print(f'  {v:<4} {k}')

print('\nSex:')
sx = Counter(r['sex'] for r in out_rows if r['sex'])
for k, v in sx.most_common():
    print(f'  {v:<4} {k}')

print('\nResponse:')
rsp = Counter(r['response'] for r in out_rows if r['response'])
for k, v in rsp.most_common(10):
    print(f'  {v:<4} {k}')
