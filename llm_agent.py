"""
Thin, optional natural-language layer on top of lookup.py.

Nothing in here is allowed to invent compliance facts. Its two jobs are:
  1. turn a free-text question into {identifier, region} for the deterministic
     lookup in lookup.py to resolve, and
  2. turn the deterministic lookup's *already-verified* result into friendlier
     prose, without adding, dropping, or altering any requirement, tag, date,
     or citation.

If the Anthropic SDK isn't installed, or no API key is configured, or a call
fails for any reason (bad key, no network, rate limit), every function here
returns None/raises a handled exception and agent.py falls back to the plain
structured (non-LLM) flow. The app must keep working either way.
"""
from __future__ import annotations

import os
from typing import Optional

import grounding

try:
    import anthropic  # type: ignore
    ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    ANTHROPIC_SDK_AVAILABLE = False

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def get_client():
    """Return an anthropic.Anthropic client if the SDK is installed and a key is set, else None."""
    if not ANTHROPIC_SDK_AVAILABLE:
        return None
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


# Forced tool-use schema for extract_query() - the model must call this tool
# and the Anthropic SDK returns schema-validated arguments directly, so
# there is no free-text JSON to regex out of a reply and no way for a
# malformed response to look like a parse failure caused by something else
# (a stray brace in prose, a markdown fence, a clarifying aside). A failure
# here is either the model declining the tool call or the SDK call itself
# raising - both handled the same way, as "couldn't extract", below.
EXTRACT_QUERY_TOOL = {
    "name": "extract_compliance_query",
    "description": (
        "Record the product identifier and destination region found in the "
        "user's question about compliance requirements, exactly as the user "
        "wrote them."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "identifier": {
                "type": "string",
                "description": (
                    "The product name, SKU, or RMN exactly as the user wrote "
                    "it - do not correct or guess spelling. Empty string if "
                    "the question doesn't name a product."
                ),
            },
            "region": {
                "type": "string",
                "description": (
                    "The destination country/region exactly as the user "
                    "wrote it, e.g. 'Taiwan', 'the EU', 'UK', 'China', 'US'. "
                    "Empty string if the question doesn't name one."
                ),
            },
        },
        "required": ["identifier", "region"],
    },
}


# The seven requirement domains lookup.py actually tracks, and a deterministic,
# keyword-only check (no model call, so it can never "guess" - Grounding Rule 3)
# for whether a free-text question also touches something outside all seven.
# Every entry here is taken straight from README.md's own "Does not cover"
# list, so this check can't drift from what the dataset covers without that
# doc also being updated (Grounding Rule 2: don't invent scope either way).
OUT_OF_SCOPE_TOPICS: dict[str, tuple[tuple[str, ...], str]] = {
    "radio_engineering_detail": (
        ("frequency band", "channel plan", "eirp", "power limit", "rf power",
         "radio frequency", "transmit power"),
        "Radio engineering detail (specific frequency bands, channel plans, "
        "or EIRP/power limits) is explicitly out of scope for this prototype "
        "(see README.md 'Does not cover').",
    ),
    "full_warranty_legal_text": (
        ("warranty text", "legal text", "entity address", "entity name",
         "phone number", "support number", "support phone"),
        "Full warranty legal text, HP entity names/addresses, or support "
        "phone numbers are explicitly out of scope - this prototype cites "
        "the source document instead of reproducing them (see README.md "
        "'Does not cover').",
    ),
    "live_scraping": (
        ("scrape", "scraping", "crawl", "crawling"),
        "This prototype never scrapes live government/regulatory websites - "
        "everything it knows is a static, hand-curated sample (see "
        "README.md 'Does not cover').",
    ),
    "translation_or_multilang": (
        ("translate", "translation", "multi-language", "multilingual"),
        "Translation and multi-language output are explicitly out of scope - "
        "input and output are English only (see README.md 'Does not "
        "cover'). Product-identifier matching itself does tolerate a "
        "partial name, extra/out-of-order words, and small typos (see "
        "lookup.py's find_product_verbose()) - that part is supported, not "
        "out of scope.",
    ),
}


