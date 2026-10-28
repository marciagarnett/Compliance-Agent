# Compliance Lookup Agent — What Changed, In Plain English

**Texas State University ISAN5318 project, Iteration 3**

This is the same implementation summary as `harness_implementation_summary.md`,
written in simpler language. The goal of all this work was the same
throughout: make sure the AI model (Claude) is never the thing deciding
whether an answer is correct or trustworthy enough to show someone. The
code around the model does that checking. The model's job stayed narrow —
read a question, write friendly sentences — and the code's job was to
double-check everything the model touched before anyone sees it.

The core lookup tool (matching a product, finding its requirements) didn't
change at all this session. Everything below is about tightening the
guardrails around the AI parts of the app.

---

## 1. One place for the "rules" the AI has to follow

**File:** `grounding.py`

Before: the project's five ground rules (things like "don't make up a
requirement that isn't in the data") were typed out by hand in more than
one place whenever the AI needed to be reminded of them. If someone edited
the wording in one spot, the other spot could be left out of date without
anyone noticing.

Now: the rules live in exactly one file, and a small helper function picks
out just the rules that are relevant to whatever the AI is doing at that
moment. One part of the app only needs to be reminded "don't invent a
product name" — that's the only rule it gets shown. Another part needs all
five rules, so it gets all five.

**Why this matters:** one source of truth means the instructions the AI
actually sees can't quietly drift away from what the written rules say they
should be.

**What's not perfect:** the plain-English rules document (`GROUNDING_RULES.md`,
meant for a person to read) still has to be updated by hand if the rules
change — it isn't automatically generated from the code. That's a known,
accepted gap, not an accident.

---

## 2. Making the AI give answers in a fixed format, not free text

**File:** `llm_agent.py`

Before: when a user typed a question like "What do I need to ship the
Poly Voyager Focus 2 to Taiwan?", the app asked the AI to figure out the
product name and the destination, then tried to find that information by
searching through the AI's reply text for something that looked like it.
That's fragile — a stray character or an unexpected reply style could
break it.

Now: the app uses a feature of Claude called "tool calling," which forces
the AI to fill in a small structured form (just two fields: product and
region) instead of writing a sentence the app then has to interpret. The
system double-checks that this form actually got filled in; if it didn't,
the app knows exactly why (the AI didn't fill it in, or the request to
Claude failed) instead of just getting a confusing blank result.

**Why this matters:** this removes a whole category of "I tried to guess
what the AI meant and guessed wrong" bugs.

**What's not perfect:** a separate, simpler check (not involving the AI)
looks for certain keywords in the question to flag topics the app doesn't
cover. That keyword check is still a bit too loose — for example, it can
flag the word "trade" even when it appears inside an unrelated word like
"trademark." This was a known issue going in and wasn't fixed this round.

---

## 3. A safety check on everything the AI writes before showing it to anyone

**File:** `llm_agent.py` (the check itself); `lookup.py` (small helper
functions it relies on)

This is the most important piece. After the AI writes a friendly, readable
answer, the app does not just show it. It runs a checklist against the
real data first:

- Is the answer actually non-empty?
- If this is a "we couldn't find a clear answer" situation, does the reply
  say so clearly, using the right wording for the situation (more on this
  below)?
- Does every source/citation that should be mentioned actually get
  mentioned?
- Does every individual requirement that should be listed actually show up?

If anything on that list fails, the app doesn't show the AI's writing at
all — it falls back to a plain, computer-generated version of the same
information instead. The AI is never trusted to grade its own homework;
the code grades it.

This checklist started simpler and got stronger twice, because of two real
problems found while actually testing the live app (not hypothetical
ones):

**Problem 1 — a cut-off answer slipped through.** One product had 12
separate requirements. The AI's reply got cut off partway through (it ran
out of allotted space, since its nicely formatted writing takes up more
room than the plain data) and silently dropped the last two requirements.
The original checklist didn't catch this, because those two missing
requirements happened to share the same source citation as an earlier one
that *did* make it in — so "every citation is present" looked true even
though two whole requirements were missing. Fix: gave the AI more room to
write its full answer, and changed the checklist to count requirements
individually instead of just checking citations.

**Problem 2 — a perfectly good clarification got rejected.** When a
product name was ambiguous (matched several possible products), the AI
correctly wrote a helpful response asking the user to pick the right one.
But the checklist rejected it anyway, for two small reasons: first, the
instructions given to the AI hadn't been updated after the app learned to
tell apart "please clarify" situations from "this needs expert review"
situations, so the AI was being told to use the wrong phrase for a
clarification case. Second — even after fixing that — the AI wrote a
polite opening sentence before the required phrase, and put the phrase in
bold text, and the checklist was looking for that exact phrase to be the
very first thing written, with no formatting around it. A perfectly good
answer was rejected over formatting that didn't actually matter. Fix: the
checklist now looks for the required phrase anywhere in the answer, not
specifically at the very start.

