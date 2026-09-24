"""
Deterministic core of the Compliance Lookup Agent.

Everything in this file is plain Python + csv - no network calls, no LLM.
This is the part of the app that must never guess: it either finds a real
row in the sample dataset, or it says plainly that it found nothing.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PRODUCT_MASTER_PATH = os.path.join(DATA_DIR, "product_master.csv")
COMPLIANCE_PATH = os.path.join(DATA_DIR, "compliance_requirements.csv")

# Canonical region names, in display order, mapped from accepted user input.
REGION_ALIASES = {
    "eu": "EU/UK", "eu/uk": "EU/UK", "uk": "EU/UK", "eu / uk": "EU/UK",
    "european union": "EU/UK", "united kingdom": "EU/UK", "eu-uk": "EU/UK",
    "us": "US", "usa": "US", "u.s.": "US", "u.s.a.": "US",
    "united states": "US", "america": "US",
    "china": "China", "cn": "China", "prc": "China",
    "taiwan": "Taiwan", "tw": "Taiwan", "roc": "Taiwan",
}
VALID_REGIONS = ["EU/UK", "US", "China", "Taiwan"]

# Order requirement domains are grouped/printed in, with a human-readable label.
DOMAIN_ORDER = [
    ("environmental_sustainability", "Environmental / Sustainability"),
    ("safety_emc_telecom", "Regulatory (Safety / EMC / Telecom)"),
    ("hearing_aid_compatibility", "Hearing Aid Compatibility"),
    ("cybersecurity", "Cybersecurity"),
    ("battery_safety", "Battery Safety"),
    ("trade_customs", "Trade / Customs"),
    ("warranty_documentation", "Warranty Documentation"),
]


@dataclass
class Product:
    product_name: str
    sku: str
    rmn: str
    category: str


@dataclass
class Requirement:
    category: str
    region: str
    domain: str
    requirement: str
    documentation_format: str  # print | online | either
    status: str  # existing | emerging
    must_comply_by: str
    citation_source: str
    last_verified: str


@dataclass
class LookupResult:
    ok: bool
    message: str = ""
    product: Optional[Product] = None
    region: Optional[str] = None
    requirements_by_domain: dict = field(default_factory=dict)
    # A short, fixed label for *why* ok is False - "" when ok is True.
    # Exists so callers (agent.py's activity log) have something structured
    # to record instead of parsing or duplicating the full message text.
    reason_code: str = ""
    # Which of the seven DOMAIN_ORDER keys the caller asked to narrow the
    # answer to (llm_agent.detect_requested_domains()) - empty means no
    # narrowing was requested, so every rendering function below shows the
    # full seven-domain profile, exactly as before domain scoping existed.
    requested_domains: list = field(default_factory=list)


def load_products(path: str = PRODUCT_MASTER_PATH) -> list[Product]:
    with open(path, newline="", encoding="utf-8") as f:
        return [Product(**row) for row in csv.DictReader(f)]


def load_requirements(path: str = COMPLIANCE_PATH) -> list[Requirement]:
    with open(path, newline="", encoding="utf-8") as f:
        return [Requirement(**row) for row in csv.DictReader(f)]


def normalize_region(raw: str) -> Optional[str]:
    """Return one of VALID_REGIONS, or None if the input doesn't match any of them."""
    if not raw:
        return None
    key = raw.strip().lower()
    if key in REGION_ALIASES:
        return REGION_ALIASES[key]
    # allow exact match on the canonical form too, case-insensitively
    for region in VALID_REGIONS:
        if region.lower() == key:
            return region
    return None


def find_product(identifier: str, products: list[Product]) -> Optional[Product]:
    """Exact-match lookup (case-insensitive) across product_name, sku, and rmn."""
    if not identifier:
        return None
    key = identifier.strip().lower()
    for p in products:
        if p.product_name.strip().lower() == key:
            return p
        if p.sku.strip().lower() == key:
            return p
        if p.rmn.strip().lower() == key:
            return p
    return None