# Deterministic (no model call) keyword hints for narrowing a free-text
# question to one or more of the seven requirement domains lookup.py tracks.
# These keys must match lookup.py's DOMAIN_ORDER keys exactly. Kept
# keyword-based, not judged by the model, for the same reason
# OUT_OF_SCOPE_TOPICS is: the app decides what counts as a domain match, not
# the model's own semantic judgment (Grounding Rule 3 - never guess).
DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "environmental_sustainability": (
        "rohs", "weee", "hazardous substance", "environmental", "sustainability",
        "energy label", "energy efficiency", "battery directive", "packaging",
        "recycl",
    ),
    "safety_emc_telecom": (
        "emc", "telecom", "ncc statement", "ncc", "type-approval", "type approval",
        "safety certification", "safety cert", "certification mark",
    ),
    "hearing_aid_compatibility": (
        "hearing aid", "hac", "accessibility", "accessible",
    ),
    "cybersecurity": (
        "cybersecurity", "cyber security", "cyber-security", "cyber resilience",
        "cra", "iot labeling", "iot labelling", "cyber trust mark",
    ),
    "battery_safety": (
        "battery safety", "un38.3", "un 38.3", "62133", "lithium battery",
        "battery transport", "power bank",
    ),
    "trade_customs": (
        "trade", "customs", "import control", "importer", "duty", "tariff",
    ),
    "warranty_documentation": (
        "warranty", "eula", "user guide", "setup instructions", "quick start guide", "qsg",
    ),
}

# Canonical order, matching lookup.py's DOMAIN_ORDER keys (duplicated here,
# not imported, for the same reason OUT_OF_SCOPE_TOPICS duplicates README's
# list rather than parsing it - this file has no dependency on lookup.py).
_DOMAIN_KEY_ORDER = (
    "environmental_sustainability", "safety_emc_telecom",
    "hearing_aid_compatibility", "cybersecurity", "battery_safety",
    "trade_customs", "warranty_documentation",
)


def detect_requested_domains(user_text: str) -> list[str]:
    """
    Deterministic, keyword-only check (no model call) for whether a
    free-text question names one or more of the seven requirement domains
    specifically - e.g. "China RoHS requirements" names
    environmental_sustainability. Returns matched domain keys in canonical
    order, empty if nothing matched. An empty result means "no domain named"
    - lookup.py then returns the full seven-domain profile, exactly as
    before this domain narrowing existed; that is intentional, not a fallback failure - a
    question that doesn't name a domain hasn't asked to be narrowed.
    A question can match more than one domain (e.g. "customs and warranty
    requirements") - both are then shown, and only those two.
    """
    lowered = user_text.lower()
    return [
        domain for domain in _DOMAIN_KEY_ORDER
        if any(kw in lowered for kw in DOMAIN_KEYWORDS[domain])
    ]


def detect_out_of_scope_topics(user_text: str) -> list[dict]:
    """
    Deterministic, keyword-only check (no model call) for whether a free-text
    question touches a topic this prototype explicitly does not cover, per
    README.md's "Does not cover" list. Returns a list of
    {"topic": ..., "note": ...} dicts, empty if nothing matched. This never
    blocks or alters a lookup - it's an additional notice attached to the
    answer, not a gate on it (Grounding Rule 4 is about escalating on
    insufficient/conflicting data, not about refusing to run a lookup).
    """
    lowered = user_text.lower()
    hits = []
    for topic, (keywords, note) in OUT_OF_SCOPE_TOPICS.items():
        if any(kw in lowered for kw in keywords):
            hits.append({"topic": topic, "note": note})
    return hits


