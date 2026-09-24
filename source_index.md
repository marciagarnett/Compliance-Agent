# Source Index

This file catalogs the reference material actually present in
[`reference/`](./reference/), right next to this index, so anyone reviewing the
project can open the real source next to the claim that cites it — and can
also see everything that was reviewed but didn't end up in the dataset,
without guessing what's in the folder.

**Why this exists:** the whole premise of this project is that compliance
information shouldn't live in scattered spreadsheets and tribal knowledge — so
the project's own reference material shouldn't either. Every requirement in
`data/compliance_requirements.csv` names a source in its `citation_source`
column; this index is where that name resolves to an actual file, what that
file is, and why it's trustworthy enough to build sample data from.

**Scope note:** this is a class-project prototype. These are real internal HP
documents (or structured to match them), used to make the *sample* dataset
realistic — the index below describes those source documents themselves, not
a claim that `data/compliance_requirements.csv` is HP's live, complete
compliance database. See `README.md` for that distinction.

---

## Directly-cited sources

These five documents are named, by filename, in the `citation_source` column of
`data/compliance_requirements.csv` — the original 48 Bluetooth Headset rows
(authored by `build_data.py`) all trace back to one of these five. The
catalog-wide expansion (`build_compliance_requirements_v2.py`, see
README.md) reuses these same five sources for the `environmental_sustainability`,
`safety_emc_telecom`, `trade_customs`, and `warranty_documentation` domains,
and for the `cybersecurity`/`battery_safety` rows that ER Roadmap_FY26Q3.pdf
(Source 5) already tracks at category-icon level. A smaller number of rows in
the three new domains cite a real external regulation directly instead - see
"Directly-cited external regulations (new domains)" below for why and what.

### Source 1

**Name:** Regulatory Requirements Summary.xlsx
**Purpose:** Country-by-country summary of safety, EMC, energy, and telecom
regulations — regulator, applicable standard, must-comply-by date, the
certification or requirement itself, and whether label/manual content is
affected. This is the primary source for the `safety_emc_telecom` and
`environmental_sustainability` domains.
**Date/Version:** Internal revision history tracked on its own "Revision
history" tab; individual country rows carry their own "Date of country change."
**Source:** Internal HP Worldwide Technical Regulations (WTR) program document.
The file's own header marks it "Internal Use Only – HP Confidential."
**Why the agent may trust it:** it's the WTR team's own canonical
requirements summary — the team whose job is specifically to track these
regulations — maintained by a named document editor and updated per country,
not a secondary or informal summary of the regulations.

### Source 2

**Name:** Machinery_ITE_Import_or_Importer_controls.xlsx
**Purpose:** Country-by-country import/customs control matrix — whether
approval must be held in the importer's own name, and whether customs review
includes a technical-regulations check, broken out by Safety/EMC/Energy/
Telecom. This is the source for the `trade_customs` domain.
**Date/Version:** Includes its own "Revision History" tab.
**Source:** Internal HP trade-compliance / import-controls working file.
**Why the agent may trust it:** values in the dataset are copied directly
from this file's Y/N/n/a/D matrix rather than inferred or estimated — it's a
direct transcription, not an interpretation.

### Source 3