def get_requirements(category: str, region: str, requirements: list[Requirement]) -> dict:
    """Return {domain_key: [Requirement, ...]} for the given category+region, in DOMAIN_ORDER."""
    grouped: dict[str, list[Requirement]] = {key: [] for key, _ in DOMAIN_ORDER}
    for r in requirements:
        if r.category == category and r.region == region:
            grouped.setdefault(r.domain, []).append(r)
    return grouped


def run_lookup(identifier: str, region_raw: str,
               products: Optional[list[Product]] = None,
               requirements: Optional[list[Requirement]] = None,
               requested_domains: Optional[list[str]] = None) -> LookupResult:
    """
    The single entry point both the CLI and the LLM layer call.
    Never raises on "not found" - it always returns a LookupResult explaining why.

    requested_domains - optional subset of DOMAIN_ORDER's keys (from
    llm_agent.detect_requested_domains()) to narrow the answer to. Unknown
    keys are dropped rather than trusted, since this is meant to be a closed
    set. None/empty means "no narrowing requested" - the full seven-domain
    profile, exactly as before this parameter existed.
    """
    products = products if products is not None else load_products()
    requirements = requirements if requirements is not None else load_requirements()
    valid_domain_keys = {key for key, _ in DOMAIN_ORDER}
    requested_domains = [d for d in (requested_domains or []) if d in valid_domain_keys]

    region = normalize_region(region_raw)
    if region is None:
        return LookupResult(
            ok=False,
            reason_code="unsupported_region",
            message=(
                f"'{region_raw}' isn't a region this prototype covers. "
                f"Supported regions right now: {', '.join(VALID_REGIONS)}. "
                "This isn't a real 'no requirements' answer - it's a coverage gap, "
                "and this app will not guess at an answer it doesn't have data for "
                "(Grounding Rule 3). Please re-check the destination, or escalate "
                "to a regulatory subject-matter expert for human review (Grounding "
                "Rule 4) for regions outside this list."
            ),
        )

    product = find_product(identifier, products)
    if product is None:
        return LookupResult(
            ok=False,
            reason_code="unmatched_product",
            message=(
                f"No product matching '{identifier}' was found in the sample product "
                "master (checked product name, SKU, and RMN, exact match only). "
                "Double-check the identifier for typos, or confirm it's one of the "
                "sample products this prototype includes - it does not cover HP's full "
                "catalog. If the identifier is correct and just isn't in this dataset, "
                "this app will not guess (Grounding Rule 3) - escalate to a regulatory "
                "subject-matter expert for human review (Grounding Rule 4) rather than "
                "assuming no requirements apply."
            ),
        )

    grouped = get_requirements(product.category, region, requirements)
    if requested_domains:
        scoped_total = sum(len(grouped.get(d, [])) for d in requested_domains)
    else:
        scoped_total = sum(len(v) for v in grouped.values())

    if scoped_total == 0:
        domain_label_by_key = dict(DOMAIN_ORDER)
        if requested_domains:
            scope_note = ", ".join(domain_label_by_key[d] for d in requested_domains)
            scope_message = (
                f"You asked specifically about {scope_note}. No {scope_note} requirements "
                f"are on file for '{product.product_name}' (category '{product.category}') "
                f"in {region}. That is a coverage gap for the domain(s) you asked about, not "
                "a statement that no requirements apply at all - other domains for this "
                "product/region may still have requirements on file; ask without naming a "
                "specific domain to see the full profile. This app will not guess at what's "
                "missing (Grounding Rule 3) - verify with a regulatory subject-matter expert "
                "for human review (Grounding Rule 4) before treating this as 'nothing "
                "required'."
            )
        else:
            scope_message = (
                f"'{product.product_name}' resolved to category '{product.category}', "
                f"but no compliance requirements are on file for that category in {region}. "
                "That is a coverage gap in this sample dataset, not a statement that no "
                "requirements exist - this app will not guess at what's missing (Grounding "
                "Rule 3). Verify with a regulatory subject-matter expert for human review "
                "(Grounding Rule 4) before treating this as 'nothing required'."
            )
        return LookupResult(
            ok=False,
            product=product,
            region=region,
            reason_code="zero_requirements_on_file",
            requested_domains=requested_domains,
            message=scope_message,
        )

    return LookupResult(
        ok=True, product=product, region=region, requirements_by_domain=grouped,
        requested_domains=requested_domains,
    )