def extract_query(client, model: str, user_text: str) -> tuple[Optional[dict], str]:
    """
    Ask the model to call the extract_compliance_query tool (forced via
    tool_choice) to record {identifier, region} from the user's question,
    and separately run the deterministic detect_out_of_scope_topics() check
    (no model call) so a question can be flagged as touching an untracked
    topic even though the model itself never judges scope.

    Returns (result, reason) - never raises to the caller:
      - On success: (the parsed dict, "").
      - On failure: (None, reason), where reason is "tool_not_called" (the
        model's response didn't include a call to extract_compliance_query -
        shouldn't happen under a forced tool_choice, but handled rather than
        assumed away) or "sdk_call_failed" (the API call itself raised - no
        network, bad/revoked key, rate limit, timeout, etc. - the exact
        cause isn't distinguished further, but "the call never completed"
        is now distinguishable from "the model didn't do what was asked").
    This replaces a single generic None that collapsed both failure modes
    together; callers now get a reason_code-shaped signal of why, the same
    pattern lookup.LookupResult already uses for its own ok/reason_code
    pairing. agent.py/app.py treat result is None as "fall back to manual
    entry" exactly as before, and in that branch call
    detect_out_of_scope_topics() themselves so the scope notice still shows
    up without the model's help; reason is new, and is only used for more
    specific activity-log entries.
    """
    system = (
        "You extract fields from a user's question about product compliance "
        "requirements by calling the extract_compliance_query tool - do not "
        "correct or guess spelling on either field, and leave a field empty "
        "if the question doesn't name it.\n\n"
        "Grounding rule that governs this task (full rule list and rationale "
        "in GROUNDING_RULES.md):\n"
        f"{grounding.render_rules([2])}\n"
        "Concretely: do not invent a product or region that wasn't mentioned - "
        "only use what the user actually wrote."
    )
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=200,
            system=system,
            tools=[EXTRACT_QUERY_TOOL],
            tool_choice={"type": "tool", "name": "extract_compliance_query"},
            messages=[{"role": "user", "content": user_text}],
        )
        tool_use = next(
            (block for block in resp.content
             if getattr(block, "type", "") == "tool_use"
             and getattr(block, "name", "") == "extract_compliance_query"),
            None,
        )
        if tool_use is None:
            return None, "tool_not_called"
        parsed = tool_use.input  # already a dict, schema-validated by the API
        result = {
            "identifier": str(parsed.get("identifier", "")).strip(),
            "region": str(parsed.get("region", "")).strip(),
            "out_of_scope_topics": detect_out_of_scope_topics(user_text),
            "requested_domains": detect_requested_domains(user_text),
        }
        return result, ""
    except Exception:
        return None, "sdk_call_failed"


