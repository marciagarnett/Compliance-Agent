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
# ---------------- EMEA (expanded beyond EU/UK) ----------------
    # Added 2026-10-07. Source: Regulatory Requirements Summary.xlsx,
    # "EMEA ITE" tab - the same workbook the original EU/UK safety_emc_telecom
    # rows above cite. Scope of this pass: safety_emc_telecom only, for the
    # 25 EMEA countries/territories this sheet lists individually (beyond
    # the already-covered "EU and EU-like* countries" bloc and UK). Where
    # the sheet left a field blank (no telecom data for a country, etc.),
    # that gap is stated explicitly below rather than invented (Grounding
    # Rule 3). environmental_sustainability, trade_customs, battery_safety,
    # warranty_documentation, hearing_aid_compatibility, and cybersecurity
    # for these 25 countries are NOT yet covered - they depend on other
    # reference workbooks (Machinery_ITE_Import_or_Importer_controls.xlsx,
    # WTR Regulatory Manual.xlsx, WW_Content_Requirements_FY25_FINAL.xlsx's
    # EMEA & ISE tab) not yet transcribed; that is a deliberate gap for this
    # pass, not a "not required" claim.
    ("Bluetooth Headset", "South Africa", "safety_emc_telecom",
     "South Africa (NRCS/ICASA) requires SANS 60950-1 / IEC 62368-1 safety and EN 55032 EMC "
     "compliance, plus ICASA Type Approval for the Bluetooth/RF module under EN 300328-2-2001, "
     "EN 301-489 pt 1 & 7, and GSM EN 301-511; evidenced by an NRCS Letter of Authority, EMI "
     "certificate, and ICASA Type Approval Certificate.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (South Africa rows)", "2026-10-07"),
    ("Bluetooth Headset", "Israel", "safety_emc_telecom",
     "Israel (Standards Institute of Israel) requires IS 1121 (IEC 62368-1) safety and IS 961 "
     "(CISPR 22/CISPR 32) EMC compliance, plus verification against EU harmonized radio standards "
     "(EN 300328, EN 301489, EN 301893, EN 300440, EN 301908, EN 301511) for the Bluetooth/Wi-Fi "
     "module; an EU DoC or equivalent test report satisfies all of these.",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Israel rows)", "2026-10-07"),
    ("Bluetooth Headset", "Ukraine", "safety_emc_telecom",
     "Ukraine requires conformity assessment to the UA LVE TR safety technical regulation "
     "(Resolution #1067) and the UA EMC TR EMC technical regulation (Resolution #1077), each "
     "evidenced by a National Statement of Conformity (NSoC), plus a UA RED TR conformity "
     "assessment (Decision #355) for the Bluetooth/Wi-Fi radio.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Ukraine rows)", "2026-10-07"),
    ("Bluetooth Headset", "Armenia", "safety_emc_telecom",
     "Armenia requires EurAsian Commission EAC TR 004/2011 and EAC TR 010/2011 safety "
     "certification/declaration and EAC TR 020/2011 EMC certification/declaration; the source "
     "sheet lists wired and wireless telecom requirements as low priority with no detailed "
     "information on file - a real data gap, not a \"not required\" finding.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Armenia rows)", "2026-10-07"),
    ("Bluetooth Headset", "Kazakhstan", "safety_emc_telecom",
     "Kazakhstan requires the same EurAsian Commission EAC TR 004/2011 and EAC TR 010/2011 safety "
     "and EAC TR 020/2011 EMC certification/declaration as other EAC member states, plus "
     "country-specific WLAN testing and/or factory inspection administered by the Ministry of "
     "Information and Communications for the wireless module.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Kazakhstan rows)", "2026-10-07"),
    ("Bluetooth Headset", "Kyrgyzstan", "safety_emc_telecom",
     "Kyrgyzstan requires the same EurAsian Commission EAC TR 004/2011 and EAC TR 010/2011 safety "
     "and EAC TR 020/2011 EMC certification/declaration as other EAC member states; the source "
     "sheet lists wired and wireless telecom requirements as low priority with no detailed "
     "information currently on file.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Kyrgyzstan rows)", "2026-10-07"),
    ("Bluetooth Headset", "Turkey", "safety_emc_telecom",
     "Turkey's safety, EMC, and wired/wireless telecom requirements for ITE products follow EU "
     "standards and directives directly, satisfied by the same EU DoC / test reports used for "
     "the EU/UK market.",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Turkey rows)", "2026-10-07"),
    ("Bluetooth Headset", "Saudi Arabia", "safety_emc_telecom",
     "Saudi Arabia (SASO) requires IEC 62368 safety compliance (IEC 60950 is no longer valid) "
     "processed through the SABER platform by an in-country Importer of Record, with EU test "
     "reports, user guides, a manufacturer's/importer's Declaration of Conformity (mDoC/iDoC), "
     "and an undertaking letter when required; the wireless module is covered by EU test reports "
     "against EU harmonized standards.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Saudi Arabia rows)", "2026-10-07"),
    ("Bluetooth Headset", "Serbia", "safety_emc_telecom",
     "Serbia requires the same EU General Product Safety Directive / Low Voltage Directive "
     "safety, EMC Directive, and Radio Equipment Directive compliance as the EU/UK market, but "
     "the Declaration of Conformity must specifically be provided in the Serbian language rather "
     "than just English.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Serbia rows)", "2026-10-07"),
    ("Bluetooth Headset", "Qatar", "safety_emc_telecom",
     "Qatar's wireless-telecom requirements for Bluetooth/Wi-Fi-enabled products follow EU "
     "harmonized standards; no additional country-specific safety or EMC certification "
     "requirement is on file for this category in the source sheet.",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Qatar rows)", "2026-10-07"),
    ("Bluetooth Headset", "UAE", "safety_emc_telecom",
     "The UAE's Telecommunications Regulatory Authority (TRA) requires Type Approval, with a "
     "physical product sample, for both wired and wireless telecom modules, in addition to "
     "EU-standards-based safety and EMC documentation (DoC, test reports, certificates, user "
     "guides).",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (UAE rows)", "2026-10-07"),
    ("Bluetooth Headset", "Bahrain", "safety_emc_telecom",
     "Bahrain's Telecommunications Regulatory Authority (TRA) requires Type Approval for wired "
     "and wireless telecom modules; safety and EMC follow EU standards with no additional "
     "certification requirement on file.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Bahrain rows)", "2026-10-07"),
    ("Bluetooth Headset", "Jordan", "safety_emc_telecom",
     "Jordan's Telecommunications Regulatory Commission (TRC) requires a physical sample for "
     "wired/wireless telecom type approval (a modular approach is accepted), and safety "
     "compliance is verified case-by-case at the import/shipment-arrival stage against EU "
     "standards.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Jordan rows)", "2026-10-07"),
    ("Bluetooth Headset", "Morocco", "safety_emc_telecom",
     "Morocco requires a Certificate of Conformity (PVoC) for every shipment for EN 62368-1 "
     "safety and a Morocco-specific DoC for EN 55032 EMC, plus ANRT homologation (host-based) "
     "for both the Bluetooth short-range module (EN 300328-2 / EN 301489-17) and the WLAN module "
     "(EN 300328, EN 301893, EN 301489-17, EN 62311).",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Morocco rows)", "2026-10-07"),
    ("Bluetooth Headset", "Oman", "safety_emc_telecom",
     "Oman requires an EU DoC for safety and EMC compliance and EU test reports / DoC / user "
     "guides for the wireless module; no additional wired-telecom certification requirement is "
     "on file for this category.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Oman rows)", "2026-10-07"),
    ("Bluetooth Headset", "Zambia", "safety_emc_telecom",
     "Zambia requires a PVoC Statement of Registration for EN 62368-1 safety and a ZICTA Type "
     "Approval Certificate (covering Bluetooth/WLAN/RF under EN 300328-2, EN 301-489, and GSM "
     "EN 301-511) for the wireless module.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Zambia rows)", "2026-10-07"),
    ("Bluetooth Headset", "Algeria", "safety_emc_telecom",
     "Algeria requires a CAP (Conformity Assessment Program) Statement of Registration / Product "
     "Certificate for EN 62368-1 safety, and the wireless module is subject to a national "
     "administrative procedure (with occasional testing) against EN 300328 / EN 301893 / "
     "EN 301489 standards.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Algeria rows)", "2026-10-07"),
    ("Bluetooth Headset", "Egypt", "safety_emc_telecom",
     "Egypt's National Telecom Regulatory Authority (NTRA) advises an EU DoC plus RF and EMC "
     "test reports for Bluetooth/WLAN modules (and a SAR report for any GSM/UMTS radio), "
     "alongside EU DoC-based EN 62368-1 safety and EN 55032 EMC compliance.",
     "online", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Egypt rows)", "2026-10-07"),
    ("Bluetooth Headset", "Tunisia", "safety_emc_telecom",
     "Tunisia's CERT authority systematically tests wired and wireless (Bluetooth/WLAN) telecom "
     "modules under a national administrative procedure, in addition to EU DoC-based EN 62368-1 "
     "safety and EN 55032 EMC compliance.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Tunisia rows)", "2026-10-07"),
    ("Bluetooth Headset", "Kuwait", "safety_emc_telecom",
     "Kuwait requires registration under the Kuwait Conformity Assurance Scheme (KUCAS), "
     "resulting in a 3-year Technical Evaluation Report, for IEC 62368-1 safety; CITRA accepts "
     "EU test reports for the wireless module.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Kuwait rows)", "2026-10-07"),
    ("Bluetooth Headset", "Gabon", "safety_emc_telecom",
     "Gabon requires an AGANOR PVoC Statement of Registration for EN 62368-1 (and associated "
     "EN 60204 machinery-safety) compliance; no wired/wireless telecom certification requirement "
     "is currently on file for this category - a real gap in the source, not a \"not required\" "
     "finding.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Gabon rows)", "2026-10-07"),
    ("Bluetooth Headset", "Kenya", "safety_emc_telecom",
     "Kenya requires a KEBS PVoC Statement of Registration for EN 60950 / EN 60204 / EN 62368-1 "
     "safety compliance; no telecom-specific certification requirement is on file for this "
     "category.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Kenya rows)", "2026-10-07"),
    ("Bluetooth Headset", "Nigeria", "safety_emc_telecom",
     "Nigeria requires a SON Product Certificate under the SONCAP (Standards Organization of "
     "Nigeria Conformity Assessment Program) for EN 62368-1 safety compliance; no telecom-"
     "specific certification requirement is on file for this category.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Nigeria rows)", "2026-10-07"),
    ("Bluetooth Headset", "Tanzania", "safety_emc_telecom",
     "Tanzania requires a TBS PVoC Statement of Registration for IEC/EN 60950, EN 60204, and "
     "EN 62368-1 safety compliance; no telecom-specific certification requirement is on file for "
     "this category.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Tanzania rows)", "2026-10-07"),
    ("Bluetooth Headset", "Uganda", "safety_emc_telecom",
     "Uganda requires a UNBS PVoC Statement of Registration for IEC/EN 60950, EN 60204, and "
     "EN 62368-1 safety compliance; no telecom-specific certification requirement is on file for "
     "this category.",
     "either", "existing", "Now",
     "Regulatory Requirements Summary.xlsx - EMEA ITE tab (Uganda rows)", "2026-10-07"),
]

HEADER = ["category", "region", "domain", "requirement", "documentation_format",
          "status", "must_comply_by", "citation_source", "last_verified"]

with open("data/compliance_requirements.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(ROWS)

print(f"Wrote {len(ROWS)} rows to data/compliance_requirements.csv")