def _active_domain_order(result: LookupResult) -> list[tuple[str, str]]:
    """
    DOMAIN_ORDER, narrowed to result.requested_domains when the question
    named specific domain(s) - unfiltered (all seven) otherwise, exactly as
    before domain scoping existed. Every function that renders per-domain
    content derives from this, so a scoped answer never shows, counts, or
    even lists as empty a domain the user didn't ask about - that's the
    difference between scoping and omission: a domain that WAS asked about
    and came back empty still gets its own "(no requirements on file)" line
    (see the zero-requirements-on-file gap in run_lookup() for the case
    where every requested domain is empty).
    """
    if not result.requested_domains:
        return DOMAIN_ORDER
    wanted = set(result.requested_domains)
    return [(key, label) for key, label in DOMAIN_ORDER if key in wanted]


def _flatten_ordered(result: LookupResult) -> list[tuple[int, "Requirement", str]]:
    """
    Number every requirement once, in domain order (the same order the full
    itemized report prints in - narrowed to result.requested_domains when
    set), and return [(row_number, requirement, domain_key), ...]. This
    numbering is the only thing that ties the urgency-sorted summary/table
    to the domain-grouped full report below it - row #7 in the table is
    always the same requirement as [#7] in the list. Numbering restarts at
    #1 for a scoped answer rather than keeping gaps from skipped domains.
    """
    flat = []
    n = 0
    for domain_key, _ in _active_domain_order(result):
        for r in result.requirements_by_domain.get(domain_key, []):
            n += 1
            flat.append((n, r, domain_key))
    return flat


def _urgency_tier(r: "Requirement") -> int:
    """
    0 = existing (already in force now), 1 = emerging with a real compliance
    date, 2 = emerging with no date yet (must_comply_by == "TBD"). This reads
    only the status/must_comply_by fields already in the dataset - it does
    not add any new judgment about which items matter more (Grounding Rule 2:
    no invented policy), it just orders what is already on file.
    """
    if r.status != "emerging":
        return 0
    if r.must_comply_by and r.must_comply_by.strip().upper() != "TBD":
        return 1
    return 2


def _build_summary_lines(result: LookupResult, flat: list) -> list[str]:
    """
    A short, counts-only summary bucketed by urgency tier. Deliberately does
    NOT paraphrase or shorten any requirement's text - only counts, domain
    labels, and the must_comply_by dates already on file, so nothing here can
    drift from what the table and full report say (Grounding Rule 2).
    """
    domain_label_by_key = dict(DOMAIN_ORDER)
    total = len(flat)
    tiers: dict[int, list] = {0: [], 1: [], 2: []}
    for n, r, domain_key in flat:
        tiers[_urgency_tier(r)].append((n, r, domain_key))

    lines = [
        f"\nSUMMARY -- {result.product.product_name} -> {result.region}: "
        f"{total} requirement{'s' if total != 1 else ''} found.",
        "This is sample data - a regulatory SME must sign off before anyone acts on it.",
        "",
    ]

    tier_titles = {
        0: "Act on now (existing - already in force)",
        1: "Track (emerging - has a compliance date)",
        2: "Monitor (emerging - no date yet)",
    }
    for tier in (0, 1, 2):
        items = tiers[tier]
        if not items:
            lines.append(f"{tier_titles[tier]}: none")
            continue
        counts: dict[str, int] = {}
        for _, _r, domain_key in items:
            counts[domain_key] = counts.get(domain_key, 0) + 1
        breakdown = ", ".join(
            f"{domain_label_by_key[key]} ({counts[key]})"
            for key, _ in DOMAIN_ORDER if key in counts
        )
        count_phrase = f"{len(items)} requirement{'s' if len(items) != 1 else ''}"
        if tier == 1:
            dates = sorted({r.must_comply_by for _, r, _ in items})
            date_note = f" - comply by {', '.join(dates)}" if len(dates) <= 3 else ""
            lines.append(f"{tier_titles[tier]}: {count_phrase} - {breakdown}{date_note}")
        else:
            lines.append(f"{tier_titles[tier]}: {count_phrase} - {breakdown}")

    lines.append("")
    if result.requested_domains:
        shown = ", ".join(
            label for key, label in DOMAIN_ORDER if key in result.requested_domains
        )
        lines.append(
            f"Coverage: this answer covers only {shown}, as asked - ask without naming "
            "a domain to see the full profile. The app tracks seven requirement domains "
            "in total (" + ", ".join(label for _, label in DOMAIN_ORDER) + ") - no "
            "cybersecurity-specific, radio-engineering detail, or full warranty legal "
            "text is tracked at all."
        )
    else:
        lines.append(
            "Coverage: " + ", ".join(label for _, label in DOMAIN_ORDER) + " only - no "
            "cybersecurity-specific, radio-engineering detail, or full warranty legal "
            "text is tracked here."
        )
    lines.append("")
    lines.append("See the table and full itemized report below for exact requirement text and citations.")
    return lines