**Why this matters:** both problems were caught by actually running the
real app with the real AI and looking closely at what came back — not by
guessing in advance what might go wrong.

**What's not perfect:** this checklist confirms the required facts are
present somewhere in the text. It does not re-read the whole answer for
general accuracy — it couldn't catch, for example, the AI correctly
including all the right pieces of information but describing them in a
way that's technically all true yet misleading.

---

## 4. Telling apart "I need you to pick one" from "this needs an expert"

**Files:** `lookup.py`, `activity_log.py`, `agent.py`, `app.py`

Before: if the app couldn't confidently match a product name, it treated
every case the same way — labeled it "Human review required," whether the
name was genuinely unmatched to anything in the dataset, or just ambiguous
between a few similar products.

Now: those are treated as two different situations. If a name matches
several real products (for example, searching "Elite" matches eight
different HP products), the app now shows that actual list and asks which
one was meant — a quick clarifying question, not an escalation. If a name
truly doesn't match anything, that's still treated as a real gap that
needs a person with subject-matter expertise to review.

In the command-line version of the app, this is a real back-and-forth: the
app asks, the person answers, and the app re-runs the search with the
answer. The web version can't pause mid-conversation that way, so instead
it shows the same list and asks the person to ask their question again
with the exact name.

This same idea was applied a second time later on: if someone asked a
question in the web app without clearly naming *both* a product and a
destination (for example, "What are the requirements for the HP Elite?"
— no destination given), the app used to just say "I couldn't understand
that, please try again" with no further help. Now it actually looks up
whatever partial information it has — if the product name is ambiguous, it
shows the real candidate list; either way, it lists the actual regions the
app supports, so the person knows exactly what to retype.

**Why this matters:** these are genuinely different problems needing
different responses. Calling them both "needs a human to review" either
makes a routine clarifying question sound alarming, or makes it too easy
for a true gap to blend in with routine small asks.

**What's not perfect:** the web app's version of "please clarify" always
restarts the conversation — it can't remember "I already asked about this"
the way the command-line version can mid-conversation.

---

## 5. Keeping a record of what actually happened on each question

**Files:** `activity_log.py`, `agent.py`, `app.py`, `lookup.py`

The app keeps a simple log file of every question asked and what happened.
This got more detailed this session: instead of one generic "it failed"
entry, the log can now say specifically why — the AI's request failed to
go through, the AI didn't fill out its form correctly, the written answer
didn't pass the safety checklist, the user didn't name both a product and
a region, or the product name was ambiguous. The web version of the app
didn't keep any log at all before this session; now it does, using the
same categories as the command-line version.

**Why this matters:** a log that just says "something went wrong" isn't
useful for figuring out what to fix. A log that says exactly which of five
different things went wrong is.

**What's not perfect:** there's still no single, complete "here's
everything that happened on this one question" record — the different
pieces (what was searched for, what the AI wrote, whether it passed the
checklist) are tracked separately rather than bundled together as one
unit. That's a smaller, incremental improvement, not the full picture.

---

## The common thread

A few ideas repeat across all five sections above:

- **The code checks the AI's work; the AI never checks its own work.**
  Every safeguard added this session is a plain, deterministic check or
  decision made in code — never a case of asking the AI "was that
  correct?" and trusting its yes.
- **Fixes came from watching the real app fail, not from guessing ahead of
  time.** Both of the verification checklist's strengthenings, and the
  web app's "please clarify" improvement, happened only after actually
  running the live app and seeing something go wrong.
- **Nothing beyond what was asked for got rebuilt or deleted.** The
  existing lookup logic and both apps' overall shape were left alone; this
  work added guardrails around them.

---

## What's still missing or imperfect

- The keyword check for off-topic questions is still too loose (can
  mis-flag a word that's part of a longer, unrelated word).
- The hosted web app has no built-in protection against someone hammering
  it with requests (no timeout or rate limiting).
- There's no single written table listing, for the whole app, which
  decisions are made by fixed rules versus by the AI.
- There's still no one complete "record of this question" object — just
  several related pieces tracked separately.
- The plain-English rules document isn't automatically kept in sync with
  the actual rule code.
- Testing so far has been a mix of simulated AI responses and a handful of
  real live tries, not a full, exhaustive, or adversarial test — some
  future input could still find something these tests didn't.
- The safety checklist confirms the right facts are present, but doesn't
  fully guarantee the writing around them is never subtly misleading.
- The command-line and web versions of the app behave a little differently
  when asking a clarifying question, because of how each one is built.

None of this is a claim that the app is finished, bulletproof, or ready for
real production use — it's an honest list of what was built and what's
still open.
