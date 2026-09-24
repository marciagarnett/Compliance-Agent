# Test Queries

Manual verification pass for the Compliance Lookup Agent MVP. Run `python agent.py`,
then type `menu` and choose option **2) Structured lookup** each time — this reaches
the deterministic core directly regardless of which mode the app defaulted to.
(By default the app skips the menu: it drops you into plain-English mode if an API
key is configured, or structured mode otherwise — see `README.md`. Typing `menu`
at any prompt always gets you the explicit 4-option menu.)

For each case: enter the **Identifier** at the first prompt, the **Region** at the
second, and confirm the **Expected** behavior appears in the output.

| # | Identifier | Region | Expected |
|---|---|---|---|
| 1 | `Poly Voyager Focus 2` | `Taiwan` | Full report across all 4 domains. Includes an `[EMERGING - must comply by 2027-07-01]` row (Taiwan BSMI Battery Standard) and a `[PRINT]`-tagged warranty row citing Taiwan's Consumer Protection Act Art. 25. |
| 2 | `RMN-BT4320` | `US` | Same product family (Poly Voyager 4320), looked up by **RMN** instead of name — confirms RMN matching works. Report should be for the US. |
| 3 | `772C4AA` | `China` | Poly Sync 20, looked up by **SKU**. Report includes a `[PRINT]`-tagged environmental row (China RoHS) and an `[EITHER]`-tagged warranty row (electronic + mandatory printed card). |
| 4 | `Poly Blackwire 3220` | `EU/UK` | Report includes an `[EITHER]`-tagged safety/EMC row (EU/UK Simplified DoC) and an `[EMERGING]` environmental row (EU Lot 7, must comply by 2028-12-14). |
| 5 | `Poly Voyager 5200` | `US` | Report includes an `[EMERGING - must comply by 2026-06-09]` row (FCC Foreign Adversary Control Attestation) — confirms a near-term emerging date renders correctly. |
| 6 | `Poly Savi 7320 Office` | `Germany` | **Not found.** Output is tagged `[NOT FOUND]` and states `Germany` isn't a covered region, lists the 4 that are, and does **not** imply no requirements apply. |
| 7 | `Totally Fake Headset 9000` | `Taiwan` | **Not found.** Output is tagged `[NOT FOUND]`, explains the identifier wasn't matched by name/SKU/RMN, and suggests double-checking or escalating — does not imply the product is compliant. |
| 8 | `poly voyager free 60` (lowercase) | `taiwan` (lowercase) | Case-insensitive matching works for both product identifier and region — same report as `Poly Voyager Free 60` / `Taiwan`. |
| 9 | `10.1-inch Display` | `Taiwan` | New (catalog-expansion) category. Includes a `cybersecurity` row (Taiwan's new cybersecurity regulation for network-connected products) — Display is the one category with direct source evidence naming it in that domain. |
| 10 | `10.1-inch Display` | `US` | Same product, different region — no `cybersecurity` row here (the EU/US cybersecurity content wasn't verified to name standalone displays specifically; this is an intentional, documented coverage gap, not an omission). |
| 11 | `HP Poly 220 Stereo USB-A Wired Headset WW` | `US` | New category (Wired Headset). Includes a `hearing_aid_compatibility` row (FCC 47 CFR Section 20.19) but no `cybersecurity` row (a standalone wired headset has no network stack of its own). |
| 12 | `HP Poly 2 Leatherette Ear Cushions (2 Pieces) WW` | `US` | New category (Cushion) — a purely mechanical/passive accessory. Report should show requirements in only `trade_customs` and `warranty_documentation`; the other five domains show "(no requirements on file for this domain/region combination)" by design (see README.md "Scope"), not by gap. |

## What to check beyond exact matches

- Every row in every result prints all five things: the exact requirement text, the existing/emerging tag (with date if emerging), the print/online/either tag, the source citation, and the last-verified date.
- Cases 1-5 and 8 each return results across **all seven domains** (environmental/sustainability, safety/EMC/telecom, hearing aid compatibility, cybersecurity, battery safety, trade/customs, warranty documentation) — no domain silently disappears even if a region has fewer rows in one category. Cases 9-12 are new-catalog cases where some domains are *expected* to have zero rows by design — see each row's Expected column.
- Cases 6 and 7 never print a requirements report — only the `[NOT FOUND]` explanation.
- If you have an Anthropic API key configured (see `README.md`), repeat case 1 as a free-text question instead — either at the default prompt (if plain-English is the default for this run) or via `menu` option 1 — e.g. *"What do I need for a Poly Voyager Focus 2 shipping to Taiwan?"* The phrased answer must still contain every requirement, tag, and citation that structured lookup #1 returns, since the LLM is instructed only to rephrase, never to add or drop facts. The raw verified data is also printed underneath so you can compare directly.