**Name:** WW_Content_Requirements_FY25_FINAL.xlsx
**Purpose:** Country-by-country matrix of whether Warranty, HP EULA, Setup
Instructions, and User Guide content must be delivered electronically or in
print, tracked separately for consumer vs. commercial customers, with legal
review comments. This is the source for the `warranty_documentation` domain.
**Date/Version:** "FY25_FINAL" (fiscal-year-25 final version); individual
country rows carry their own legal-approval dates (e.g., one row notes "Legal
approved elimination of printed warranty on 6/23/23").
**Source:** Internal HP document, explicitly reviewed and filled in by named
in-country legal teams (see its own "Instructions for legal reviews" tab).
**Why the agent may trust it:** each country's answer reflects a specific
legal team's sign-off for that jurisdiction, not a general company-wide
assumption applied everywhere.

### Source 4

**Name:** WW-long-form-QSG-content (2).xlsx
**Purpose:** Defines HP's compliance-content taxonomy for product Quick
Start Guides — which statements (RoHS variants, WEEE, EU/UK DoC, EU RED
graphic, NCC statement, IEEE 802.11x note, EAC logo, etc.) belong in which
document type (long-form QSG, safety insert, radio-compliance insert), and
whether each is product-specific or generic.
**Date/Version:** Working file as provided; no separate revision-history tab.
**Source:** Internal HP Knowledge Management & Enablement (KME) working
file — provided as an example of the team's current content-requirements
matrix.
**Why the agent may trust it:** it comes directly from the team that owns
compliance documentation day-to-day; it was used only to determine which
requirement *types* exist and which document they belong in, not copied as
legal text into any row.

### Source 5

**Name:** ER Roadmap_FY26Q3.pdf
**Purpose:** Executive dashboard and roadmap of active and emerging
regulatory requirements worldwide — total counts, market/domain breakdowns,
and a timeline of specific emerging regulations with effective dates and
impact ratings. This is the sole source for every row in the dataset marked
`status = emerging`, including its `must_comply_by` dates.
**Date/Version:** FY26 Q3 (actuals through end of July), dated August 2026.
Authored by Dorcas Tan.
**Source:** Internal HP WTR program executive report, marked "HP
Confidential."
**Why the agent may trust it:** it's the most current forward-looking view
available on this topic, produced by the same WTR program that owns Source 1
— it's why this prototype can claim to support *proactive* compliance
planning rather than only reporting what's already in force.

---

## Directly-cited external regulations (new domains)

`hearing_aid_compatibility` and part of `battery_safety` are not covered at
row level by any of the five sources above - only `environmental_sustainability`,
`safety_emc_telecom`, `trade_customs`, `warranty_documentation`, and the
`cybersecurity`/`battery_safety` items ER Roadmap_FY26Q3.pdf already flags at
category-icon level (the China Mobile Power Bank rule and Taiwan's draft BSMI
Battery Standard, both of which already existed, un-domained, in the original
Bluetooth Headset dataset before these domains existed) are. Rather than
inventing a fake worksheet reference for the rest, the rows below cite the
real, publicly-documented regulation directly. These are well-established,
named regulations (not sample/invented content) - the *sample* part of this
dataset is which categories were judged to be in scope for each, not whether
the regulation itself is real:

- **Regulation (EU) 2023/1542** (EU Battery Regulation) - battery_safety, EU/UK.
- **UN Manual of Tests and Criteria, Part III Subsection 38.3** (UN38.3
  lithium-battery transport testing) - battery_safety, all regions with a
  battery-equipped category.
- **IEC 62133-2** (portable lithium cell/pack safety) - battery_safety, US.
- **FCC 47 CFR Section 20.19** (Hearing Aid Compatibility) - hearing_aid_compatibility, US.
- **RED 2014/53/EU Article 3(3)(f) and EN 301 406** (radio equipment
  accessibility) - hearing_aid_compatibility, EU/UK (radio-bearing ear-coupled
  categories only).
- **Directive (EU) 2019/882** (European Accessibility Act) - hearing_aid_compatibility, EU/UK.
- **Taiwan NCC telecommunications terminal equipment accessibility technical
  regulations** - hearing_aid_compatibility, Taiwan.
- **Regulation (EU) 2024/2847** (EU Cyber Resilience Act) - cybersecurity, EU/UK.

**China is deliberately left with zero `hearing_aid_compatibility` rows** -
no accessibility-specific regulation for ear-coupled telecom equipment could
be verified against this project's approved reference material or a citable
public source with enough confidence to state a requirement. This is a real
coverage gap, not a claim that no such requirement exists (Grounding Rule 3
applies to how this dataset gets built, not only to how it gets queried).

---

## Methodology source (informs the data model, not cited per row)

### Source 6

**Name:** WTR Regulatory Manual.xlsx
**Purpose:** Defines documentation-*format* rules — whether a requirement is
for certification purposes, must be part of a regulatory submittal package,
requires localization, and whether it may be delivered as printed hardcopy,
on a device's integrated display/control panel, via QR code, on the web, or
on an HDD.
**Date/Version:** "last regular update: 1/5/2024" per its own Manual Guide
tab; its Energy Efficiency tab is dated separately.
**Source:** Internal HP WTR program manual, maintained by a named document
editor.
**Why the agent may trust it:** this file is *why* the dataset has a
`documentation_format` (print / online / either) field at all, and why
`either` is reserved specifically for cases where a QR code or web link is
allowed in place of print — that rule came directly from this manual. No
single dataset row cites it individually because it shaped the schema
itself, not any one country's answer.

---

## Source for data/product_master.csv (whole-file, not per-row citation_source)

`data/product_master.csv` doesn't have its own `citation_source` column - a
product's category is looked up by name/SKU, not individually cited the way
each compliance requirement row is - so its provenance is tracked here at
the file level instead.

### Source 7

**Name:** ASCM Report_Poly_2026-09-09.xlsx
**Purpose:** HP's real ASCM (product master) export for the Poly product
lines [BR, NG, NL, NJ] - one row per SKU per localized variant, with
category, part number (Base PN), AMO descriptions, and GA/End-of-Sales/
End-of-Manufacturing lifecycle dates. This is the direct source for every
row in `data/product_master.csv` beyond the original 7 hand-picked samples.
**Date/Version:** Exported 2026-09-09 20:44 UTC (per the file's own header
row); 2,244 rows across 31 categories as exported.
**Source:** Internal HP ASCM export.
**Why the agent may trust it:** it's a live system-of-record export (part
numbers, UPCs, real lifecycle dates), not a curated or hand-typed summary -
`build_product_master.py` documents exactly which rows were kept, dropped,
or split into a new category (see that script's docstring for the full
methodology, including the Bluetooth-vs-wired headset split and why RMN is
left blank for every row sourced from this file).

