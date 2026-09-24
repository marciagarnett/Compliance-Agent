# Ground Truth Reference

This document merges `source_index.md` and `GROUNDING_RULES.md` into one
place, organized around four questions: which sources/rules were selected,
why they're appropriate, how the agent uses them, and what happens when
they're insufficient. It's a reader's map, not a new authority — if scope or
rules ever change, update `source_index.md` (source detail) and
`GROUNDING_RULES.md` (behavioral rules) first, since those two remain the
files the code and its comments cite by name, then refresh this summary to
match.

---

## 1. Sources selected, and why each is appropriate

Six documents in `reference/` are cited grounding for
`data/compliance_requirements.csv`. Five are cited per row (verified against
every `citation_source` value in the CSV); the sixth shaped the data model
itself rather than any one row.

**Source 1 — Regulatory Requirements Summary.xlsx.** Country-by-country
safety/EMC/energy/telecom regulations; feeds the `safety_emc_telecom` and
`environmental_sustainability` domains. Appropriate because it's the WTR
program's own canonical requirements summary, maintained by a named editor
and updated per country — not a secondary summary of the regulations.

**Source 2 — Machinery_ITE_Import_or_Importer_controls.xlsx.**
Country-by-country import/customs control matrix; feeds `trade_customs`.
Appropriate because dataset values are copied directly from its Y/N/n/a/D
matrix — a direct transcription, not an interpretation.

**Source 3 — WW_Content_Requirements_FY25_FINAL.xlsx.** Print-vs-electronic
delivery matrix for warranty/EULA/setup/user-guide content; feeds
`warranty_documentation`. Appropriate because each country's answer reflects
a named in-country legal team's sign-off, not a company-wide assumption.

**Source 4 — WW-long-form-QSG-content (2).xlsx.** Defines which compliance
statements belong in which Quick Start Guide document type. Used only to
determine which requirement *types* exist and where they belong, not copied
as legal text into any row. Appropriate because it comes directly from the
team that owns compliance documentation day-to-day.

**Source 5 — ER Roadmap_FY26Q3.pdf.** Roadmap of active and emerging
regulations; the sole source for every `status = emerging` row and its
`must_comply_by` dates. Appropriate because it's the most current
forward-looking view available, from the same WTR program as Source 1 — why
this prototype can support proactive planning, not just report what's
already in force.

**Source 6 — WTR Regulatory Manual.xlsx (methodology, not cited per row).**
Defines the `documentation_format` rules (print/online/either), including
when a QR code or web link may substitute for print. Appropriate because
it's the manual that directly defines those rules; no row cites it
individually because it shaped the schema, not any one country's answer.

Reviewed but not used as grounding (full detail in `source_index.md`):
ASCM Report_Poly (structural model only, no content copied), PULSAR/Radio
products summary (radio engineering detail — out of scope), Regulatory
SharePoint Links (a pointer, not content), the per-country warranty legal
text itself (Source 3 is about *whether* it's delivered print/electronic,
not its wording), the KME product master list (used only to confirm
category placement), and the GPCS Regs Forum deck (on-topic but not yet
mined — a candidate for a future update).

---

## 2. How the agent uses them

The agent never reads `reference/` or `source_index.md` at runtime — those
exist for a human reviewer. What it actually reads is
`data/compliance_requirements.csv` (and `product_master.csv` to resolve an
identifier to a category first), and only through `lookup.py`'s
`run_lookup()`, which Grounding Rule 1 names as "the only place that
produces requirement content." `llm_agent.py`'s `phrase_answer()` is
instructed to treat that lookup's already-verified output (`VERIFIED_DATA`)
as its only source of facts.

Two rules constrain what the agent is allowed to add on top of that data.
Rule 2 forbids inventing a policy, fact, or procedure not already in the
dataset: `extract_query()`'s system prompt refuses to invent a product or
region the user didn't mention, and `phrase_answer()`'s system prompt
forbids adding any requirement, policy, or procedure beyond what
`VERIFIED_DATA` contains. Rule 5 requires citing the source used: every
requirement `format_result()` prints carries its `citation_source` and
`last_verified` date, and `phrase_answer()` is required to preserve every
citation in its phrased answer. The one field without a per-row citation is
`documentation_format` itself, since it comes from Source 6's methodology
rather than any one row's answer.

---

## 3. What happens when they're insufficient

Three distinct gaps are handled, all under Rules 3 and 4:

**Coverage gaps** — an unsupported region, an unmatched product, or a
matched product/region with zero requirements on file. `run_lookup()`
returns `ok=False` with a fixed `reason_code`
(`unsupported_region` / `unmatched_product` / `zero_requirements_on_file`).
This is never rendered as "no requirements apply" — every such message
states the gap explicitly and directs the reader to escalate to a
regulatory SME. `phrase_answer()`'s system prompt requires its answer to
open with the literal line "Human review required." whenever the lookup
didn't succeed, and forbids softening a not-found result into an implication
of compliance.

**Out-of-scope topics** — a question touching something the four tracked
domains don't cover at all (cybersecurity as its own domain, radio
engineering detail, full warranty legal text, live scraping, fuzzy/
translated matching). This is checked by `detect_out_of_scope_topics()`, a
deterministic keyword match against README.md's "Does not cover" list — no
model call, so it can't guess. It runs on every free-text question (and
directly, if the extraction call itself fails) and prints an explicit notice
before any lookup result. It never blocks the lookup; it names the gap
alongside whatever the four tracked domains do return.

**Domain scoping** — related to the out-of-scope check above but distinct
from it, and not a form of insufficiency at all: when a question names one
or more of the four tracked domains specifically (e.g. "China RoHS
requirements"), `detect_requested_domains()` (same deterministic,
keyword-only discipline, no model judgment) narrows the answer to just
those domains. This is scoping, not omission — nothing about the domain(s)
actually asked about is dropped; only domains the question never raised are
left out of that one answer, and the answer says so plus how to see the
full profile. A question that names no domain is unaffected.

**Conflicting data** — not actively detected today. The sample dataset was
hand-checked when built and contains no contradictory rows, so this is
currently a standing disclaimer in `format_result()`'s footer rather than an
automated check: if a future, larger dataset ever produces contradictory
requirements, the instruction is to treat that as a human-review case, not
something the agent resolves on its own. This is the one open gap noted in
`GROUNDING_RULES.md`'s "Known limitation" section.

---

## Rule-to-code map

| Rule | What it requires | Enforced in |
|---|---|---|
| 1. Use approved reference only | Facts come only from `compliance_requirements.csv` | `lookup.py: run_lookup()`; `llm_agent.py: phrase_answer()` system prompt |
| 2. Don't invent facts/policy | No product, region, requirement, or policy beyond the dataset | `llm_agent.py: extract_query()`, `phrase_answer()` system prompts |
| 3. Don't guess when insufficient | Coverage gaps and out-of-scope topics are named, not papered over; domain-scoped questions narrow without omitting | `lookup.py: run_lookup()` non-`ok` branches, `_active_domain_order()`; `llm_agent.py: detect_out_of_scope_topics()`, `detect_requested_domains()` |
| 4. Require human review | "Human review required." on any not-found result; escalate-to-SME on every gap | `lookup.py: format_result()` / `at_a_glance()` footer; `phrase_answer()` system prompt |
| 5. Identify the source used | Every requirement carries its citation and last-verified date | `lookup.py: format_result()`; `phrase_answer()` system prompt |
