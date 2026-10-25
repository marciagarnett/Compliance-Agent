#!/usr/bin/env python3
"""
Compliance Lookup Agent (MVP) - terminal application.

Run it with:
    python agent.py

By default the app drops you straight into whichever mode makes sense: if a
Claude API key is configured, you can just type a question in plain English;
if not, it asks for a product identifier directly (structured mode). Type
'menu' at any prompt to see all four options explicitly (including the one
not currently the default), 'list' to see the sample products, or 'quit' to
exit.

Scope, data model, and known gaps are documented in README.md - read that
first if anything below is surprising. Short version: this is a prototype
covering the full active HP/Poly catalog sample (1,652 products, 49
categories - notebooks, desktops, displays, and Poly-brand audio/video
accessories). Regions covered are data-driven (see lookup.VALID_REGIONS) -
starting from EU/UK, US, China, and Taiwan, now expanded with a first
EMEA-region pass (Bluetooth Headset category only so far) - built on a
small sample dataset modeled on real HP WTR-program document structures.
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv

import activity_log
import lookup
import llm_agent

load_dotenv()  # reads .env if present; harmless if it doesn't exist

def _banner() -> str:
    # Regions line is built from lookup.VALID_REGIONS (itself derived from
    # data/compliance_requirements.csv - see lookup._discover_valid_regions)
    # rather than hardcoded, so it can never silently go stale again as
    # regions are added.
    regions_line = ", ".join(lookup.VALID_REGIONS)
    return f"""
==============================================================================
 Compliance Lookup Agent (MVP prototype)
==============================================================================
 Covers: full active HP/Poly catalog sample - 1,652 products, 49 categories
 Regions covered: {regions_line}
 Domains covered: environmental/sustainability, safety/EMC/telecom,
                  hearing aid compatibility, cybersecurity, battery safety,
                  trade/customs, warranty documentation
 This is a prototype on a small SAMPLE dataset - not HP's live compliance
 content. See README.md for full scope, sources, and known gaps.
 Note: region coverage varies by product category - not every domain/region
 combination has data for every category yet (an honest gap, not "nothing
 required"; the app will tell you when it hits one).
==============================================================================
"""

MENU = """
What would you like to do?
  1) Ask a question in plain English{llm_note}
  2) Structured lookup (enter product identifier, then region)
  3) List sample products in this prototype
  4) Back to the default prompt
