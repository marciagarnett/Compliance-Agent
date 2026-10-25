"""
Single source of truth for this project's five grounding rules.

The authoritative explanation of each rule - why it exists, and exactly
which code enforces it - lives in GROUNDING_RULES.md; that file is written
for a human reader and is not duplicated here. This module holds only the
short, one-sentence statement of each rule (taken verbatim from
GROUNDING_RULES.md's own numbered section headers), so that statement
exists in exactly one place in the codebase instead of being separately
hand-retyped inside every system prompt that needs to state it.

Every system prompt that cites a grounding rule - currently
llm_agent.extract_query() and llm_agent.phrase_answer() - calls
render_rules() with only the rule ids that actually govern that call, then
adds its own call-specific instructions for what the rule means in that
context. For example, the exact "Human review required." sentinel phrase
phrase_answer() must open with is a presentation detail specific to that
call, not part of the rule's own one-sentence statement - it stays local to
phrase_answer() rather than living here. This keeps the rule statements
themselves single-sourced while letting each call site stay narrow and
task-specific, per this project's existing design (narrow, role-specific
prompts).

If GROUNDING_RULES.md's own wording for a rule ever changes, this list
needs to be updated to match - there is no automatic parser tying the two
together (the markdown file includes a long "why" and "where enforced"
explanation per rule that a human should keep writing by hand). What this
module removes is the OTHER kind of drift: the same one-sentence rule text
being independently hand-retyped inside two or more system prompts with no
link between them at all.
"""
from __future__ import annotations

GROUNDING_RULES: list[dict[str, object]] = [
    {
        "id": 1,
        "text": "Use approved reference information when making decisions "
                "or recommendations.",
    },
    {
        "id": 2,
        "text": "Do not invent organizational policies, facts, rules, or "
                "procedures.",
    },
    {
        "id": 3,
        "text": "If the reference does not contain enough information, do "
                "not make up an answer or action.",
    },
    {
        "id": 4,
        "text": "Require human review when the available information is "
                "insufficient or conflicting.",
    },
    {
        "id": 5,
        "text": "When practical, identify which approved source or rule "
                "was used.",
    },
]

_RULES_BY_ID = {rule["id"]: rule for rule in GROUNDING_RULES}


def render_rules(rule_ids: list[int]) -> str:
    """
    Render the given grounding rules, by id, as numbered lines suitable for
    dropping into a system prompt - e.g. render_rules([2]) for a prompt
    that only needs rule 2 in scope, or render_rules([1, 2, 3, 4, 5]) for
    one that needs all five. Raises KeyError on an unknown id, so a typo in
    a call site fails loudly instead of silently dropping a rule.
    """
    return "\n".join(f"{i}. {_RULES_BY_ID[i]['text']}" for i in rule_ids)