---

## Source for data/product_master.csv, part 2: non-Poly HP product lines

### Source 8

**Name:** HP Products under KME .xlsx
**Purpose:** Internal KME (Knowledge Management & Enablement) tracker of HP
product *documentation programs* by product line - notebooks, desktops,
workstations, thin clients, retail/RPOS systems, and displays - plus the
"Poly" tab (still excluded; see below). Most sheets are project/program
tracking (codenames, ODM contacts, doc-kit part numbers, code-freeze/GA
dates), not a finished-goods parts catalog the way ASCM was for Poly - only
one sheet ("AMO WOR's without kits") is a real parts list with orderable
part numbers. This is the source for every non-Poly row in
`data/product_master.csv`.
**Date/Version:** Working KME tracker as provided; no separate revision-
history tab; individual programs carry their own code-freeze/GA/EOP dates.
**Source:** Internal HP KME working file.
**Why the agent may trust it, and where it falls short:** it's the KME
team's own live tracker, not a secondary summary - but per an explicit
project decision, several fields are populated in this dataset despite
being a materially weaker fit than the equivalent ASCM fields were for
Poly:
- `sku` is the sheet's own "Model Number" column where one exists, which is
  frequently a **wildcarded family pattern** (e.g. "24-cr0xxx",
  "GT16-0xxx, GT16-000") covering many actual configurations rather than one
  orderable part - not a true SKU. Where no Model Number column exists at
  all, `sku` instead falls back to `PROJ-<internal project code>` (253 of
  the added rows) - an internal codename, weaker still, and not separately
  confirmed as acceptable the way the Model Number fallback was.
