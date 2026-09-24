# Grounding Rules

These are the rules this agent follows when it looks up, phrases, or presents
compliance information. They apply to both the deterministic lookup
(`lookup.py`) and the optional plain-English layer on top of it
(`llm_agent.py`). Read `README.md` and `source_index.md` first for what
"approved reference" means in this project — this file is about *how* the
agent is required to behave with respect to that material, not what the
material is.

---

### 1. Use approved reference information when making decisions or recommendations.

Every requirement the agent states must come from `data/compliance_requirements.csv`,
which is itself sourced only from the documents named in `source_index.md`'s
"Directly-cited sources" section. The agent does not draw on general
knowledge about compliance, HP, or regulations when answering a lookup — only
on this project's approved dataset.

**Where this is enforced:** `lookup.py`'s `run_lookup()` is the only place
that produces requirement content, and it only ever reads
`data/compliance_requirements.csv`. `llm_agent.py`'s `phrase_answer()` system
prompt states this as its first rule and is instructed to treat
`VERIFIED_DATA` as its only source of facts.

### 2. Do not invent organizational policies, facts, rules, or procedures.

If a requirement, policy, or procedure isn't already in the approved dataset,
the agent must not state it, imply it, or fill the gap with a plausible-
sounding guess — including in the free-text mode's friendlier phrasing.

**Where this is enforced:** `llm_agent.py`'s `extract_query()` system prompt
already refuses to invent a product or region the user didn't mention;
`phrase_answer()`'s system prompt explicitly forbids adding any requirement,
policy, or procedure beyond what `VERIFIED_DATA` contains.

### 3. If the reference does not contain enough information, do not make up an answer or action.

A missing product, an unsupported region, or a category/region combination
with no requirements on file are coverage gaps, not "no requirements apply."
The agent states this distinction explicitly every time, rather than staying
silent about the gap or letting an absence of data read as a clean bill of
compliance.

**Where this is enforced:** every non-`ok` branch of `lookup.py`'s
`run_lookup()` (unsupported region, unmatched product, zero requirements
found) is rendered by `format_result()`/`at_a_glance()` as a simple
"Human review required." headline followed by a message that names the gap
and says so is not a "nothing required" answer. `llm_agent.py`'s
`phrase_answer()` system prompt requires its own phrased answer to open with
that same "Human review required." line whenever the lookup did not
succeed, and separately instructs the model not to soften a "not found"
result into an implication of compliance.

A related but distinct gap - a question asking about something outside the
seven requirement domains this app tracks at all (radio engineering detail,
full warranty legal text, live scraping, fuzzy/translated matching) - is
caught before the lookup even runs.
`llm_agent.py`'s `detect_out_of_scope_topics()` is a deterministic,
keyword-only check (no model call) against exactly the list in README.md's
"Does not cover" section; `extract_query()` runs it on every free-text
question and returns the hits alongside the extracted identifier/region, and
`agent.py`'s `natural_language_lookup()` prints an explicit notice for any
hit - via the same path if the API call fails outright - before showing
whatever the seven tracked domains do return. It never blocks the lookup;
it just names the gap instead of leaving it silently unaddressed.

Separate from that gap - and not a case of "not enough information" at all -
is domain *scoping*: when a free-text question names one or more of the
seven tracked domains specifically (e.g. "China RoHS requirements" names
environmental_sustainability), the answer is narrowed to just those domains
rather than always returning the full seven-domain profile. This is
deliberately not treated as omission under this rule: nothing the reference
contains about the domain(s) actually asked about is dropped, softened, or
summarized away - only domains the question never raised are left out of
that specific answer, and the answer says so and says how to see the full
profile. **Where this is enforced:** `llm_agent.py`'s
`detect_requested_domains()` is a deterministic, keyword-only check (no
model call, same discipline as the out-of-scope check above) that
`extract_query()` runs on every free-text question; `lookup.py`'s
`run_lookup()` accepts the result as `requested_domains`, evaluates the
zero-requirements gap against just that subset, and `_active_domain_order()`
is what every rendering function (`at_a_glance()`, `format_result()`,
`format_result_details()`) derives its per-domain output from, so a scoped
answer's table, summary, and itemized report all narrow consistently. An
unscoped question (no domain named) is unaffected - full seven-domain profile,
exactly as before this existed.

### 4. Require human review when the available information is insufficient or conflicting.

Every coverage-gap message in `lookup.py` ends by directing the stakeholder
to escalate to a regulatory subject-matter expert (SME) for human review,
rather than treating the gap as resolved. `format_result()`'s footer carries
the same requirement for results that *are* found — this is a prototype on
sample data, and human sign-off is still required before anyone acts on it.

This prototype does not currently attempt to detect or resolve *conflicting*
source data (the sample dataset doesn't contain contradictory rows to
resolve), but the same human-review requirement is written into the footer:
if requirements ever read as contradictory, that is a signal to escalate, not
a case for the agent to adjudicate on its own.

**Where this is enforced:** `lookup.py`'s coverage-gap messages and
`format_result()`'s footer; `llm_agent.py`'s `phrase_answer()` system prompt
requires every escalation notice to be preserved and, for "not found"
results, requires the phrased answer to close with the same human-review
direction.

### 5. When practical, identify which approved source or rule was used.

Every requirement row in the dataset carries a `citation_source` naming the
exact source file (and, where applicable, tab or section) it came from, plus
a `last_verified` date. `format_result()` prints both under every
requirement it shows. The one exception is the `documentation_format` field
itself (print/online/either) — it isn't cited per row because it comes from
a single methodology source (`source_index.md` Source 6) that shaped the
schema rather than any one row's answer, and that's noted there.

**Where this is enforced:** `lookup.py`'s `format_result()` prints the
citation and last-verified date for every requirement; `llm_agent.py`'s
`phrase_answer()` system prompt requires every citation in `VERIFIED_DATA` to
still appear in the phrased answer.

---

## Known limitation

Rule 4's "conflicting" case is handled today only as a standing disclaimer,
not as active detection — the app does not scan for rows that contradict
each other. That's an acceptable gap for this MVP's small, curated sample
dataset (each category/region/domain combination was hand-checked when the
CSV was built), but it's a real gap if this project ever ingests larger or
less-curated data: a next iteration would need an actual conflict-detection
pass before this rule can be called fully automated rather than
disclaimer-only.
