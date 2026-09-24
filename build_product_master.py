"""
One-time script used to expand data/product_master.csv from the original 7
hand-picked samples to the full active Poly-brand catalog.

Not part of the running application - kept here for transparency/
reproducibility of how the expanded dataset was built, the same reason
build_data.py (which built compliance_requirements.csv) is kept. Safe to
re-run; it is idempotent against an already-expanded product_master.csv
(anything whose SKU is already present is left alone, never duplicated).

Source: ../ASCM Report_Poly_2026-09-09.xlsx (see source_index.md - this is
now a directly-cited source for product_master.csv, not just a structural
model). That workbook is HP's real ASCM export for the Poly product lines
[BR, NG, NL, NJ] - one row per SKU per localized variant, 2,244 rows across
31 categories as of the 2026-09-09 export.

What this script does, and the judgment calls baked into it:

1. Groups rows by Base PN (the real HP part number / SKU) - the same PN
   often appears more than once for different localized/regional variants
   (e.g. a plain SKU and its "... US" counterpart). One row per PN is kept,
   preferring the non-localized ("Local (Y/N)" != "Y") variant so the
   product name doesn't carry a country suffix.
2. Drops any PN whose every variant has already passed its "ES - End of
   Sales" date as of the run date - i.e. products no longer sold at all.
   (As of the 2026-09-09 export this is only 3 of 2,244 rows - the ASCM
   export is overwhelmingly current-catalog already.)
3. Skips any PN that's already a row in product_master.csv, so this never
   creates a duplicate of (or overwrites) a hand-curated sample row - e.g.
   Poly Sync 20 / 772C4AA, one of the original 7, is also in the ASCM export
   and is left as the original row.
4. category: ASCM's own "Category" column is used as-is for every category
   except "Headset", which this script splits into "Bluetooth Headset" (has
   an RF radio - Bluetooth, DECT, or a bundled BT700 USB dongle - so it's
   the same category the existing 4-domain compliance rows already cover)
   vs. "Wired Headset" (USB/3.5mm only, no radio - a new category with zero
   rows in compliance_requirements.csv today; see README's Scope section and
   GROUNDING_RULES.md Rule 3 for why that's surfaced as an honest coverage
   gap rather than guessed at). The radio/wired split is a keyword check
   over the product description (bluetooth/dect/wireless/bt700/" bt ") -
   a best-effort heuristic, not a lookup against a real RF-certification
   attribute, since ASCM doesn't carry one. Spot-check before trusting it
   for a specific product line.
5. rmn is left blank for every newly-added row: neither ASCM nor the HP
   Products under KME workbook has a Regulatory Model Number field, so
   there is nothing real to put there (the RMN values on the original 7
   samples were authored for the prototype, not sourced from either file).
"""
import csv
import openpyxl
from datetime import datetime

SRC = "../ASCM Report_Poly_2026-09-09.xlsx"
PM_PATH = "data/product_master.csv"
TODAY = datetime(2026, 9, 23)


def is_radio_bearing(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in ["bluetooth", " bt ", "bt700", "dect", "wireless", "+bt"])


def best_desc(r):
    # PMG 100 AMO Description (fullest/most human-readable) first, falling
    # back to the two shorter AMO description columns if it's blank.
    return (r[7] or r[5] or r[6] or "").strip()


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["ASCM Report"]
    rows = [r for r in ws.iter_rows(min_row=14, max_row=2257, max_col=32, values_only=True) if r[0]]

    by_pn: dict[str, list] = {}
    for r in rows:
        pn = r[2]
        if pn:
            by_pn.setdefault(pn, []).append(r)

    with open(PM_PATH, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    existing_skus = {row["sku"].strip() for row in existing}

    new_rows = []
    skipped_discontinued = 0
    skipped_existing = 0
    for pn, variants in by_pn.items():
        if pn in existing_skus:
            skipped_existing += 1
            continue
        active_variants = [r for r in variants if not (isinstance(r[29], datetime) and r[29] < TODAY)]
        if not active_variants:
            skipped_discontinued += 1
            continue
        chosen = next((r for r in active_variants if r[3] != "Y"), active_variants[0])

        category_raw = chosen[0]
        desc = best_desc(chosen)
        if category_raw == "Headset":
            category = "Bluetooth Headset" if is_radio_bearing(desc) else "Wired Headset"
        else:
            category = category_raw

        new_rows.append({
            "product_name": desc,
            "sku": pn,
            "rmn": "",
            "category": category,
        })

    new_rows.sort(key=lambda r: (r["category"], r["product_name"]))

    print(f"existing rows kept as-is: {len(existing)}")
    print(f"skipped (already in product_master.csv): {skipped_existing}")
    print(f"skipped (fully discontinued, no active variant): {skipped_discontinued}")
    print(f"new rows added: {len(new_rows)}")

    with open(PM_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_name", "sku", "rmn", "category"])
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)


if __name__ == "__main__":
    main()
