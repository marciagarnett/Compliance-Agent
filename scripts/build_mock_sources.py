#!/usr/bin/env python3
"""
One-time setup: partitions the agent's current data/*.csv into mock
"source system" feeds that stand in for HP's real systems of record.

This exists so the business-process simulation has something realistic to
sync FROM. In a real HP deployment, product_master data would come from
PLM/ERP, and compliance_requirements data would come from however many
separate teams track their own domain (warranty/legal, trade compliance,
regulatory affairs, environmental/sustainability, an emerging-regulations
horizon-scan, and a handful of specialized SME-tracked standards) - which is
exactly the fragmentation the agent's problem statement describes. Rather
than invent fake content, this splits the CSVs that already exist (and are
already sourced/cited per row) along their real citation_source column, so
each mock feed is a faithful subset of verified content, just filed under
the system/team that would really own it.

Run once to bootstrap source_systems_integration/. The recurring job is
sync_from_source_systems.py, which reads these feeds back in - this script
is not part of the weekly schedule.
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCES = ROOT / "source_systems_integration"

# citation_source prefix (text before " - ", or the whole string when there
# is no " - ") -> (mock feed filename, owning team/system label)
SOURCE_MAP = {
    "WW_Content_Requirements_FY25_FINAL.xlsx": (
        "warranty_requirements_feed.csv", "Warranty & Legal"),
    "Machinery_ITE_Import_or_Importer_controls.xlsx": (
        "trade_customs_feed.csv", "Trade Compliance"),
    "Regulatory Requirements Summary.xlsx": (
        "regulatory_requirements_feed.csv", "Regulatory Affairs"),
    "WW-long-form-QSG-content (2).xlsx": (
        "environmental_sustainability_feed.csv", "Environmental & Sustainability Compliance"),
    "ER Roadmap_FY26Q3.pdf": (
        "emerging_regulations_roadmap_feed.csv", "Regulatory Horizon Scanning"),
}
# Anything not in SOURCE_MAP above (standalone regulation/standard citations
# - battery, cybersecurity, hearing-aid-compatibility) is small enough in
# each individual bucket that in practice it's tracked ad hoc rather than in
# one of HP's five maintained trackers - grouped into one feed.
FALLBACK_FEED = ("specialized_standards_feed.csv", "Specialized Compliance SMEs")


def main() -> None:
    SOURCES.mkdir(exist_ok=True)

    # --- product master: one system of record (PLM/ERP) ---
    plm_path = SOURCES / "plm_product_master_extract.csv"
    shutil.copyfile(DATA / "product_master.csv", plm_path)
    with open(DATA / "product_master.csv", newline="", encoding="utf-8") as f:
        pm_rows = sum(1 for _ in csv.DictReader(f))
    print(f"wrote {plm_path.name}: {pm_rows} product records (from data/product_master.csv)")

    # --- compliance requirements: fragmented across team feeds ---
    with open(DATA / "compliance_requirements.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    buckets: dict[str, list[dict]] = {}
    for row in rows:
        prefix = row["citation_source"].split(" - ")[0].strip()
        feed_name, owning_team = SOURCE_MAP.get(prefix, FALLBACK_FEED)
        bucket = buckets.setdefault(feed_name, {"owning_team": owning_team, "rows": []})
        bucket["rows"].append(row)

    out_fields = ["owning_team"] + list(fieldnames)
    for feed_name, bucket in sorted(buckets.items()):
        out_path = SOURCES / feed_name
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            for row in bucket["rows"]:
                writer.writerow({"owning_team": bucket["owning_team"], **row})
        print(f"wrote {feed_name}: {len(bucket['rows'])} requirements (owner: {bucket['owning_team']})")

    print(f"\n{len(buckets)} mock compliance feeds + 1 product-master feed written to {SOURCES}")


if __name__ == "__main__":
    main()
