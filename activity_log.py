"""
Basic, append-only activity log for the Compliance Lookup Agent.

Every lookup attempt writes exactly one line recording whether the agent
COMPLETED its task, needs CLARIFICATION from the asker, stopped for
HUMAN_REVIEW, or FAILED outright - plus just enough context to find that
query again later. CLARIFICATION and HUMAN_REVIEW are deliberately kept
separate: an ambiguous product match just needs the asker to pick from a
short list the system already showed them, while HUMAN_REVIEW means a
regulatory subject-matter expert's judgment is actually needed - logging
both the same way would overstate how much human involvement a given
turn really required. Deliberately excluded, per
project policy (don't store more than is needed): the user's raw free-text
question, the full lookup message/citation text, the Anthropic API key, and
any exception details or stack traces. Stored as plain text, one line per
event, so it can be opened and read without any special tooling.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "activity_log.txt")

# The four outcomes this log distinguishes - nothing finer-grained than this.
COMPLETED = "COMPLETED"
# The asker needs to answer a targeted follow-up (e.g. pick one of several
# plausible product matches) before this turn can resolve - not a case
# that needs a regulatory SME's judgment. See reason_code "ambiguous_product".
CLARIFICATION = "CLARIFICATION"
HUMAN_REVIEW = "HUMAN_REVIEW"
FAILED = "FAILED"


def log_event(outcome: str, mode: str, identifier: str = "", region: str = "", reason: str = "") -> None:
    """
    Append one line to activity_log.txt.

    outcome    - COMPLETED, CLARIFICATION, HUMAN_REVIEW, or FAILED (use the
                 constants above).
    mode       - which entry point this was: "structured", "ask", or "startup".
    identifier - the product identifier involved, if any. Deliberately NOT
                 the user's raw free-text question - that could contain
                 anything they happened to type, which this log has no
                 reason to keep.
    region     - the region involved, if any.
    reason     - a short, fixed label (e.g. "unmatched_product"), never the
                 full message text, a citation, or a stack trace.

    Never raises - a logging problem (disk full, permissions, read-only
    filesystem) must never be able to take down the agent itself.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = (
        f"{timestamp} | {outcome:<13} | mode={mode:<10} | "
        f"identifier={identifier!r} | region={region!r} | reason={reason}\n"
    )
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
