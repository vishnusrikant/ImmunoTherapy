"""
UK Biobank Showcase catalog puller.

Downloads the publicly-available UKB Showcase schemas (metadata only — no
patient-level data) into datasets/ukbiobank_catalog/ and derives:

  - gap_features_summary.csv  — CRP / IL-6 / ICD-10 diagnosis field coverage
  - autoimmune_icd10_codes.csv — ICD-10 codes for irAE-relevant autoimmune dx

These files are used in the project's limitations section to cite exact UKB
field IDs and coverage counts. No UKB login or approved application required —
Showcase metadata is publicly downloadable.

Source: https://biobank.ndph.ox.ac.uk/showcase/
"""

from __future__ import annotations

import csv
import sys
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "datasets" / "ukbiobank_catalog"
SCHEMA_BASE = "https://biobank.ndph.ox.ac.uk/ukb/scdown.cgi?fmt=txt&id={sid}"

SCHEMAS = {
    1:  "fields.tsv",
    2:  "encodings.tsv",
    3:  "categories.tsv",
    11: "encoding_values_hierint.tsv",
    12: "encoding_values_hierstr.tsv",
}

ICD10_ENCODING_ID = "19"

AUTOIMMUNE_PREFIXES = {
    "E05":   "Graves' disease / thyrotoxicosis",
    "E06":   "Thyroiditis (incl. Hashimoto's)",
    "E10":   "Type 1 diabetes mellitus",
    "G35":   "Multiple sclerosis",
    "G61":   "Inflammatory polyneuropathy (incl. Guillain-Barre)",
    "G70":   "Myasthenia gravis and other myoneural disorders",
    "K50":   "Crohn's disease",
    "K51":   "Ulcerative colitis",
    "K74":   "Fibrosis and cirrhosis of liver (incl. autoimmune hepatitis)",
    "K75":   "Other inflammatory liver diseases",
    "L10":   "Pemphigus",
    "L40":   "Psoriasis",
    "L63":   "Alopecia areata",
    "L80":   "Vitiligo",
    "M05":   "Seropositive rheumatoid arthritis",
    "M06":   "Other rheumatoid arthritis",
    "M30":   "Polyarteritis nodosa and related conditions",
    "M31":   "Other necrotizing vasculopathies",
    "M32":   "Systemic lupus erythematosus",
    "M33":   "Dermatopolymyositis",
    "M34":   "Systemic sclerosis",
    "M35":   "Other systemic involvement of connective tissue (incl. Sjogren's)",
    "M45":   "Ankylosing spondylitis",
    "D86":   "Sarcoidosis",
    "D68.61": "Antiphospholipid syndrome (within coagulation defects)",
}


def download_schema(sid: int, fname: str) -> Path:
    dest = OUT_DIR / fname
    if dest.exists() and dest.stat().st_size > 1024:
        print(f"  [skip] {fname} already present ({dest.stat().st_size:,} bytes)")
        return dest
    url = SCHEMA_BASE.format(sid=sid)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    print(f"  [get]  {url}")
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        out.write(resp.read())
    print(f"         wrote {fname} ({dest.stat().st_size:,} bytes)")
    return dest


def load_fields(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def find_gap_feature_fields(fields: list[dict]) -> list[dict]:
    # IL-6 has no standalone UKB field — it is one of ~2,941 Olink Explore assays
    # accessed through Field 30900 + Data-Coding 143. So we match by field_id for
    # Olink and by title keyword for the others.
    keyword_map = {
        "CRP":               ("c-reactive protein",),
        "Autoimmune ICD-10": ("diagnoses - icd10", "diagnoses - icd-10"),
        "NLR inputs":        ("neutrophil count", "lymphocyte count"),
        "Albumin":           ("albumin",),
        "BMI":               ("body mass index",),
    }
    olink_field_ids = {"30900", "30901", "30902", "30903"}

    rows = []
    for label, needles in keyword_map.items():
        for row in fields:
            title = row["title"].lower()
            if any(n in title for n in needles):
                rows.append(_gap_row(label, row))
    for row in fields:
        if row["field_id"] in olink_field_ids:
            rows.append(_gap_row("IL-6 (Olink panel)", row))
    return rows


def _gap_row(label: str, row: dict) -> dict:
    return {
        "gap_feature":      label,
        "field_id":         row["field_id"],
        "title":            row["title"],
        "units":            row.get("units", ""),
        "num_participants": row.get("num_participants", ""),
        "item_count":       row.get("item_count", ""),
        "main_category":    row.get("main_category", ""),
        "debut":            row.get("debut", ""),
    }


def extract_autoimmune_icd10(hierstr_path: Path) -> list[dict]:
    rows = []
    with open(hierstr_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["encoding_id"] != ICD10_ENCODING_ID:
                continue
            code = row["value"]
            for prefix, block_label in AUTOIMMUNE_PREFIXES.items():
                if code.startswith(prefix.replace(".", "")) or code == prefix:
                    rows.append({
                        "icd10_code":      code,
                        "meaning":         row["meaning"],
                        "autoimmune_block": prefix,
                        "block_label":     block_label,
                    })
                    break
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"         wrote {path.name} ({len(rows)} rows)")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUT_DIR}")

    print("\n[1/3] Downloading UKB Showcase schema files...")
    for sid, fname in SCHEMAS.items():
        download_schema(sid, fname)

    print("\n[2/3] Extracting gap-feature field coverage...")
    fields = load_fields(OUT_DIR / "fields.tsv")
    gap_rows = find_gap_feature_fields(fields)
    write_csv(
        OUT_DIR / "gap_features_summary.csv",
        gap_rows,
        ["gap_feature", "field_id", "title", "units",
         "num_participants", "item_count", "main_category", "debut"],
    )

    print("\n[3/3] Extracting autoimmune ICD-10 codes...")
    autoimmune = extract_autoimmune_icd10(OUT_DIR / "encoding_values_hierstr.tsv")
    write_csv(
        OUT_DIR / "autoimmune_icd10_codes.csv",
        autoimmune,
        ["icd10_code", "meaning", "autoimmune_block", "block_label"],
    )

    print(f"\nDone. {len(gap_rows)} gap-feature rows, {len(autoimmune)} autoimmune ICD-10 codes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
