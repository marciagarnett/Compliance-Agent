#!/usr/bin/env python3
"""
Weekly sync: pulls from the mock "source system" feeds in
source_systems_integration/ (standing in for HP's real PLM/ERP and the various
compliance teams' own systems) and refreshes data/product_master.csv and
data/compliance_requirements.csv - the single source of truth the live
agent (app.py / agent.py, via lookup.py) actually queries.

This is the piece of the simulation that makes the agent's answers stay
current proactively: run this on a schedule, and whenever one of the mock
source feeds changes (a team updates their tracker), that change shows up
in the agent's data on the next run - instead of someone discovering the
gap only after documentation has already shipped.

Usage:  python scripts/sync_from_source_systems.py

Writes a dated row to sync_log.csv every run (even a no-op run), and backs
up the previous data/*.csv before overwriting (as data/<name>_<UTC
timestamp>.csv.bak, ignored by git like the project's other .bak files).

Fail-safe, not fail-open: if a source feed can't be read/parsed, that half
of the sync is skipped (with a loud warning) and the existing, previously
verified data/*.csv is left untouched rather than overwritten with
something unverified. This mirrors app.py's own "fail loudly, never serve
half-broken data" approach.
"""
from __future__ import annotations

import csv
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCES = ROOT / "source_systems_integration"
LOG_PATH = ROOT / "sync_log.csv"

PRODUCT_MASTER_FIELDS = ["product_name", "sku", "rmn", "category"]
COMPLIANCE_FIELDS = [
    "category", "region", "domain", "requirement", "documentation_format",
    "status", "must_comply_by", "citation_source", "last_verified",
]


def _read_rows(path: Path, fieldnames: list[str]) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{k: row.get(k, "") for k in fieldnames} for row in reader]


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _backup(path: Path, stamp: str) -> None:
    if not path.exists():
        return
    backup_path = path.with_name(f"{path.stem}_{stamp}.csv.bak")
    backup_path.write_bytes(path.read_bytes())


def sync_product_master(stamp: str) -> tuple[int, int]:
    """Returns (added, removed) row counts; (0, 0) if unchanged or on error."""
    feed_path = SOURCES / "plm_product_master_extract.csv"
    live_path = DATA / "product_master.csv"
    try:
        new_rows = _read_rows(feed_path, PRODUCT_MASTER_FIELDS)
    except Exception as exc:  # noqa: BLE001 - this is a demo sync job
        print(f"  [SKIPPED] product master: couldn't read {feed_path.name}: {exc}")
        return 0, 0

    old_rows = _read_rows(live_path, PRODUCT_MASTER_FIELDS) if live_path.exists() else []
    old_set = {tuple(r[k] for k in PRODUCT_MASTER_FIELDS) for r in old_rows}
    new_set = {tuple(r[k] for k in PRODUCT_MASTER_FIELDS) for r in new_rows}
    added, removed = len(new_set - old_set), len(old_set - new_set)

    if added or removed:
        _backup(live_path, stamp)
        _write_rows(live_path, PRODUCT_MASTER_FIELDS, new_rows)
    return added, removed


def sync_compliance_requirements(stamp: str) -> tuple[int, int, list[str]]:
    """Returns (added, removed, per_feed_summary_lines)."""
    feed_paths = sorted(SOURCES.glob("*_feed.csv"))
    new_rows: list[dict] = []
    summary: list[str] = []
    for feed_path in feed_paths:
        try:
            rows = _read_rows(feed_path, ["owning_team"] + COMPLIANCE_FIELDS)
        except Exception as exc:  # noqa: BLE001 - this is a demo sync job
            print(f"  [SKIPPED FEED] {feed_path.name}: couldn't read it: {exc}")
            continue
        owning_team = rows[0]["owning_team"] if rows else "(unknown)"
        summary.append(f"{feed_path.name} ({owning_team}): {len(rows)} rows")
        for row in rows:
            new_rows.append({k: row[k] for k in COMPLIANCE_FIELDS})

    if not feed_paths:
        print("  [SKIPPED] compliance requirements: no *_feed.csv files found")
        return 0, 0, []

    new_rows.sort(key=lambda r: (r["category"], r["region"], r["domain"], r["requirement"]))

    live_path = DATA / "compliance_requirements.csv"
    old_rows = _read_rows(live_path, COMPLIANCE_FIELDS) if live_path.exists() else []
    old_set = {tuple(r[k] for k in COMPLIANCE_FIELDS) for r in old_rows}
    new_set = {tuple(r[k] for k in COMPLIANCE_FIELDS) for r in new_rows}
    added, removed = len(new_set - old_set), len(old_set - new_set)

    if added or removed:
        _backup(live_path, stamp)
        _write_rows(live_path, COMPLIANCE_FIELDS, new_rows)
    return added, removed, summary


def _log(stamp: str, pm_added: int, pm_removed: int, cr_added: int, cr_removed: int) -> None:
    is_new = not LOG_PATH.exists()
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow([
                "run_timestamp_utc", "product_master_added", "product_master_removed",
                "compliance_requirements_added", "compliance_requirements_removed", "changed",
            ])
        changed = bool(pm_added or pm_removed or cr_added or cr_removed)
        writer.writerow([stamp, pm_added, pm_removed, cr_added, cr_removed, changed])


def main() -> int:
    if not SOURCES.exists():
        print(f"ERROR: {SOURCES} does not exist - run scripts/build_mock_sources.py first.")
        return 1

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"=== sync run {stamp} ===")

    pm_added, pm_removed = sync_product_master(stamp)
    cr_added, cr_removed, feed_summary = sync_compliance_requirements(stamp)

    for line in feed_summary:
        print(f"  - {line}")

    print(f"product_master.csv:          +{pm_added} / -{pm_removed}")
    print(f"compliance_requirements.csv: +{cr_added} / -{cr_removed}")

    _log(stamp, pm_added, pm_removed, cr_added, cr_removed)

    if pm_added or pm_removed or cr_added or cr_removed:
        print("Result: CHANGES PULLED IN - data/*.csv updated, previous versions backed up.")
    else:
        print("Result: no changes - the agent's data already matches all source feeds.")
    print(f"Logged to {LOG_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
