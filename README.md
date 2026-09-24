# Compliance Lookup Agent (MVP prototype)

A terminal application prototype for the HP/KME customer-discovery problem: a
single place a stakeholder can query, by product identifier, for the
environmental, sustainability, regulatory, trade, and warranty compliance
requirements that apply to a product in a given region — with citations, a
clear existing-vs-emerging flag, and whether the requirement must appear in
print, online, or either.

This is a class-project prototype, **not** a production tool and **not**
HP's live compliance system.

## What's real vs. sample here

The dataset's *structure* (columns, domains, the existing/emerging split, the
print/online/either distinction) is modeled directly on real HP Worldwide
Technical Regulations (WTR) program artifacts. Those artifacts are the
project's **approved reference material** — the actual files live in
[`reference/`](./reference/), and [`source_index.md`](./source_index.md)
catalogs each one: what it is, its date/version, and why the agent may trust
it as a grounding source. Read that file before touching the data model.

This project also follows five explicit grounding rules: use approved
reference information for decisions/recommendations, never invent
organizational policies/facts/rules/procedures, don't guess when the
reference is insufficient, require human review when information is
insufficient or conflicting, and cite the approved source used when
practical. The full rules, and a note on where each is enforced in the code,
are in [`GROUNDING_RULES.md`](./GROUNDING_RULES.md). [`AGENT_SPEC.md`](./AGENT_SPEC.md) is the one-page version of all of this - Role, Intended User, Job, Ground Truth, Boundaries, and Human Escalation, each with a pointer to where it's stored and enforced in the code. Start there if you're new to this project.

The actual *content* in `data/compliance_requirements.csv` — the specific
requirement wording, dates, and citations — is a small hand-authored **sample**
written to be representative of those documents, not extracted from HP's live,
complete compliance database. `build_data.py` authored the original 48 rows,
scoped to the `Bluetooth Headset` category only; `build_compliance_requirements_v2.py`
is the follow-up script that expanded that sample to cover the full 49-category
catalog and the three new domains below, while carrying the original 48 rows
forward unchanged. Both scripts are kept in this folder for transparency into
how each row was authored, not because either is part of the running app.

## Scope

**Product catalog:** `data/product_master.csv` covers the full active HP
catalog it could be built from real KME/ASCM data - 1,652 products across
49 categories: Poly-brand audio/video (Bluetooth Headset, Wired Headset,
Video Conferencing, Phone, and 28 others; see `build_product_master.py`) and
notebooks, desktops, workstations, thin clients, retail/RPOS systems, and
displays (Consumer Notebook, Commercial Notebook, Commercial Desktop,
Display, and 17 others; see `build_product_master_kme.py`). The second
source's identifiers are weaker than the first's throughout - most of its
sheets are KME's own documentation-*program* tracking, not a finished-goods
parts catalog, so `sku` is frequently a wildcarded product-family pattern
(e.g. `24-cr0xxx`) rather than one orderable part number, or (253 rows) an
internal `PROJ-<code>` fallback where no such pattern exists at all; `rmn`
values on those rows can also repeat across clearly unrelated products.
Both build scripts document every judgment call in full - read them before
trusting a specific identifier field for something other than the demo.

**Compliance coverage now matches the full catalog** -
every one of the 49 categories in `data/product_master.csv` has at least one
compliance row on file (verified by `build_compliance_requirements_v2.py`'s
own sanity check, which fails loudly if a catalog category is ever left
unclassified). The 48 original `Bluetooth Headset` rows are still the only
ones hand-authored one requirement at a time; the other 48 categories are
generated from a smaller set of **category archetypes** - groups of
categories that share the same real, checkable properties (does the category
actually contain a radio, is it battery-powered, is it worn against the ear,
does it have its own network/OS stack) - because the underlying source
material (see `source_index.md`) is itself organized generically across
product categories, not per HP product line, for four of the five approved
workbooks. `build_compliance_requirements_v2.py`'s module docstring explains
this in full, including the specific evidence behind every category's
classification.