def phrase_answer(client, model: str, user_text: str, verified_report: str, found: bool) -> Optional[str]:
    """
    Turn the deterministic, already-verified report into friendlier prose.
    The model is explicitly told not to add or change any factual content -
    every requirement, tag, date, and citation in `verified_report` must
    still appear, unchanged, somewhere in the output.
    Returns None if the call fails; agent.py just prints verified_report alone then.
    """
    system = (
        "You are presenting the result of a compliance-requirements lookup to a "
        "stakeholder. This application follows five grounding rules (full rule "
        "list and rationale in GROUNDING_RULES.md):\n"
        f"{grounding.render_rules([1, 2, 3, 4, 5])}\n\n"
        "Concretely, for this task:\n"
        "1. Your only source of facts is VERIFIED_DATA below, the already-fact-"
        "checked result of a deterministic lookup against this project's "
        "approved reference material.\n"
        "2. Nothing you write may introduce a requirement, policy, or procedure "
        "that isn't already stated in VERIFIED_DATA.\n"
        "3. If VERIFIED_DATA reports 'not found' or a coverage gap, say so "
        "plainly - never imply the product is compliant, that nothing is "
        "required, or that a gap means it's safe to proceed.\n"
        "4. When found is False, your answer MUST open with the exact line "
        "'Human review required.' on its own, then a blank line, then a plain "
        "explanation of why - drawn only from VERIFIED_DATA's message, never "
        "invented or reworded away from what it actually says. Preserve every "
        "escalate-to-a-regulatory-SME notice in VERIFIED_DATA exactly as "
        "written. This prototype does not attempt to resolve conflicting "
        "source data automatically - if VERIFIED_DATA ever contains "
        "requirements that read as contradictory, open with that same 'Human "
        "review required.' line and flag the conflict explicitly as a "
        "human-review case rather than picking one.\n"
        "5. Every citation ('Source: ...') in VERIFIED_DATA must still appear "
        "in your answer, attached to the requirement it supports.\n\n"
        "Formatting: the At a Glance table in VERIFIED_DATA (row numbers, "
        "domain, tracking status, existing/emerging status, format, and "
        "comply-by date) has already been printed to the user, verbatim and "
        "unedited, immediately before your response - do not reproduce or "
        "re-summarize that table yourself. Your job is a short friendly "
        "framing sentence plus prose covering the SUMMARY section and the "
        "full itemized report that follow it in VERIFIED_DATA. You may add "
        "light structure, but you must NOT omit, summarize away, soften, or "
        "add any requirement, status tag ([EXISTING]/[EMERGING]), "
        "documentation-format tag ([PRINT]/[ONLINE]/[EITHER]), date, or "
        "citation. Every requirement and citation in VERIFIED_DATA must "
        "still be present, with its full original wording, in your answer. "
        "Each requirement in VERIFIED_DATA is tagged with a row marker like "
        "'[#3]' - reproduce that exact marker, unchanged, immediately before "
        "the requirement it tags, for every requirement you include (the "
        "same marker the At a Glance table's row numbers already use, so a "
        "reader can match your prose back to that table). If you are ever "
        "at risk of running out of space before covering every requirement, "
        "write shorter framing prose rather than dropping a requirement - "
        "every requirement and its marker must appear."
    )
    user_msg = (
        f"The user's original question was: {user_text!r}\n\n"
        f"VERIFIED_DATA (found={found}):\n{verified_report}"
    )
    try:
        # 3000, not 1200: a real run on a 12-requirement product was
        # observed truncating mid-report at the 1200-token cap (markdown
        # headers/bold/rules cost noticeably more tokens than the plain
        # report being paraphrased) - verify_phrased_answer()'s row-marker
        # check below is the actual safety net against a truncated or
        # otherwise incomplete answer reaching the user, but there is no
        # reason to make truncation likely in normal use when raising this
        # is this cheap.
        resp = client.messages.create(
            model=model,
            max_tokens=3000,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text").strip()
    except Exception:
        return None


def verify_phrased_answer(
    phrased: Optional[str],
    citations: list[str],
    found: bool,
    row_markers: Optional[list[str]] = None,
) -> bool:
    """
    Deterministic (no model call) check of phrase_answer()'s own output
    against the facts it was supposed to preserve. This is an application-
    level decision rule, not a model self-assessment - the Iteration 3
    harness design's point on this (see AGENT_SPEC.md / the harness design
    doc) is that whether a phrased answer is acceptable must be decided by
    code checking the model's output against known facts, never by asking
    the model to confirm its own compliance.

    Checks, in order:
      1. `phrased` must be non-empty.
      2. If `found` is False, `phrased` must open with the exact sentinel
         line "Human review required." - the one requirement
         phrase_answer()'s system prompt places on a not-found/coverage-gap
         result (Grounding Rule 4).
      3. Every string in `citations` (pass lookup.shown_citations(result))
         must appear verbatim somewhere in `phrased` - nothing the report
         cited may be dropped when the model rephrases it (Grounding
         Rule 5).
      4. Every marker in `row_markers` (pass lookup.shown_row_markers(result))
         must appear verbatim somewhere in `phrased`. This exists because
         check 3 alone has a real, observed gap: a live run truncated a
         12-requirement answer after requirement #10, yet still passed
         check 3, because #10/#11/#12 all cited the same source document -
         the one citation string that survived the cutoff (from #10) was
         enough to satisfy "every citation appears," even though two whole
         requirements were silently missing. Row markers are one-per-
         requirement (lookup.shown_row_markers()), so a dropped requirement
         is always a missing marker, even when its citation isn't unique.
         `row_markers` defaults to None/empty, which skips this check -
         for callers that haven't been updated to pass it, this behaves
         exactly as it did before this check was added.

    Returns False on any failure. The caller's job on False is to not show
    `phrased` to the user and fall back to the verified report instead -
    the exact same fallback agent.py/app.py already use when
    phrase_answer() itself returns None, so this adds a new REASON to take
    that branch, not a new branch.
    """
    if not phrased:
        return False
    if not found and not phrased.startswith("Human review required."):
        return False
    if not all(citation in phrased for citation in citations if citation):
        return False
    return all(marker in phrased for marker in (row_markers or []) if marker)
