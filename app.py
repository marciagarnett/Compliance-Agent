#!/usr/bin/env python3
"""
Compliance Lookup Agent - web wrapper (for a hosted, remotely-testable demo).

This is a thin Flask layer on top of the SAME deterministic core the
terminal app uses - lookup.py and llm_agent.py are imported unchanged, not
reimplemented. Nothing about the grounding rules, the dataset, or the
lookup logic changes by being served over HTTP instead of a terminal.

The web app exposes a single mode: ask a question in plain English (POST
/ask). The structured identifier+region form was removed after user
testing showed people found the two side-by-side modes confusing, and
consistently preferred the plain-English answers anyway - see
deployment_checklist.md / test notes for the reasoning. agent.py (the CLI)
still exposes structured lookup directly, since that testing was specific
to the web UI.

WHAT THIS DOES NOT DO: it never reads reference/ or ground_truth.zip (the
real internal HP workbooks) - only data/product_master.csv and
data/compliance_requirements.csv, the same sample CSVs the CLI app reads.
Those two files, plus this script and the rest of the existing project
code, are the only things meant to be deployed/hosted; reference/ and
ground_truth.zip should stay local and out of git entirely (see
.gitignore).

Run locally with:  python app.py
Run in production with a real WSGI server, e.g.:  gunicorn app:app

Environment variables (all optional - see README.md / .env.example for the
two the CLI app already uses):
  ANTHROPIC_API_KEY   - required for the app to answer anything. Without
                        it, the page loads but the question box is
                        disabled, since there is no other query path left.
  ANTHROPIC_MODEL     - optional model override (see llm_agent.py).
  WEB_APP_USERNAME /
  WEB_APP_PASSWORD   - if BOTH are set, the whole app is gated behind HTTP
                        Basic Auth. Strongly recommended for any hosted demo
                        URL that isn't meant to be fully public, since
                        every question spends your Anthropic API key.
                        Leave both unset to run without a gate (fine for
                        purely local testing only).
  PORT                - what port to listen on when run directly with
                        `python app.py` (most hosts set this for you and
                        expect gunicorn to read it instead - see Procfile).
"""
from __future__ import annotations

import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, Response, render_template, request

import activity_log
import llm_agent
import lookup

load_dotenv()  # reads .env if present; harmless if it doesn't exist

app = Flask(__name__)

# Loaded once at process startup - both CSVs are small and read-only, so
# there's no reason to re-read them per request. If either fails to load,
# fail loudly at startup rather than serving a half-broken app (same
# fail-closed philosophy as agent.py's main()).
PRODUCTS = lookup.load_products()
REQUIREMENTS = lookup.load_requirements()

LLM_CLIENT = llm_agent.get_client()
LLM_MODEL = llm_agent.DEFAULT_MODEL
LLM_AVAILABLE = LLM_CLIENT is not None


