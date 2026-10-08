# Compliance Lookup Agent — Overview & End-to-End Workflow

## What it is

A class-project prototype for the HP/KME customer-discovery problem: one
place a stakeholder can ask "what compliance requirements apply to product
X in region Y?" and get a grounded, cited answer instead of digging through
spreadsheets and tribal knowledge. It is explicitly **not** HP's live
compliance system — the data model mirrors real HP WTR program artifacts,
but the content is a hand-authored, representative sample.

The core design principle: the agent never lets an LLM state a compliance
fact. A deterministic lookup against curated reference data produces every
fact; an LLM is used only to understand the question (extract a product
identifier/region/domain) and to phrase the final answer in plain English.
Five documented Grounding Rules enforce this — use only approved reference
data, never invent facts, never guess among ambiguous matches, escalate to
human review when information is missing or conflicting, and always cite
the source used.

## Architecture, in three layers

1. **`lookup.py`** — deterministic engine. Resolves a product identifier
   (name, SKU, or RMN) to its category via `product_master.csv`, then joins
   category + region + domain against `compliance_requirements.csv`. No
   LLM involved; same inputs always produce the same answer.
2. **`llm_agent.py`** — the optional plain-English layer (Claude API).
   Extracts the identifier/region/domain from a free-text question, then
   phrases the lookup's verified result into prose. It is instructed to
   treat the lookup's output as its only source of facts and never add to
   it.
3. **`agent.py` (CLI) / `app.py` (Flask, deployed on Render)** — the two
   front doors to the same engine. Both offer a structured lookup mode
   (enter identifier + region directly) and a natural-language "ask a
   question" mode; which one a session defaults to depends on whether an
   LLM API key is configured, but either is reachable at any time.

## Data model and coverage

`product_master.csv` is the identifier → category crosswalk (1,652 products
across 49 categories). `compliance_requirements.csv` is the actual knowledge
base, keyed by category + region + domain, tracking seven requirement
domains (environmental/sustainability, safety/EMC/telecom, hearing aid
compatibility, cybersecurity, battery safety, trade/customs, warranty
documentation) for 57 regions total: the original EU/UK, US, China, Taiwan;
a 27-country EMEA expansion (25 countries plus a Ghana/Rwanda gap-fill); 10
Americas countries (Argentina, Brazil, Canada, Chile, Colombia, Mexico,
Paraguay, Peru, Ecuador, Venezuela, Panama — the last two telecom-only);
and 15 APJ countries (Cambodia, India, Indonesia, South Korea, Malaysia,
Pakistan, Philippines, Sri Lanka, Thailand, Vietnam, Australia, Hong Kong,
Japan, New Zealand, Singapore) — each only in whichever domains the
underlying reference material actually supports. Coverage is uneven on
purpose and was expanded in two passes: a first pass, then a self-audit
against the same five approved workbooks that found real sourced content
the first pass had missed or under-scoped (safety_emc_telecom for 8 APJ
countries that pass said had no source; trade_customs for Argentina/Chile;
warranty for most of the Americas/APJ; 8 new regions; and several named
emerging regulations). `hearing_aid_compatibility` and `cybersecurity`
remain EU/UK/US/Taiwan/China-only everywhere. Gaps are deliberate and
disclosed, never silently guessed — per Grounding Rule 3.

## The end-to-end simulated business workflow

The project treats the agent as one participant in a larger business
process, not something running in isolation. `demo_full_business_process.py`
runs this live, end to end, with the project's real, unmodified code:

1. **Upstream source** — a compliance team (Trade Compliance, Regulatory
   Affairs, Warranty & Legal, etc.) adds a newly tracked requirement to its
   own mock system-of-record feed (`source_systems_integration/*.csv`) —
   standing in for HP's real PLM/ERP and each team's own tracking system.
2. **Weekly sync** — `scripts/sync_from_source_systems.py` pulls every
   team's feed into the single source of truth the live agent actually
   queries (`data/compliance_requirements.csv`), logging every run (even a
   no-op one) to `sync_log.csv` and backing up the prior data before
   overwriting it. It fails safe: an unreadable feed leaves existing,
   previously-verified data untouched rather than corrupting it.
3. **AI agent** — the real `agent.py` pipeline answers a live question
   both before and after the sync, demonstrating that the new requirement
   is invisible until synced and then correctly surfaced afterward.
4. **Human review** — a compliance SME reviews the agent's verified report
   and records an approval decision in `human_review_log.csv`. The agent
   surfaces information; it doesn't self-certify it.
5. **Final outcome** — the approved requirement is written into the
   product's actual documentation file under `product_documentation/`,
   closing the loop from a source system's change to shipped documentation.

This mirrors a realistic enterprise flow: distributed teams maintain their
own systems of record → a scheduled sync centralizes them → stakeholders get
one queryable, cited interface → a human still signs off before anything
becomes official documentation.

## Validation

Three scripted test scenarios (a normal lookup, an ambiguous/unsupported
input, and a corrupted upstream feed) plus a recorded usability test with a
real end user, whose feedback (confusion over the results table's status
vocabulary and a strong preference for the natural-language mode) is
tracked as open follow-up work rather than folded in silently.

## Known limitations

No translation/multi-language support (input and output are English
only) — product-identifier matching itself already tolerates partial
names, extra/out-of-order words, and small typos (`lookup.find_product_verbose`),
that part is not a gap. The results table's status terms (Act on now /
Existing / Monitor / Emerging) have no on-screen legend yet. Coverage
outside the original four regions is real but uneven: EMEA/Americas lack
battery safety, cybersecurity, and hearing-aid-compatibility data, and APJ
currently has trade/customs coverage only — because no reference source
yet covers those domains for those countries, not because of a shortcut —
disclosed in the app's output, not hidden.