This does **not** mean every category/region/domain combination has a row -
a category can legitimately have zero rows in a domain that doesn't apply to
it (a passive accessory like a cushion has no `safety_emc_telecom` rows,
because it contains no active electronics to certify) or in a domain the
underlying source material simply doesn't cover for that category with
enough confidence to state a requirement (e.g. `hearing_aid_compatibility`
has no China rows - see "Domains" below). Both are honest gaps surfaced the
same way as any other missing data, per Grounding Rule 3 - never read as
"nothing required."

**A name-lookup caveat carried forward from the catalog build:** many
notebook/desktop/display product names are shared marketing family names
across several distinct configurations (e.g. several different real products
are all named "HP 14"). `find_product()` does an exact, first-match lookup -
searching by one of these shared names silently returns whichever matching
row happens to come first in `product_master.csv`, not necessarily the
specific configuration meant. Searching by the specific Model Number/SKU
avoids the ambiguity.

**Regions and domains:** four regions (EU/UK, US, China, Taiwan), and seven
requirement domains: the original `environmental_sustainability` and
`safety_emc_telecom`, plus three added alongside the catalog expansion -
`hearing_aid_compatibility` (telecom-terminal accessibility rules for
devices worn against or held to the ear), `cybersecurity` (network-connected/
"digital element" product regulation - the EU Cyber Resilience Act, the US
IoT Labeling "Cyber Trust Mark" program, Taiwan's new cybersecurity
regulation), and `battery_safety` (transport/safety/traceability rules for
products that ship with a battery - UN38.3, IEC 62133-2, the EU Battery
Regulation, China's Mobile Power Bank traceability rule, Taiwan's draft BSMI
Battery Standard) - and the original `trade_customs` and
`warranty_documentation`. A handful of rows in the three new domains cite a
real external regulation directly (e.g. "FCC 47 CFR Section 20.19") rather
than one of the five project workbooks, because those specific topics aren't
covered at row level by any of the five - `source_index.md` documents this
distinction and lists every such citation.

**Does not cover (known gaps for a future iteration):**
- Full warranty legal text, HP entity names/addresses, or support phone
  numbers — the real source document for this is far more extensive than an
  MVP warrants; this app cites it instead of reproducing it.
- Radio engineering detail — specific frequency bands, channel plans, or
  EIRP/power limits.
- Any live scraping of government/regulatory websites — everything here is a
  static, hand-curated sample.
- Fuzzy or semantic product matching, translation, or multi-language output —
  identifier lookup is exact-match only (case-insensitive).
- Any UI beyond this terminal application.

## How it works

`lookup.py` is the deterministic core: it loads the two CSVs in `data/`,
resolves a product identifier (name, SKU, or RMN — exact match) to a product
category, and joins that against the compliance requirements table for the
requested region. It never guesses — if a product, region, or combination
isn't in the sample data, it says so plainly instead of implying "no
requirements apply."

