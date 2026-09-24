"""
One-time script used to generate data/compliance_requirements.csv.
Not part of the running application - kept here for transparency/reproducibility
of how the sample dataset was authored. Safe to delete after data/ is generated.
"""
import csv

ROWS = [
    # category, region, domain, requirement, documentation_format, status, must_comply_by, citation_source, last_verified

    # ---------------- EU/UK ----------------
    ("Bluetooth Headset", "EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances "
     "(lead, mercury, cadmium, hexavalent chromium, PBB, PBDE, and 4 phthalates) must be met.",
     "online", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU/UK RoHS reference)", "2026-09-09"),
    ("Bluetooth Headset", "EU/UK", "environmental_sustainability",
     "Product must display the EU WEEE crossed-out wheelie-bin symbol on the device housing.",
     "print", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU WEEE Statement)", "2026-09-09"),
    ("Bluetooth Headset", "EU/UK", "environmental_sustainability",
     "EU Lot 7 Ecodesign regulation newly extends requirements to external power supplies, wireless "
     "chargers, and USB Type-C charging cables shipped with the product.",
     "online", "emerging", "2028-12-14",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (EMEA)", "2026-08-01"),

    ("Bluetooth Headset", "EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing RED 2014/53/EU and IEC 62368-1 "
     "safety/EMC standard must be included with the product.",
     "either", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU/UK Simplified DoC)", "2026-09-09"),
    ("Bluetooth Headset", "EU/UK", "safety_emc_telecom",
     "Product must carry the EU RED graphic/marking and the CE mark on the device or its packaging.",
     "print", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU RED graphic)", "2026-09-09"),
    ("Bluetooth Headset", "EU/UK", "safety_emc_telecom",
     "Documentation must include an IEEE 802.11x radio compliance note for the integrated Wi-Fi module.",
     "online", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (IEEE 802.11x note)", "2026-09-09"),

    ("Bluetooth Headset", "EU/UK", "trade_customs",
     "Customs approval for Safety, EMC, Energy, and Telecom is NOT required to be held specifically "
     "in the importer's (HP entity's) name for EU/EEA.",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (EU/EEA row)", "2026-09-09"),
    ("Bluetooth Headset", "EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC/Energy/Telecom is handled on "
     "a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (EU/EEA and UK rows)", "2026-09-09"),
    ("Bluetooth Headset", "EU/UK", "trade_customs",
     "A UK-specific conformity marking (UKCA) may be required alongside CE marking depending on the "
     "product's UK market entry route; final scope/date still being confirmed.",
     "print", "emerging", "TBD",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (UK row)", "2026-09-09"),

    ("Bluetooth Headset", "EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the "
     "customer must be given the option to request a printed copy.",
     "either", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - EMEA & ISE tab (United Kingdom row)", "2025-05-01"),
    ("Bluetooth Headset", "EU/UK", "warranty_documentation",
     "Austria: if only a short-form warranty is provided in print, the full long-form guarantee "
     "statement must also be made available to the consumer on a \"permanent data carrier\" "
     "(electronic or physical); a website link alone does not satisfy this.",
     "either", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - EMEA & ISE tab (Austria row)", "2025-05-01"),
    ("Bluetooth Headset", "EU/UK", "warranty_documentation",
     "Setup instructions containing safety/regulatory notices must be provided in printed form for "
     "both commercial and consumer customers in the UK.",
     "print", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - EMEA & ISE tab (United Kingdom row)", "2025-05-01"),

    # ---------------- US ----------------
    ("Bluetooth Headset", "US", "environmental_sustainability",
     "No federal RoHS-equivalent restriction applies to headsets at the national level, but California "
     "Proposition 65 disclosure may apply if regulated substances are present.",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA row, comments)", "2026-09-09"),
    ("Bluetooth Headset", "US", "environmental_sustainability",
     "ENERGY STAR labeling is voluntary for this product category and is not a mandatory requirement.",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA Energy row)", "2026-09-09"),
    ("Bluetooth Headset", "US", "environmental_sustainability",
     "USA Cybersecurity: FCC-adjacent IoT Labeling Program (\"Cyber Trust Mark\") is newly effective and "
     "may apply to connected accessories; effective date still TBD.",
     "online", "emerging", "TBD",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (Americas)", "2026-08-01"),

    ("Bluetooth Headset", "US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via "
     "Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA EMC row)", "2023-06-14"),
    ("Bluetooth Headset", "US", "safety_emc_telecom",
     "FCC ID / regulatory model number must be marked on the product or accessible via e-label per "
     "47 CFR Section 2.935.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA EMC row, comments)", "2023-06-14"),
    ("Bluetooth Headset", "US", "safety_emc_telecom",
     "USA Wireless: FCC Foreign Adversary Control Attestation requirement newly effective June 9, 2026, "
     "requiring supply-chain attestation prior to equipment authorization.",
     "online", "emerging", "2026-06-09",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (Americas)", "2026-08-01"),

    ("Bluetooth Headset", "US", "trade_customs",
     "Customs approval for Telecom is required to be held in the importer's (HP entity's) name for US "
     "import; Safety, EMC, and Energy are not.",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (United States row)", "2026-09-09"),
    ("Bluetooth Headset", "US", "trade_customs",
     "US customs review does not include a technical-regulations check for Safety, EMC, Energy, or "
     "Telecom at border entry for this product category.",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (United States row)", "2026-09-09"),
    ("Bluetooth Headset", "US", "trade_customs",
     "FCC Supply Chain Security / Equipment Authorization rule updates are in progress and may add new "
     "import-eligibility checks; effective date TBD.",
     "online", "emerging", "TBD",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (Americas)", "2026-08-01"),

    ("Bluetooth Headset", "US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers "
     "(printed warranty was legally cleared for elimination on 6/23/23).",
     "online", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - AMS & LA tab (United States row)", "2023-06-23"),
    ("Bluetooth Headset", "US", "warranty_documentation",
     "Setup instructions must be provided in printed form; U.S. law does not strictly mandate this, but "
     "a printed pointer to the Safety & Comfort Guide is included to align with other countries and "
     "reduce litigation risk.",
     "print", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - AMS & LA tab (United States row)", "2023-06-23"),
    ("Bluetooth Headset", "US", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers.",
     "online", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - AMS & LA tab (United States row)", "2023-06-23"),

    # ---------------- China ----------------
    ("Bluetooth Headset", "China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-"
     "substance disclosure table must be included.",
     "print", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (China RoHS)", "2026-09-09"),
    ("Bluetooth Headset", "China", "environmental_sustainability",
     "China Energy Label / energy-efficiency disclosure applies where the accessory includes a charging "
     "base; revised energy standard becomes effective Feb 1, 2027.",
     "print", "emerging", "2027-02-01",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)", "2026-08-01"),
    ("Bluetooth Headset", "China", "environmental_sustainability",
     "China Regulation Notice (product-specific compliance statement) must be included per WTR APJ "
     "ITE guidance.",
     "either", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (China Regulation Notice)", "2026-09-09"),

    ("Bluetooth Headset", "China", "safety_emc_telecom",
     "China Compulsory Certification (CCC) safety/EMC mark must be affixed to the product where "
     "applicable to the accessory category.",
     "print", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - APJ ITE tab (China row)", "2026-09-09"),
    ("Bluetooth Headset", "China", "safety_emc_telecom",
     "China SRRC radio-type approval must be obtained and the approval/model number disclosed in "
     "product documentation for the Bluetooth/Wi-Fi radio.",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - APJ ITE tab (China row)", "2026-09-09"),
    ("Bluetooth Headset", "China", "safety_emc_telecom",
     "China's new Mobile Power Bank traceability requirement (QR code) applies if the product ships "
     "with a battery-pack accessory; NPIs must comply by March 2026, sustaining products by March 2027.",
     "either", "emerging", "2027-03-01",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)", "2026-08-01"),

    ("Bluetooth Headset", "China", "trade_customs",
     "Customs approval for Telecom, EMC, and Safety must be held in the importer's (HP entity's) name "
     "for import into China; Energy is not required.",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (China row)", "2026-09-09"),
    ("Bluetooth Headset", "China", "trade_customs",
     "Chinese customs review includes a technical-regulations check for EMC, Energy, and Telecom, with "
     "Safety review handled discretionarily (\"D\").",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (China row)", "2026-09-09"),
    ("Bluetooth Headset", "China", "trade_customs",
     "China RoHS registration is expanding to cover scanners, peripherals, and external power supply "
     "accessories, effective Aug 1, 2027.",
     "online", "emerging", "2027-08-01",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)", "2026-08-01"),

    ("Bluetooth Headset", "China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the "
     "option of a printed copy; a mandatory printed service/warranty card is also required per China's "
     "telecom card regulation.",
     "either", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (China row)", "2026-09-09"),
    ("Bluetooth Headset", "China", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers in China.",
     "online", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (China row)", "2026-09-09"),
    ("Bluetooth Headset", "China", "warranty_documentation",
     "Setup instructions may be provided electronically in China; no print mandate was identified for "
     "this product category.",
     "online", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (China row)", "2026-09-09"),

    # ---------------- Taiwan ----------------
    ("Bluetooth Headset", "Taiwan", "environmental_sustainability",
     "Taiwan BSMI RoHS marking and hazardous-substance disclosure applies to Group 1-6 accessory "
     "products.",
     "print", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - APJ ITE tab (Taiwan row)", "2026-09-09"),
    ("Bluetooth Headset", "Taiwan", "environmental_sustainability",
     "Taiwan BSMI Battery Standard is in draft; official release expected 2H 2026, with enforcement "
     "beginning July 1, 2027, for products shipping with a battery pack.",
     "either", "emerging", "2027-07-01",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)", "2026-08-01"),
    ("Bluetooth Headset", "Taiwan", "environmental_sustainability",
     "Taiwan's new Cybersecurity regulation for network-connected products newly applies to displays "
     "and digital cameras from Jan 1, 2028; not yet confirmed to extend to headset accessories.",
     "online", "emerging", "2028-01-01",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)", "2026-08-01"),

    ("Bluetooth Headset", "Taiwan", "safety_emc_telecom",
     "Taiwan BSMI Safety/EMC certification mark must be affixed to the product for Group 1-6 category "
     "accessories.",
     "print", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - APJ ITE tab (Taiwan row)", "2026-09-09"),
    ("Bluetooth Headset", "Taiwan", "safety_emc_telecom",
     "Taiwan NCC statement and radio type-approval number must be included in product documentation "
     "for the Bluetooth/Wi-Fi radio.",
     "either", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (NCC Statement)", "2026-09-09"),
    ("Bluetooth Headset", "Taiwan", "safety_emc_telecom",
     "Documentation must include an EIRP disclosure and IEEE 802.11x compliance note for the integrated "
     "wireless radio.",
     "online", "existing", "Now",
     "WW-long-form-QSG-content (2).xlsx - Sheet2 (EIRP content / IEEE 802.11x note)", "2026-09-09"),

    ("Bluetooth Headset", "Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import "
     "into Taiwan; Energy is not required.",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (Taiwan row)", "2026-09-09"),
    ("Bluetooth Headset", "Taiwan", "trade_customs",
     "Taiwan customs review includes a technical-regulations check for Safety, EMC, Energy, and Telecom "
     "at border entry.",
     "online", "existing", "Now",
     "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (Taiwan row)", "2026-09-09"),
    ("Bluetooth Headset", "Taiwan", "trade_customs",
     "Taiwan BSMI EMC/RoHS scope is expanding to add new Group 7 products and tiled monitors, effective "
     "Jan 1, 2028.",
     "online", "emerging", "2028-01-01",
     "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)", "2026-08-01"),

    ("Bluetooth Headset", "Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in "
     "printed form, including product name/type/quantity, serial number, warranty coverage and period, "
     "and manufacturer/distributor name and address.",
     "print", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (Taiwan row)", "2026-09-09"),
    ("Bluetooth Headset", "Taiwan", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers in Taiwan.",
     "online", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (Taiwan row)", "2026-09-09"),
    ("Bluetooth Headset", "Taiwan", "warranty_documentation",
     "A generic (non-product-specific) warranty statement is acceptable in Taiwan only if it does not "
     "create ambiguity about the length and type of warranty offered.",
     "print", "existing", "Now",
     "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (Taiwan row)", "2026-09-09"),
]

HEADER = ["category", "region", "domain", "requirement", "documentation_format",
          "status", "must_comply_by", "citation_source", "last_verified"]

with open("data/compliance_requirements.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(ROWS)

print(f"Wrote {len(ROWS)} rows to data/compliance_requirements.csv")
