#!/usr/bin/env python3
"""
Compliance Lookup Agent - web wrapper (for a hosted, remotely-testable demo).

This is a thin Flask layer on top of the SAME deterministic core the
terminal app uses - lookup.py and llm_agent.py are imported unchanged, not
reimplemented. Nothing about the grounding rules, the dataset, or the
lookup logic changes by being served over HTTP instead of a terminal.

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
  ANTHROPIC_API_KEY   - enables the free-text ("ask") mode. Without it, the
                        app still runs, just with structured lookup only,
                        exactly like the CLI.
  ANTHROPIC_MODEL     - optional model override (see llm_agent.py).
  WEB_APP_USERNAME /
  WEB_APP_PASSWORD   - if BOTH are set, the whole app is gated behind HTTP
                        Basic Auth. Strongly recommended for any hosted demo
                        URL that isn't meant to be fully public, since the
                        "ask" mode spends your Anthropic API key on every
                        request. Leave both unset to run without a gate
                        (fine for purely local testing only).
  PORT                - what port to listen on when run directly with
                        `python app.py` (most hosts set this for you and
                        expect gunicorn to read it instead - see Procfile).
"""
from __future__ import annotations

import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, Response, render_template, request

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
        regions=lookup.VALID_REGIONS,
        result=None,
        query=None,
    )


@app.route("/lookup", methods=["POST"])
@_require_basic_auth
def structured_lookup():
    """Structured lookup - same deterministic path agent.py's structured_lookup() uses."""
    identifier = request.form.get("identifier", "").strip()
    region = request.form.get("region", "").strip()

    result = lookup.run_lookup(identifier, region, PRODUCTS, REQUIREMENTS)
    report = lookup.format_result(result)

    return render_template(
        "index.html",
        llm_available=LLM_AVAILABLE,
        regions=lookup.VALID_REGIONS,
        result=report,
        query=f"{identifier!r} / {region!r} (structured)",
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
            "index.html", llm_available=LLM_AVAILABLE, regions=lookup.VALID_REGIONS,
            result=None, query=None,
        )

    if not LLM_AVAILABLE:
        report = "[Plain-English mode needs an Anthropic API key - see README.md.]"
        return render_template(
            "index.html", llm_available=LLM_AVAILABLE, regions=lookup.VALID_REGIONS,
            result=report, query=user_text,
        )

    out_of_scope = llm_agent.detect_out_of_scope_topics(user_text)
    extracted = llm_agent.extract_query(LLM_CLIENT, LLM_MODEL, user_text)

    if extracted is None:
        report = (
            "[Couldn't reach the Claude API to interpret that question, or the "
            "response couldn't be read. Try the structured lookup form instead, "
            "or resubmit your question.]"
        )
        if out_of_scope:
            report = "\n".join(f"[Heads up] {h['note']}" for h in out_of_scope) + "\n\n" + report
        return render_template(
            "index.html", llm_available=LLM_AVAILABLE, regions=lookup.VALID_REGIONS,
            result=report, query=user_text,
        )

    identifier = extracted["identifier"]
    region = extracted["region"]
    requested_domains = extracted.get("requested_domains", [])

    if not identifier or not region:
        report = (
            f"[Could not confidently identify both a product and a region in that "
            f"question (got identifier={identifier!r}, region={region!r}). Try the "
            "structured lookup form below instead, or rephrase your question to "
            "name both a product and a destination region explicitly.]"
        )
        return render_template(
            "index.html", llm_available=LLM_AVAILABLE, regions=lookup.VALID_REGIONS,
            result=report, query=user_text,
        )

    result = lookup.run_lookup(identifier, region, PRODUCTS, REQUIREMENTS,
                                requested_domains=requested_domains)
    verified_report = lookup.format_result(result)
    phrased = llm_agent.phrase_answer(LLM_CLIENT, LLM_MODEL, user_text, verified_report, result.ok)

    parts = []
    for hit in extracted.get("out_of_scope_topics", out_of_scope):
        parts.append(f"[Heads up] {hit['note']}")
    if phrased:
        parts.append(phrased)
        parts.append("\n--- Verified source data (unedited) ---")
        parts.append(verified_report)
    else:
        parts.append(
            "[Couldn't reach the Claude API to phrase a summary - showing the "
            "verified lookup result directly.]"
        )
        parts.append(verified_report)

    return render_template(
        "index.html", llm_available=LLM_AVAILABLE, regions=lookup.VALID_REGIONS,
        result="\n".join(parts), query=user_text,
    )


if __name__ == "__main__":
    # Local/dev only - a real deployment should run this via gunicorn
    # (see Procfile), not Flask's built-in dev server.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
