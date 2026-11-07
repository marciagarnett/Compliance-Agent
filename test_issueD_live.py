from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.insert(0, ".")
import lookup, llm_agent

client = llm_agent.get_client()
model = llm_agent.DEFAULT_MODEL
products = lookup.load_products()
requirements = lookup.load_requirements()

cases = [
    ("T6: TW dock queried as UK (should flag)", "HP Thunderbolt 4 100W G6 Dock TW", "UK"),
    ("Related: PHILI monitor queried as US (should flag)", "HP E22 G5 FHD Monitor PHILI", "US"),
]

for label, ident, region in cases:
    print("=" * 90)
    print(label)
    result = lookup.run_lookup(ident, region, products, requirements)
    print("  region_mismatch_note set:", bool(result.region_mismatch_note))

    verified_report = lookup.format_result(result)
    not_ok_header = lookup.not_ok_header(result)
    phrased = llm_agent.phrase_answer(client, model, f"what's required for the {ident} in {region}?",
                                       verified_report, result.ok, not_ok_header,
                                       result.region_mismatch_note)
    note_in_phrased = bool(result.region_mismatch_note) and (result.region_mismatch_note in (phrased or ""))
    print("  model's phrased answer included the note verbatim:", note_in_phrased)

    verified_ok = llm_agent.verify_phrased_answer(
        phrased, lookup.shown_citations(result), result.ok,
        lookup.shown_row_markers(result), not_ok_header,
        result.region_mismatch_note,
    )
    print("  verify_phrased_answer() result:", verified_ok)
    print()
    print("  --- phrased answer ---")
    print(" ", (phrased or "(none)").replace("\n", "\n  "))