> """

COMMANDS = {"quit", "exit", "q", "menu", "help", "options", "list", "products"}


def list_sample_products(products: list[lookup.Product]) -> None:
    print("\nSample products in this prototype (name / SKU / RMN):")
    for p in products:
        print(f"  - {p.product_name}  /  {p.sku}  /  {p.rmn}")
    print()


def _outcome_for(result: lookup.LookupResult) -> str:
    """
    Map a LookupResult to one of activity_log's four outcomes. An ambiguous
    product match (reason_code == "ambiguous_product") is a clarification
    situation - the asker needs to pick from a short list the system
    already showed them - not a case that needs a regulatory SME's
    judgment, so it gets its own CLARIFICATION bucket instead of being
    folded into HUMAN_REVIEW (see activity_log.py's module docstring).
    """
    if result.ok:
        return activity_log.COMPLETED
    if result.reason_code == "ambiguous_product":
        return activity_log.CLARIFICATION
    return activity_log.HUMAN_REVIEW


def _prompt_for_candidate(result: lookup.LookupResult, region, products, requirements,
                           requested_domains=None) -> lookup.LookupResult:
    """
    When run_lookup() couldn't resolve a single product but found
    plausible candidates (reason_code == "ambiguous_product"), ask once
    which one was meant and re-run the lookup with that exact name. This
    is a clarification question, not an escalation: the system already has
    enough information to ask a targeted follow-up, and resolving it needs
    the asker's answer, not a human reviewer's judgment.

    Returns the original result unchanged if there's nothing to clarify,
    or if the asker doesn't pick a valid option (blank input, or a number
    out of range) - one follow-up only, no retry loop, the same discipline
    the existing identifier/region follow-up above already uses.
    """
    if result.reason_code != "ambiguous_product" or not result.candidates:
        return result
    print("\nDid you mean one of these?")
    for i, name in enumerate(result.candidates, start=1):
        print(f"  {i}) {name}")
    choice = input("Enter a number, or press Enter to skip: ").strip()
    if not choice.isdigit():
        return result
    idx = int(choice)
    if not (1 <= idx <= len(result.candidates)):
        return result
    chosen = result.candidates[idx - 1]
    print(f"\n[Using '{chosen}' - re-running the lookup.]")
    return lookup.run_lookup(chosen, region, products, requirements,
                              requested_domains=requested_domains)


def structured_lookup(products, requirements, identifier: str | None = None) -> None:
    if identifier is None:
        identifier = input("Product identifier (name, SKU, or RMN): ").strip()
    region = input("Destination region (EU/UK, US, China, or Taiwan): ").strip()
    result = lookup.run_lookup(identifier, region, products, requirements)
    result = _prompt_for_candidate(result, region, products, requirements)
    activity_log.log_event(
        _outcome_for(result),
        mode="structured",
        identifier=identifier,
        region=region,
        reason=result.reason_code,
    )
    print(lookup.format_result(result))


def _print_out_of_scope_notice(hits: list[dict]) -> None:
    """
    Print an explicit notice for any topic detect_out_of_scope_topics() found
    outside the seven requirement domains this prototype tracks
    (environmental_sustainability, safety_emc_telecom,
    hearing_aid_compatibility, cybersecurity, battery_safety, trade_customs,
    warranty_documentation). Never blocks the lookup that follows - it's an
    additional notice, not a gate.
    """
    if not hits:
        return
    print(
        "\n[Heads up - this question also touches on something outside the "
        "seven requirement domains this prototype tracks (environmental_"
        "sustainability, safety_emc_telecom, hearing_aid_compatibility, "
        "cybersecurity, battery_safety, trade_customs, "
        "warranty_documentation):]"
    )
    for hit in hits:
        print(f"  - {hit['note']}")
    print(
        "[Any lookup result below only covers the seven tracked domains - "
        "that is not a claim the topic above doesn't apply, only that this "
        "prototype doesn't track it (Grounding Rule 3: this app will not "
        "guess).]\n"
    )


def natural_language_lookup(client, model, products, requirements, user_text: str | None = None) -> None:
    if user_text is None:
        user_text = input("Ask your question: ").strip()
    if not user_text:
        return

    extracted, extract_fail_reason = llm_agent.extract_query(client, model, user_text)
    if extracted is None:
        activity_log.log_event(activity_log.FAILED, mode="ask", reason=extract_fail_reason)
        _print_out_of_scope_notice(llm_agent.detect_out_of_scope_topics(user_text))
        print(
            "\n[Couldn't reach the Claude API to interpret that question, or the "
            "response couldn't be read. Falling back to structured entry for this "
            "query - your API key/network connection may need a check.]\n"
        )
        structured_lookup(products, requirements)
        return

    _print_out_of_scope_notice(extracted.get("out_of_scope_topics", []))

    identifier, region = extracted["identifier"], extracted["region"]
    if not identifier or not region:
        print(
            f"\n[Could not confidently identify both a product and a region in that "
            f"question (got identifier={identifier!r}, region={region!r}). "
            "Let's fill in the missing piece(s) directly.]\n"
        )
        if not identifier:
            identifier = input("Product identifier (name, SKU, or RMN): ").strip()
        if not region:
            region = input("Destination region (EU/UK, US, China, or Taiwan): ").strip()

    # Deterministic (no model judgment involved) - see
    # llm_agent.detect_requested_domains(). Empty means the question didn't
    # name a specific domain, so run_lookup() returns the full profile,
    # exactly as before domain scoping existed.
    requested_domains = extracted.get("requested_domains", [])
    if requested_domains:
        scope_note = ", ".join(
            label for key, label in lookup.DOMAIN_ORDER if key in requested_domains
        )
        print(
            f"\n[Scoping this answer to: {scope_note} - based on your question. Ask "
            "without naming a specific domain to see the full compliance profile for "
            "this product/region.]\n"
        )

    result = lookup.run_lookup(identifier, region, products, requirements,
                                requested_domains=requested_domains)
    result = _prompt_for_candidate(result, region, products, requirements, requested_domains)
    if result.ok:
        # Print the At a Glance table directly, verbatim, before the LLM
        # gets involved at all - its position is then guaranteed by code,
        # not by trusting the model to reproduce or preserve it.
        print(lookup.at_a_glance(result))
    # Still built from the complete report (table included) - phrase_answer()'s
    # system prompt refers to "the At a Glance table in VERIFIED_DATA" and
    # needs the full text to ground its answer in, even though it's told not
    # to reproduce the table itself.
    verified_report = lookup.format_result(result)

    phrased = llm_agent.phrase_answer(client, model, user_text, verified_report, result.ok)
    # The At a Glance table was already printed above for a successful
    # lookup, so only the rest of the report prints here - otherwise the
    # same table would appear twice in one response. For a failed lookup,
    # at_a_glance() was never printed, so details == verified_report.
    details = lookup.format_result_details(result)
    # Deterministic, application-level check of the model's own output
    # against the real citations and the required human-review sentinel -
    # never a model self-assessment. A phrased answer that fails this is
    # never shown, regardless of how confident or well-formed it reads.
    verified_ok = llm_agent.verify_phrased_answer(
        phrased, lookup.shown_citations(result), result.ok,
        lookup.shown_row_markers(result),
    )
    # One log entry per turn, fired here (after the full pipeline, not
    # right after run_lookup()) so it can reflect what the user actually
    # saw. A coverage gap (ok=False) still logs with its existing
    # reason_code; a found result logs COMPLETED either way, but with a
    # distinct reason when the friendly phrasing itself didn't make it to
    # the user - a phrasing/verification problem is not a compliance-data
    # problem, so it doesn't change the outcome bucket, only the reason.
    if not result.ok:
        phrase_reason = result.reason_code
    elif phrased is None:
        phrase_reason = "llm_phrase_failed"
    elif not verified_ok:
        phrase_reason = "verification_failed"
    else:
        phrase_reason = ""
    activity_log.log_event(
        _outcome_for(result),
        mode="ask",
        identifier=identifier,
        region=region,
        reason=phrase_reason,
    )
    if verified_ok:
        print("\n" + phrased)
        print("\n--- Verified source data (unedited) ---")
        print(details)
    elif phrased:
        print(
            "\n[The phrased summary didn't pass this app's check against the "
            "verified data (missing a citation, or missing the required "
            "human-review notice) - showing the verified lookup result "
            "directly.]"
        )
        print(details)
    else:
        print(
            "\n[Couldn't reach the Claude API to phrase a summary - showing the "
            "verified lookup result directly.]"
        )
        print(details)


def run_menu(client, model, products, requirements, llm_available) -> None:
    """The full, explicit 4-option menu - reachable any time by typing 'menu'."""
    llm_note = f" (using model: {model})" if llm_available else " (needs ANTHROPIC_API_KEY - not configured, option disabled)"
    while True:
        choice = input(MENU.format(llm_note=llm_note)).strip()
        if choice == "1":
            if not llm_available:
                print("\n[Plain-English mode needs an Anthropic API key - see README.md.]\n")
                continue
            natural_language_lookup(client, model, products, requirements)
        elif choice == "2":
            structured_lookup(products, requirements)
        elif choice == "3":
            list_sample_products(products)
        elif choice == "4":
            return
        else:
            print("\nPlease enter 1, 2, 3, or 4.\n")


def main() -> None:
    print(_banner())

    try:
        products = lookup.load_products()
        requirements = lookup.load_requirements()
    except Exception as e:
        # Fail closed: a missing file, an empty file, malformed/renamed
        # columns, bad encoding - whatever the cause, don't limp along on
        # partial or guessed data. Stop here with a clear message instead
        # of a raw traceback.
        activity_log.log_event(activity_log.FAILED, mode="startup", reason="data_load_failed")
        print(f"Could not load sample data files: {e}")
        sys.exit(1)

    client = llm_agent.get_client()
    model = llm_agent.DEFAULT_MODEL
    llm_available = client is not None

    if llm_available:
        default_mode = "ask"
        print(
            f"Plain-English mode is ready (model: {model}) and is the default below - "
            "just type your question and press Enter.\n"
            "Other commands, any time: 'menu' (see all options), 'list' (sample products), "
            "'quit' (exit).\n"
        )
    else:
        default_mode = "lookup"
        print(
            "No Anthropic API key detected (or the anthropic package isn't installed), so "
            "this run defaults to structured lookup below: type a product identifier and "
            "press Enter, then enter a region when asked.\n"
            "Other commands, any time: 'menu' (see all options), 'list' (sample products), "
            "'quit' (exit). See README.md for how to add a key and unlock plain-English mode.\n"
        )

    try:
        while True:
            label = "Ask your question" if default_mode == "ask" else "Product identifier (name, SKU, or RMN)"
            raw = input(f"\n{label} > ").strip()
            lowered = raw.lower()

            if lowered in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            if lowered in ("menu", "help", "options"):
                run_menu(client, model, products, requirements, llm_available)
                continue
            if lowered in ("list", "products"):
                list_sample_products(products)
                continue
            if not raw:
                continue

            if default_mode == "ask":
                natural_language_lookup(client, model, products, requirements, user_text=raw)
            else:
                structured_lookup(products, requirements, identifier=raw)
    except (EOFError, KeyboardInterrupt):
        # Ctrl+C, Ctrl+D, or piped input running out - exit cleanly instead
        # of a raw traceback. Covers input() calls made deeper in
        # run_menu()/structured_lookup()/natural_language_lookup() too,
        # since those exceptions propagate up to this same try/except.
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