# Short labels for the same three urgency tiers _urgency_tier() returns,
# sized to fit a table column (the summary block uses the longer,
# parenthetical form of these same three tiers).
TRACKING_STATUS_LABELS = {0: "Act on now", 1: "Track", 2: "Monitor"}


def _build_table_lines(flat: list) -> list[str]:
    """
    A compact, fixed-width "At a glance" table of only the short, comparable
    fields (row #, domain, tracking status, existing/emerging status,
    format, comply-by date), sorted by urgency tier and then by date.
    Deliberately excludes the requirement text and citation - those are full
    sentences that would have to be wrapped or truncated to fit a column,
    and truncating source text is exactly what Grounding Rule 2/3 rule out.
    The full text stays intact in the itemized report below, cross-referenced
    by the same row number.
    """
    domain_label_by_key = dict(DOMAIN_ORDER)

    def sort_key(item):
        n, r, _domain_key = item
        tier = _urgency_tier(r)
        date_key = r.must_comply_by if tier == 1 else ""
        return (tier, date_key, n)

    ordered = sorted(flat, key=sort_key)

    headers = ["#", "Domain", "Tracking Status", "Status", "Format", "Comply By"]
    rows = []
    for n, r, domain_key in ordered:
        rows.append([
            f"#{n}",
            domain_label_by_key[domain_key],
            TRACKING_STATUS_LABELS[_urgency_tier(r)],
            "Emerging" if r.status == "emerging" else "Existing",
            r.documentation_format.capitalize(),
            r.must_comply_by,
        ])

    widths = [
        max([len(headers[i])] + [len(row[i]) for row in rows])
        for i in range(len(headers))
    ]

    def fmt_row(cells):
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    lines = [
        "",
        "AT A GLANCE (sorted by urgency: act-on-now first, then nearest "
        "compliance date, then no-date-yet)",
        fmt_row(headers),
        fmt_row(["-" * w for w in widths]),
    ]
    lines.extend(fmt_row(row) for row in rows)
    return lines


def _scope_line(result: LookupResult) -> list[str]:
    """
    A one-line "Scoped to: ..." header addition when the question named
    specific domain(s), so it's visually obvious a report is a narrowed view
    rather than the full profile - the table/summary/itemized sections
    themselves already reflect the same narrowing via _active_domain_order().
    Empty list (nothing appended) when unscoped, so an unscoped report's
    header is byte-identical to before domain scoping existed.
    """
    if not result.requested_domains:
        return []
    domain_label_by_key = dict(DOMAIN_ORDER)
    scope_note = ", ".join(domain_label_by_key[d] for d in result.requested_domains)
    return [f"Scoped to: {scope_note} (ask without naming a domain for the full profile)"]


def at_a_glance(result: LookupResult) -> str:
    """
    Just the header line + the "At a glance" table, standing on its own.
    This exists so agent.py's natural-language path can print this exact,
    code-rendered block unconditionally, before handing the report to the
    LLM to phrase as prose - the table's position and figures are then
    guaranteed by code, never left to the model to reproduce. (The model
    isn't required to reproduce the table anyway - only the itemized
    requirements and citations are covered by Grounding Rule 2/5 - so this
    also removes an easy place for the two to drift apart.)
    Returns the same "Human review required." string format_result() would
    return for a failed lookup, since there is no table to show up front in
    that case.
    """
    if not result.ok:
        return f"\nHuman review required.\n\n{result.message}\n"

    flat = _flatten_ordered(result)
    lines = [
        f"\nCompliance requirements for: {result.product.product_name} "
        f"(SKU {result.product.sku}, RMN {result.product.rmn})",
        f"Category: {result.product.category}   Destination region: {result.region}",
    ]
    lines.extend(_scope_line(result))
    lines.append("=" * 78)
    lines.extend(_build_table_lines(flat))
    return "\n".join(lines)


