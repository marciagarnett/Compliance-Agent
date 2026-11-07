"""
One-time script (companion to build_product_master.py) that expands
data/product_master.csv with the additional ASCM Report exports dropped
into ../Products/ on 2026-09-25: eight new non-Poly categories (Business
Desktop Accessories, Desktop Workstation Accessories, DIY MF, Docking
Station, Mobile Workstations, Peripherals CPS & BPS [2 sheets], Retail
Solutions, Thin Client), plus a newer Poly re-export (2026-09-23, superset
of the 2026-09-09 one build_product_master.py already used), plus five
per-product HP Thin Client "SCM" spec documents.

Same idempotent philosophy as build_product_master.py and
build_product_master_kme.py: never touches a SKU already present in
product_master.csv, safe to re-run.

ASCM column layout (Category, Feature ID, Base PN, Local Y/N, Local Code,
3 description columns, Code Name, ..., ES - End of Sales) is identical
across every ASCM Report_*.xlsx file, confirmed by direct inspection - only
the header row number varies (13 for most exports, 19 for the Desktop
Workstation Accessories one), so the header row is located dynamically by
scanning for the 'Base PN' column label rather than assumed at a fixed row
the way build_product_master.py's original single-file version did.

Category handling: ASCM's own Category column is used as-is for every
sheet, with the same Headset -> Bluetooth/Wired split build_product_master.py
uses (keyword check for a radio in the description), since new categories
here can include Headset rows too (Peripherals CPS & BPS in particular).

The five SCM_*.xlsx files are a different shape entirely (a per-product
workbook, not a catalog export) - each is read for its Base Unit row on the
'AV Data' sheet to pull a real per-unit KMAT part number (used as sku) and
marketing long description (used as product_name). They carry no RMN field
at all (confirmed by inspection), so rmn is left blank for these five, same
as every other ASCM-sourced row with no real RMN source.
"""
import csv
import glob
import os
from datetime import datetime

import openpyxl

PM_PATH = "data/product_master.csv"
TODAY = datetime(2026, 9, 25)

# (path relative to this script's cwd, sheet names to process or None for all)
ASCM_SOURCES = [
    ("../Products/ASCM Report_Business Desktop Accessories_2026-8-31.xlsx", None),
    ("../Products/ASCM Report_Desktop Workstation Accessories_2026-8-31.xlsx", None),
    ("../Products/ASCM Report_DIY MF_2026-08-26.xlsx", None),
    ("../Products/ASCM Report_Docking Station_2026-08-26.xlsx", None),
    ("../Products/ASCM Report_Mobile_Workstations_2026-08-26.xlsx", None),
    ("../Products/ASCM Report_Peripherals_CPS & BPS_2026-08-26.xlsx", None),
    ("../Products/ASCM Report_Retail Solutions_2026-8-31.xlsx", None),
    ("../Products/ASCM Report_Thin Client_2026-8-31.xlsx", None),
    ("../Products/ASCM Report_Poly_2026-09-23.xlsx", None),  # newer than the 2026-09-09 export build_product_master.py used
]

SCM_SOURCES = [
    "../Products/SCM_HP_Elite_t655_Thin_Client__HP_tz655_Trusted_Zero_Client_Dec_2025_M73811-999_08_27_2026_336.0.xlsx",
    "../Products/SCM_HP_Elite_t660_Thin_Client__HP_Elite_t660_Fanless_Dec_2025_N86488-999_08_27_2026_180.0.xlsx",
    "../Products/SCM_HP_Elite_t755_Puffin_Dec_2025_M73809-999_08_27_2026_254.0.xlsx",
    "../Products/SCM_HP_EliteDesk_7_G1a_TC_Philby_NPI_2026_P79884-999_08_27_2026_56.0.xlsx",
    "../Products/SCM_HP_Pro_t550_Yuhina_Dec_2025_M98626-999_08_27_2026_307.0.xlsx",
    "../Products/SCM_HP_ProDesk_5_G1i_Waxwing_NPI_2025_P16052-999_08_27_2026_106.0.xlsx",
]


# Local Code -> region, for the handful of codes this project's own
# compliance_requirements.csv actually tracks as a region. Keep in sync
# with lookup.py's SUFFIX_TO_REGION (same 14 regions, same source: a
# direct scan of every ASCM Report_*.xlsx file's Local Code and
# description columns, cross-checked for a 1:1, collision-free mapping -
# see evaluation_review_and_priorities.md). Deliberately only the
# confirmed, unambiguous codes - an unrecognized or blank Local Code
# leaves region "" rather than guessing, same Grounding Rule 3 the rest
# of this project follows.
LOCAL_CODE_TO_REGION = {
    "ABA": "US", "AB0": "Taiwan", "ABU": "UK", "ABB": "EU/UK",
    "AB2": "China", "AB1": "South Korea", "ABJ": "Japan",
    "ABG": "Australia", "AC4": "Brazil", "ACJ": "India",
    "AB4": "Singapore", "A2N": "Saudi Arabia", "A2K": "Philippines",
    "ABT": "Israel",
}


