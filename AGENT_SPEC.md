# Agent Spec

A one-page definition of what this agent is, who it's for, and what it will
and won't do — with a pointer, for each item, to where that behavior is
actually stored and enforced in the code. Read `README.md` for setup and
`source_index.md` / `GROUNDING_RULES.md` for the material this spec depends
on; this file is the short version that ties Role/User/Job/Ground
Truth/Boundaries/Escalation together in one place.

---

### Role — what is this agent?

A deterministic compliance-requirements lookup tool for one narrow slice of
HP's product catalog, with an optional plain-English layer on top. It is a
class-project prototype, explicitly not a production tool and not HP's live
compliance system.

**Stored in:** `README.md`'s opening paragraph ("A terminal application
prototype for the HP/KME customer-discovery problem... This is a
class-project prototype, **not** a production tool and **not** HP's live
compliance system").
**Applied in:** `agent.py`'s `BANNER` constant prints the same framing on
every run. There is no runtime check that restricts use beyond this
disclosure — the boundary here is disclosed, not mechanically enforced.

### Intended User — who is it serving?

A stakeholder who needs a compliance answer for a specific product and
region — someone who needs the information, not someone qualified to
certify it themselves (that's who Human Escalation routes to instead).

**Stored in:** `README.md` ("a single place a stakeholder can query, by
product identifier, for the... compliance requirements that apply to a
product in a given region").
**Applied in:** nowhere more specific than this. "Stakeholder" is the only
persona ever named in this project — there's no named role, team, or
seniority level written down anywhere, and nothing in the code branches on
who's asking. **This is the one item in this spec that's under-specified**;
if a real persona (a program manager, a compliance analyst, a docs writer)
gets identified, it belongs here, and it would probably sharpen the Job and
Boundaries sections too — right now the app assumes its user can act on a
citation but can't independently verify the underlying regulation.

### Job — what task should it perform?

Given a product identifier (name, SKU, or RMN) and a destination region,
resolve the product to a category and return every on-file requirement for
that category/region, grouped by domain (environmental/sustainability,
safety/EMC/telecom, trade/customs, warranty documentation), each tagged
existing/emerging, print/online/either, and cited to its source. In
free-text mode, first turn a plain-English question into that same
identifier+region pair, then phrase the result back in prose without
changing any of it.

**Stored in:** `README.md`'s "How it works" section; `lookup.py`'s
module docstring ("Deterministic core of the Compliance Lookup Agent...
this is the part of the app that must never guess"); `llm_agent.py`'s
module docstring ("Nothing in here is allowed to invent compliance facts").
**Applied in:** `lookup.py`'s `run_lookup()` does the identifier → category →
requirements join; `agent.py`'s `structured_lookup()` and
`natural_language_lookup()` are the only two entry points that call it, so
every path through the app — menu-driven or free-text — ends up at the same
deterministic function.

### Ground Truth — what information should it trust?

Only `data/compliance_requirements.csv`, and only because that CSV is itself
sourced from the five approved documents in `source_index.md`'s
"Directly-cited sources" list, plus one methodology source that shaped the
schema. Nothing in `reference/` outside that cited set counts as ground
truth, and neither does general world knowledge.

**Stored in:** `source_index.md` in full (what each source is, its
date/version, and why it's trustworthy); Rule 1 of `GROUNDING_RULES.md`
("Use approved reference information when making decisions or
recommendations").
**Applied in:** `lookup.py`'s `COMPLIANCE_PATH` constant points at exactly
one file — there is no code path that reads anything else, so this
boundary is structural, not just a documented rule. `llm_agent.py`'s
`phrase_answer()` system prompt separately instructs the model that
`VERIFIED_DATA` (the deterministic lookup's output) is its only source of
facts.

### Boundaries — what should it not do?

No invented policies, facts, rules, or procedures beyond the dataset; no
guessing at coverage gaps; no reproducing full warranty legal text, HP
entity addresses, or phone numbers; no radio-engineering detail (frequency
bands, EIRP/power limits); no cybersecurity domain yet; no live scraping; no
fuzzy/semantic matching or translation — exact match only; no resolving
conflicting source data on its own; never implying compliance from an
absence of data.

**Stored in:** `README.md`'s "Does not cover (known gaps for a future
iteration)" list; Rules 2 and 3 of `GROUNDING_RULES.md` (no invented facts;
don't make up an answer when the reference is insufficient).
**Applied in:** the scope exclusions themselves are enforced by omission —
there's no code that does live scraping or fuzzy/translated matching. But
whether a free-text question *asks about* one of these excluded topics
(radio engineering detail, full warranty legal text, live scraping,
fuzzy/translated matching) is now actively detected, not just
silently unaddressed: `llm_agent.py`'s `detect_out_of_scope_topics()` is a
deterministic, keyword-only check (no model call) run by `extract_query()`
on every free-text question, and `agent.py`'s `natural_language_lookup()`
prints an explicit notice for any hit before showing whatever the seven
tracked domains do return - including on the path where the API call fails
outright. The no-invention rule is enforced in `llm_agent.py`'s two system
prompts (`extract_query()` won't invent a product or region the user didn't
write; `phrase_answer()` won't add a requirement beyond `VERIFIED_DATA`) and
in `lookup.py`'s `run_lookup()`, which returns an explicit result rather than
an empty or inferred one whenever a gap exists - surfaced to the stakeholder
as a plain "Human review required." headline plus the specific reason why,
never a silent empty answer.

### Human Escalation — when should it stop or request review?

Stop and point to a regulatory subject-matter expert (SME) whenever: the
product identifier doesn't match anything in the sample master; the region
isn't one of the four supported; a matched category/region combination has
zero requirements on file; or requirements ever read as contradictory. Even
on a clean "found" result, every output carries a standing reminder that
this is sample data requiring human sign-off before anyone acts on it —
escalation isn't reserved for failures alone.

**Stored in:** Rule 4 of `GROUNDING_RULES.md` ("Require human review when
the available information is insufficient or conflicting").
**Applied in:** all three coverage-gap messages in `lookup.py`'s
`run_lookup()` (unsupported region, unmatched product, zero requirements for
a category/region) name "Grounding Rule 4" explicitly and direct escalation
to a regulatory SME; `format_result()`'s footer adds the same reminder to
every successful result. `llm_agent.py`'s `phrase_answer()` system prompt
requires that direction to survive into the phrased prose rather than being
smoothed away, and requires a "not found" phrased answer to close with the
same human-review direction rather than resolving it itself.

---

## How these six sections relate to the other project docs

`source_index.md` answers "what's approved" (Ground Truth's source list).
`GROUNDING_RULES.md` answers "how the agent must behave with respect to
that material" (Rules 1–5, which this spec's Ground Truth / Boundaries /
Human Escalation sections draw on directly). This file, `AGENT_SPEC.md`,
is the layer above both: it names the agent's Role and Job in plain terms
and is the place a new contributor should start before reading the other
two.
