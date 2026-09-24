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

import json
import os
import re
from typing import Optional

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


def _extract_json_object(text: str) -> Optional[dict]:
    """Best-effort pull of the first {...} JSON object out of a model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


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
    "fuzzy_or_translation": (
        ("translate", "translation", "fuzzy match", "similar product",
         "multi-language", "multilingual"),
        "Fuzzy/semantic product matching, translation, and multi-language "
        "output are explicitly out of scope - identifier lookup is exact-"
        "match only (see README.md 'Does not cover').",
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


def extract_query(client, model: str, user_text: str) -> Optional[dict]:
    """
    Ask the model to pull {"identifier": ..., "region": ...} out of free text,
    and separately run the deterministic detect_out_of_scope_topics() check
    (no model call) so a question can be flagged as touching an untracked
    topic even though the model itself never judges scope.
    Returns None (never raises to the caller) if the SDK call fails or the
    response can't be parsed - agent.py treats None as "fall back to manual
    entry", and in that branch calls detect_out_of_scope_topics() itself so
    the scope notice still shows up without the model's help.
    """
    system = (
        "You extract two fields from a user's question about product compliance "
        "requirements: 'identifier' (a product name, SKU, or RMN as the user wrote it "
        "- do not correct or guess spelling) and 'region' (the destination country/"
        "region as the user wrote it, e.g. 'Taiwan', 'the EU', 'UK', 'China', 'US'). "
        "Respond with ONLY a JSON object: {\"identifier\": \"...\", \"region\": \"...\"}. "
        "If either field is missing or unclear from the question, set it to an empty "
        "string. Do not invent a product or region that wasn't mentioned - only use "
        "what the user actually wrote (see GROUNDING_RULES.md, Rule 2: do not invent "
        "facts)."
    )
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user_text}],
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
        parsed = _extract_json_object(text)
        if not parsed:
            return None
        return {
            "identifier": str(parsed.get("identifier", "")).strip(),
            "region": str(parsed.get("region", "")).strip(),
            "out_of_scope_topics": detect_out_of_scope_topics(user_text),
            "requested_domains": detect_requested_domains(user_text),
        }
    except Exception:
        return None


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
        "stakeholder. This application follows five grounding rules (full text in "
        "GROUNDING_RULES.md) that govern everything you write here:\n"
        "1. Use approved reference information when making decisions or "
        "recommendations - your only source of facts is VERIFIED_DATA below, the "
        "already-fact-checked result of a deterministic lookup against this "
        "project's approved reference material.\n"
        "2. Do not invent organizational policies, facts, rules, or procedures. "
        "Nothing you write may introduce a requirement, policy, or procedure that "
        "isn't already stated in VERIFIED_DATA.\n"
        "3. If the reference does not contain enough information, do not make up "
        "an answer or action. If VERIFIED_DATA reports 'not found' or a coverage "
        "gap, say so plainly - never imply the product is compliant, that nothing "
        "is required, or that a gap means it's safe to proceed.\n"
        "4. Require human review when the available information is insufficient "
        "or conflicting. When found is False, your answer MUST open with the "
        "exact line 'Human review required.' on its own, then a blank line, "
        "then a plain explanation of why - drawn only from VERIFIED_DATA's "
        "message, never invented or reworded away from what it actually says. "
        "Preserve every escalate-to-a-regulatory-SME notice in VERIFIED_DATA "
        "exactly as written. This prototype does not attempt to resolve "
        "conflicting source data automatically - if VERIFIED_DATA ever contains "
        "requirements that read as contradictory, open with that same 'Human "
        "review required.' line and flag the conflict explicitly as a "
        "human-review case rather than picking one.\n"
        "5. When practical, identify which approved source or rule was used. "
        "Every citation ('Source: ...') in VERIFIED_DATA must still appear in your "
        "answer, attached to the requirement it supports.\n\n"
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
        "still be present, with its full original wording, in your answer."
    )
    user_msg = (
        f"The user's original question was: {user_text!r}\n\n"
        f"VERIFIED_DATA (found={found}):\n{verified_report}"
    )
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1200,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text").strip()
    except Exception:
        return None