def is_radio_bearing(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in ["bluetooth", " bt ", "bt700", "dect", "wireless", "+bt"])


def best_desc(r):
    return (r[7] or r[5] or r[6] or "").strip()


def find_header_row(ws, max_scan=25):
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=max_scan, max_col=32, values_only=True), start=1):
        if row and "Base PN" in row:
            return i
    return None


def extract_ascm_sheet(ws, existing_skus, seen_skus):
    header_row = find_header_row(ws)
    if header_row is None:
        return [], f"    !! no 'Base PN' header found in sheet '{ws.title}' - skipped"
    rows = [r for r in ws.iter_rows(min_row=header_row + 1, max_row=ws.max_row, max_col=32, values_only=True) if r[0]]

    by_pn = {}
    for r in rows:
        pn = r[2]
        if pn:
            by_pn.setdefault(pn, []).append(r)

    new_rows = []
    skipped_discontinued = 0
    skipped_existing = 0
    skipped_dupe = 0
    for pn, variants in by_pn.items():
        if pn in existing_skus:
            skipped_existing += 1
            continue
        if pn in seen_skus:
            skipped_dupe += 1
            continue
        active_variants = [r for r in variants if not (isinstance(r[29], datetime) and r[29] < TODAY)]
        if not active_variants:
            skipped_discontinued += 1
            continue
        chosen = next((r for r in active_variants if r[3] != "Y"), active_variants[0])

        category_raw = (chosen[0] or "").strip()
        desc = best_desc(chosen)
        if not desc:
            continue
        if category_raw == "Headset":
            category = "Bluetooth Headset" if is_radio_bearing(desc) else "Wired Headset"
        else:
            category = category_raw

        seen_skus.add(pn)
        local_code = (chosen[4] or "").strip() if len(chosen) > 4 else ""
        region = LOCAL_CODE_TO_REGION.get(local_code, "")
        new_rows.append({"product_name": desc, "sku": pn, "rmn": "", "category": category, "region": region})

    summary = (f"    kept {len(new_rows)}, skipped existing {skipped_existing}, "
               f"dupe-within-run {skipped_dupe}, discontinued {skipped_discontinued}")
    return new_rows, summary


def extract_scm_file(path, existing_skus, seen_skus):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["AV Data"]
    header = None
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=15, max_col=25, values_only=True), start=1):
        if row and "AV#" in row:
            header = row
            header_row = i
            break
    if header is None:
        return [], "    !! no AV# header found - skipped"
    cmap = {h: idx for idx, h in enumerate(header) if h}
    cat_idx = 0
    av_idx = cmap.get("AV#")
    longdesc_idx = cmap.get("Marketing Long Description\n(100 Char)")
    shortdesc_idx = cmap.get("Marketing Short Description\n(40 Char)")

    for row in ws.iter_rows(min_row=header_row + 1, max_row=ws.max_row, max_col=25, values_only=True):
        if (row[cat_idx] or "").strip() != "Base Unit":
            continue
        sku = row[av_idx] if av_idx is not None else None
        if not sku:
            continue
        product_name = (longdesc_idx is not None and row[longdesc_idx]) or \
                       (shortdesc_idx is not None and row[shortdesc_idx]) or sku
        if sku in existing_skus:
            return [], f"    skipped (AV# {sku} already in product_master.csv)"
        if sku in seen_skus:
            return [], f"    skipped (AV# {sku} duplicate within this run)"
        seen_skus.add(sku)
        return [{"product_name": product_name.strip(), "sku": sku, "rmn": "", "category": "Thin Client", "region": ""}], \
               f"    added AV# {sku} -> {product_name.strip()!r}"
    return [], "    !! no 'Base Unit' row found in AV Data - skipped"


def main():
    with open(PM_PATH, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    existing_skus = {row["sku"].strip() for row in existing if row["sku"]}
    seen_skus = set()

    all_new_rows = []

    for path, _ in ASCM_SOURCES:
        if not os.path.exists(path):
            print(f"{path}: !! FILE NOT FOUND - skipped")
            continue
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        print(path)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            new_rows, summary = extract_ascm_sheet(ws, existing_skus, seen_skus)
            print(f"  [{sheet_name}]")
            print(summary)
            all_new_rows.extend(new_rows)

    for path in SCM_SOURCES:
        if not os.path.exists(path):
            print(f"{path}: !! FILE NOT FOUND - skipped")
            continue
        print(path)
        new_rows, summary = extract_scm_file(path, existing_skus, seen_skus)
        print(summary)
        all_new_rows.extend(new_rows)

    all_new_rows.sort(key=lambda r: (r["category"], r["product_name"]))

    print()
    print(f"existing rows kept as-is: {len(existing)}")
    print(f"total new rows added: {len(all_new_rows)}")

    with open(PM_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_name", "sku", "rmn", "category", "region"])
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(all_new_rows)


if __name__ == "__main__":
    main()