`llm_agent.py` is an optional layer on top, using the Claude API, that lets
you type a question in plain English (e.g. *"What do I need for a Poly
Voyager Focus 2 shipping to Taiwan?"*) instead of filling in two prompts. The
model itself only does two things: (1) pull the product identifier and
region out of your sentence, handing them straight to the same deterministic
lookup above, and (2) rephrase the lookup's already-verified result into
friendlier prose — it's explicitly instructed not to add, drop, or soften
any requirement, tag, date, or citation, and the raw verified data is always
printed underneath the phrased answer so you can check it directly.

Two more checks run alongside the model, deterministically (no model
judgment involved, so they can't drift or guess): a keyword check for
questions that touch something outside the seven tracked domains entirely
(see "Does not cover" below), and a keyword check for whether the question
names one or more of the seven tracked domains specifically (e.g. "China
RoHS requirements") — if it does, the answer is narrowed to just those
domains instead of the full seven-domain profile, and says so. A question
that doesn't name a domain gets the full profile, exactly as before this
existed.

**The app works fully without an API key** — you just get the structured
(product + region prompt) mode instead of the free-text mode. If a Claude API
call ever fails (bad key, no network, rate limit), the app catches it and
falls back to structured entry for that one query rather than crashing.

**Default mode:** on startup, the app picks the best default automatically —
if an API key is configured, it drops you straight into plain-English mode
(just type a question); if not, it drops you into structured mode (type a
product identifier, then a region). Either way, typing `menu` at any prompt
brings up the full 4-option menu (including whichever mode isn't the current
default), `list` shows the sample products, and `quit` exits.

## Setup

**1. Install Python dependencies** (Python 3.10+ recommended):

```
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**2. (Optional) Enable the plain-English mode** by adding a Claude API key:

1. Go to <https://console.anthropic.com>, sign in or create an account.
2. Open **Settings > API Keys** and create a new key.
3. In this folder, copy `.env.example` to a new file named `.env`.
4. Open `.env` and replace `your-key-here` with the key you just created.

`.env` is already listed in `.gitignore` and is never read by anything except
your own machine — don't share it or commit it. If you skip this step
entirely, the app still runs; it just defaults to structured mode instead of
plain-English mode (see "Default mode" above).

**3. Run it:**

```
python agent.py
```

## Files in this folder

| File | Purpose |
|---|---|
| `agent.py` | Entry point — run this. The terminal menu/loop. |
| `lookup.py` | Deterministic lookup core (no network calls). |
| `llm_agent.py` | Optional Claude-API layer for free-text queries. |
| `data/product_master.csv` | Sample product identifier → category crosswalk. |
| `data/compliance_requirements.csv` | Sample compliance knowledge base. |
| `build_data.py` | The original script that authored the Bluetooth Headset-only CSV (kept for transparency, not run by the app). |
| `build_compliance_requirements_v2.py` | The follow-up script that expanded the CSV to the full 49-category catalog and three new domains (kept for transparency, not run by the app). |
| `test_queries.md` | Manual verification test cases. |
| `requirements.txt` | Python dependencies. |
| `.env.example` | Template for your own `.env` — copy it, don't edit it in place. |
| `source_index.md` | Index of the approved reference material this project is grounded on. |
| `reference/` | The actual reference documents `source_index.md` describes. |
| `GROUNDING_RULES.md` | The five grounding rules this agent follows, and where each is enforced in the code. |
| `AGENT_SPEC.md` | One-page Role/User/Job/Ground Truth/Boundaries/Escalation definition, with pointers into the code. |
| `activity_log.py` | Basic append-only logger - one line per lookup attempt. |
| `activity_log.txt` | The log itself (created on first run, not checked in - see `.gitignore`). |

## Logging

Every lookup attempt - structured or free-text - appends one line to
`activity_log.txt`, a plain-text file created next to `agent.py` on first
run. Each line records only:

- **outcome** - `COMPLETED` (a real result was found), `HUMAN_REVIEW` (a
  coverage gap - unsupported region, unmatched product, or zero
  requirements on file - routed the query to Grounding Rule 4 instead of
  guessing), or `FAILED` (the app itself broke - the sample data wouldn't
  load, or the Claude API call failed) - see `AGENT_SPEC.md`'s Human
  Escalation section for what each of these means.
- **mode** - `structured`, `ask`, or `startup`.
- **identifier** / **region** - the resolved product identifier and region,
  when there were any.
- **reason** - a short, fixed label (e.g. `unmatched_product`), never a
  full sentence.

What it deliberately does **not** store: the user's raw free-text question
(it could contain anything they happened to type), the full lookup message
or citation text (already available in the CSV and in `GROUNDING_RULES.md`),
the Anthropic API key, or exception details/stack traces. The log exists to
answer "did this run complete, need a human, or fail" at a glance - not to
duplicate the app's own data or capture anything beyond that.

## Known limitations to call out in a demo or writeup

- This is a sample dataset covering every category in the sample catalog
  across four regions — it is not a claim about HP's actual, complete
  compliance obligations, and a handful of category/region/domain
  combinations are deliberately left with zero rows where the reviewed
  source material didn't support a confident claim (see "Scope" above).
- The free-text mode's *understanding* of a question depends on the Claude
  API; its *facts* never do — they always come from the same CSV the
  structured mode reads.
- No automated update pipeline exists yet; a next iteration would need one to
  keep `must_comply_by` dates and citations current as the real WTR content
  changes.