def _require_basic_auth(f):
    """
    Optional HTTP Basic Auth gate. Only active when BOTH WEB_APP_USERNAME
    and WEB_APP_PASSWORD are set in the environment - otherwise every
    request passes through unchanged, so a purely local/dev run still works
    with zero extra setup.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        expected_user = os.environ.get("WEB_APP_USERNAME")
        expected_pass = os.environ.get("WEB_APP_PASSWORD")
        if not expected_user or not expected_pass:
            return f(*args, **kwargs)

        auth = request.authorization
        if not auth or auth.username != expected_user or auth.password != expected_pass:
            return Response(
                "Authentication required.", 401,
                {"WWW-Authenticate": 'Basic realm="Compliance Lookup Agent"'},
            )
        return f(*args, **kwargs)
    return wrapped


@app.route("/healthz")
def healthz():
    """Plain health check for whatever host/platform is running this."""
    return {"status": "ok", "products": len(PRODUCTS), "requirements": len(REQUIREMENTS)}


@app.route("/", methods=["GET"])
@_require_basic_auth
def index():
    return render_template(
        "index.html",
        llm_available=LLM_AVAILABLE,
        phrased=None,
        verified=None,
        heads_up=[],
        query=None,
    )


@app.route("/ask", methods=["POST"])
@_require_basic_auth
def ask():
    """
    Free-text lookup - mirrors agent.py's natural_language_lookup(), minus
    the terminal-only "confirm what I understood" back-and-forth (a single
    HTTP request can't pause mid-flight for that the way a terminal prompt
    can). Falls back to a clear message, never a crash, if the LLM layer
    isn't configured or a call fails - exactly like the CLI.
    """
    user_text = request.form.get("question", "").strip()
    if not user_text:
        return render_template(
            "index.html", llm_available=LLM_AVAILABLE,
            phrased=None, verified=None, heads_up=[], query=None,
        )

    if not LLM_AVAILABLE:
        report = "[Plain-English mode needs an Anthropic API key - see README.md.]"
        return render_template(
            "index.html", llm_available=LLM_AVAILABLE,
            phrased=report, verified=None, heads_up=[], query=user_text,
        )

    out_of_scope = llm_agent.detect_out_of_scope_topics(user_text)
    extracted, extract_fail_reason = llm_agent.extract_query(LLM_CLIENT, LLM_MODEL, user_text)

    if extracted is None:
        activity_log.log_event(activity_log.FAILED, mode="ask", reason=extract_fail_reason)
        report = (
            "[Couldn't reach the Claude API to interpret that question, or the "
            "response couldn't be read. Please resubmit your question - if this "
            "keeps happening, try rephrasing it to name both a product and a "
            "destination region explicitly.]"
        )
        heads_up = [h["note"] for h in out_of_scope] if out_of_scope else []
        return render_template(
            "index.html", llm_available=LLM_AVAILABLE,
            phrased=report, verified=None, heads_up=heads_up, query=user_text,
        )

    identifier = extracted["identifier"]
    region = extracted["region"]
    requested_domains = extracted.get("requested_domains", [])

    if not identifier or not region:
        # The CLI (agent.py) handles this by pausing and asking input()
        # directly - a single HTTP request can't do that. Give the asker
        # something concrete to resubmit with instead of a bare "couldn't
        # identify" dead end: resolve whatever identifier text WAS given
        # (even without a region - find_product_verbose() doesn't need
        # one) so a genuinely ambiguous product name still surfaces its
        # candidate list here, exactly as it would further down the
        # pipeline, and always list the supported regions when region is
        # the gap, since that list is fixed and free to offer.
        lines = []
        reason = "missing_identifier_or_region"
        product_candidates: list[str] = []
        if identifier:
            product, match_note, product_candidates = lookup.find_product_verbose(identifier, PRODUCTS)
            if product is not None:
                if match_note:
                    # A fallback (partial-name/word/fuzzy) match - say what
                    # was typed and what it resolved to, since they differ.
                    lines.append(f"I matched '{identifier}' to '{product.product_name}'. {match_note}")
                else:
                    # An exact match on name, SKU, or RMN - identifier and
                    # product.product_name may be byte-identical, so
                    # "matched X to X" would read strangely; just confirm it.
                    lines.append(f"I found an exact match for '{product.product_name}'.")
            elif product_candidates:
                reason = "ambiguous_product"
                lines.append(
                    f"'{identifier}' matches more than one sample product - did you "
                    "mean one of these?"
                )
                lines.extend(f"  - {c}" for c in product_candidates)
            else:
                lines.append(
                    f"I couldn't find a product matching '{identifier}' in the sample "
                    "dataset (checked name, SKU, and RMN)."
                )
        else:
            lines.append("I couldn't identify a product in that question.")

        if not region:
            lines.append(
                f"\nA destination region is also needed - supported regions: "
                f"{', '.join(lookup.VALID_REGIONS)}."
            )

        lines.append(
            "\nPlease ask again naming one exact product (name, SKU, or RMN from "
            "the list above if one was shown) and one of the supported regions."
        )
        report = "[" + "\n".join(lines) + "]"

        # Every path above ends in something concrete the asker can act on
        # (an exact match confirmed, a candidate list, or the fixed list of
        # supported regions) - that is a clarification question, not a
        # dead end, so it gets the same CLARIFICATION bucket an ambiguous
        # run_lookup() result does rather than FAILED (see activity_log.py).
        activity_log.log_event(
            activity_log.CLARIFICATION, mode="ask", identifier=identifier, region=region,
            reason=reason,
        )
        return render_template(
            "index.html", llm_available=LLM_AVAILABLE,
            phrased=report, verified=None, heads_up=[], query=user_text,
        )

    result = lookup.run_lookup(identifier, region, PRODUCTS, REQUIREMENTS,
                                requested_domains=requested_domains)
    # format_result() (table + summary + itemized report) is what
    # phrase_answer() reads to write the prose answer, so the model always
    # sees the full picture - but format_result_verified() (itemized report
    # only, no table/summary) is what's actually SHOWN beneath that answer.
    # User testing found the table needed a legend most people wouldn't
    # have, and the summary was redundant with the phrased answer above it;
    # the itemized report (with citations) was the part called genuinely
    # helpful, and it's also the only part that isn't LLM-generated.
    full_report = lookup.format_result(result)
    verified_report = lookup.format_result_verified(result)
    # Only meaningful when result.ok is False (ignored by phrase_answer()'s
    # prompt and verify_phrased_answer()'s check otherwise), but computed
    # unconditionally since it's cheap and both call sites need it below.
    not_ok_header = lookup.not_ok_header(result)
    phrased = llm_agent.phrase_answer(
        LLM_CLIENT, LLM_MODEL, user_text, full_report, result.ok, not_ok_header
    )

    heads_up = [hit["note"] for hit in extracted.get("out_of_scope_topics", out_of_scope)]
    # Same deterministic, application-level check agent.py's CLI path uses -
    # a phrased answer that drops a citation or the required human-review
    # sentinel is never shown, no matter how well-formed it reads.
    verified_ok = llm_agent.verify_phrased_answer(
        phrased, lookup.shown_citations(result), result.ok,
        lookup.shown_row_markers(result), not_ok_header,
    )
    phrase_call_failed = phrased is None  # captured before phrased is overwritten below
    if phrased and not verified_ok:
        phrased = (
            "[The phrased summary didn't pass this app's check against the "
            "verified data (missing a citation, or missing the required "
            "human-review notice) - showing the verified lookup result "
            "directly.]"
        )
    elif not phrased:
        phrased = (
            "[Couldn't reach the Claude API to phrase a summary - showing the "
            "verified lookup result directly.]"
        )

    # One log entry per completed lookup attempt on this route - there was
    # none at all here before this change, unlike agent.py's CLI path.
    # Fired after the full pipeline so it reflects what was actually
    # returned, not just whether the lookup matched.
    if not result.ok:
        phrase_reason = result.reason_code
    elif not verified_ok:
        phrase_reason = "llm_phrase_failed" if phrase_call_failed else "verification_failed"
    else:
        phrase_reason = ""
    # An ambiguous product match (several plausible candidates, no single
    # resolution) is a clarification situation, not an escalation - the
    # candidates are already listed in `phrased`/`verified_report` above,
    # and resolving it needs the asker to resubmit with one of those exact
    # names, not a regulatory SME's review. Logged as its own outcome so
    # it isn't counted the same as a genuine coverage gap.
    if result.ok:
        outcome = activity_log.COMPLETED
    elif result.reason_code == "ambiguous_product":
        outcome = activity_log.CLARIFICATION
    else:
        outcome = activity_log.HUMAN_REVIEW
    activity_log.log_event(
        outcome,
        mode="ask", identifier=identifier, region=region, reason=phrase_reason,
    )

    return render_template(
        "index.html", llm_available=LLM_AVAILABLE,
        phrased=phrased, verified=verified_report, heads_up=heads_up, query=user_text,
    )


if __name__ == "__main__":
    # Local/dev only - a real deployment should run this via gunicorn
    # (see Procfile), not Flask's built-in dev server.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