def _summary_and_itemized_lines(result: LookupResult, flat: list) -> list[str]:
    """
    The urgency-bucketed summary and the full domain-grouped itemized report
    - everything format_result() shows *after* the At a glance table.
    Factored out so format_result_details() can reuse it without also
    rebuilding the header + table that at_a_glance() already renders on its
    own (see that function's docstring for why the two must stay separable).
    """
    by_domain: dict[str, list[tuple[int, "Requirement"]]] = {}
    for n, r, domain_key in flat:
        by_domain.setdefault(domain_key, []).append((n, r))

    lines = ["-" * 78]
    lines.extend(_build_summary_lines(result, flat))
    lines.append("\n" + "-" * 78)
    lines.append("FULL ITEMIZED REPORT (grouped by domain; row numbers match the table above)")
    for domain_key, domain_label in _active_domain_order(result):
        rows = by_domain.get(domain_key, [])
        lines.append(f"\n-- {domain_label} --")
        if not rows:
            lines.append("  (no requirements on file for this domain/region combination)")
            continue
        for n, r in rows:
            status_tag = (
                f"[EMERGING - must comply by {r.must_comply_by}]"
                if r.status == "emerging" else "[EXISTING]"
            )
            format_tag = f"[{r.documentation_format.upper()}]"
            lines.append(f"  [#{n}] {status_tag} {format_tag}")
            lines.append(f"    Requirement: {r.requirement}")
            lines.append(f"    Source: {r.citation_source}  (last verified: {r.last_verified})")
    lines.append("\n" + "=" * 78)
    lines.append(
        "This is a prototype built on a small sample dataset - it is NOT a substitute "
        "for sign-off from a regulatory subject-matter expert."
    )
    lines.append(
        "Grounding rule: if any requirements above read as conflicting, or you're "
        "unsure which one applies, treat that as a signal to escalate for human "
        "review (Grounding Rule 4) - this app does not attempt to resolve "
        "conflicting source data on its own."
    )
    return lines


def format_result(result: LookupResult) -> str:
    """
    Render a LookupResult as: an "At a glance" quick-scan table (top,
    urgency-sorted, tagged with tracking status), an urgency-bucketed
    summary, and the full itemized report - in that order. Nothing from the
    original domain-grouped, fully-cited report is dropped or shortened; the
    table and summary are additional views onto the same data, not a
    replacement for any of it. This is the complete, self-contained report -
    used as-is by the structured (non-LLM) path, and passed whole to
    llm_agent.phrase_answer() as VERIFIED_DATA so the model has the table
    available even though it is told not to reproduce it.
    """
    if not result.ok:
        return f"\nHuman review required.\n\n{result.message}\n"

    flat = _flatten_ordered(result)
    lines = [
        f"\nCompliance requirements for: {result.product.product_name} "
        f"(SKU {result.product.sku}, RMN {result.product.rmn})",
        f"Category: {result.product.category}   Destination region: {result.region}",
    ]
    lines.extend(_scope_line(result))
    lines.append("=" * 78)
    lines.extend(_build_table_lines(flat))
    lines.extend(_summary_and_itemized_lines(result, flat))
    return "\n".join(lines)


def format_result_details(result: LookupResult) -> str:
    """
    Same content as format_result(), minus the leading header + "At a
    glance" table. For agent.py's natural-language path, which already
    prints at_a_glance() verbatim before handing the report to the LLM -
    printing this afterward (instead of format_result()'s full text) shows
    the summary and full itemized report without the table appearing a
    second time in the same response. For a failed lookup there is no table
    to begin with, so this is identical to format_result().
    """
    if not result.ok:
        return format_result(result)
    flat = _flatten_ordered(result)
    return "\n".join(_summary_and_itemized_lines(result, flat))