- `rmn` is populated from a column literally named "RMN" (or "Regulatory
  Model") on the sheets that have one, even though the same value
  frequently repeats across clearly unrelated products (e.g. one desktop
  RMN value spans an All-in-One, an Envy, and two different OMEN gaming
  towers) - RMN lookup on a shared value resolves to whichever product this
  project's build script happened to list first, not necessarily the one
  asked about.
- The "Poly" tab (unreleased-product roadmap - project codenames, no SKU)
  remains excluded, same as before this source was added for its other
  sheets.
- All five Display sheets are collapsed into one "Display" category, since
  none of them have compliance data yet to differentiate on.

See `build_product_master_kme.py`'s docstring for the full extraction
methodology and per-sheet column mapping.

---

## Present in reference/ but not cited (reviewed, not grounding)

These documents are physically present in `reference/` alongside the cited
sources above, and were reviewed while scoping this project, but **no row in
`data/compliance_requirements.csv` cites any of them.** Listed here so this
index matches what's actually in the folder, and so the record of what was
considered — and why it didn't become grounding — stays honest and complete.

- **PULSAR MasterCountryList-5G and 6E_WTR.xlsx** and **Radio products
  summary.xlsx** — radio engineering detail (frequency bands, EIRP/power
  limits). Explicitly out of scope for this prototype (see README.md).
- **Regulatory SharePoint Links.docx** — a pointer to HP's internal
  SharePoint portal, not itself a source of regulatory content.
- **WW_Country-Specific Warranty Text_FY25_FINAL.docx** — the actual
  per-country legal warranty text. Its existence is what Source 3's
  print/electronic findings are about, but its legal language itself is
  never reproduced and no dataset row cites it directly.
- **Iteration-0_Part-1_ISAN5318_MarciaGarnett.pdf** — the customer-discovery
  and problem-definition writeup for this project. It's the reason this
  project exists, not a compliance-content source.
- **GPCS Regs Forum 12, 13 August.pptx** — 77-slide deck from HP's "Global
  Product Compliance / Sustainability Packaging Regulatory Forum" (12–13
  August 2026, presented by Jacob Gulick, Carlos Madrigal, and Jesus Perez;
  marked "HP Private, Confidential for Internal Use Only"). Covers HazCom
  regulatory initiatives and the EU Packaging and Packaging Waste Regulation
  (PPWR) in detail — manufacturer obligations, Declarations of Conformity,
  "placed on the market" timing, and packaging design/substance-restriction
  requirements, several noted as "Enforced 12 August 2026." Its subject
  matter falls inside the `environmental_sustainability` domain this
  prototype already covers, but no dataset row draws from it yet — reviewed
  and logged here rather than worked into the sample data for this pass. A
  reasonable candidate to mine for a future update (see "How to add a new
  source" below), since it's dated, named, and squarely on-topic.

---

## Project process documents (not compliance sources)

These files are also in `reference/`, but they aren't HP compliance material
at all — they're this project's own build history, kept for the same
transparency reason `build_data.py` is kept (see README.md): so anyone
reviewing the project can see how the AI build was directed, not because the
running app reads them.

- **implementation_prompt.md** — the original build brief handed to the
  agent that built this prototype. Scoped to two requirement domains
  (environmental/sustainability and regulatory/EMC only), with no
  existing/emerging status or print/online/either distinction.
- **implementation_prompt_revised.md** and
  **implementation_prompt_revised_final.md** (identical content) — the
  revised brief that actually directed this build. It expands scope to the
  four requirement domains, `status` (existing/emerging), and
  `documentation_format` (print/online/either) fields the dataset and app
  now have, and adds the trade/customs and warranty-documentation domains
  using Sources 2 and 3 above. This is the operative brief;
  `implementation_prompt.md` is kept only to show the scope grew from an
  earlier draft.

---

## How to add a new source

1. Get the document approved the same way the six above were (an internal,
   named, dated document from the team that actually owns that domain — not
   a summary of a summary).
2. Copy the file into `reference/` (or confirm it's already there — check
   the "Present in reference/ but not cited" section above first, since a
   file may already be in the folder waiting to be promoted).
3. Add a `### Source N` entry above with the same five fields: Name, Purpose,
   Date/Version, Source, and Why the agent may trust it.
4. Only then update `data/compliance_requirements.csv` rows to cite it in
   `citation_source`.
