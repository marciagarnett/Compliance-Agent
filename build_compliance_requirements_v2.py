"""
Script used to generate the EXPANDED data/compliance_requirements.csv - the
catalog-wide follow-up to build_data.py (which authored the original 48
Bluetooth Headset-only rows and is left completely untouched/still present
for its own transparency record).

Not part of the running app - kept here, like build_data.py, purely for
transparency into how each row was authored. Safe to delete after data/ is
regenerated.

WHY AN ARCHETYPE MODEL INSTEAD OF 49 HAND-AUTHORED CATEGORY BLOCKS
--------------------------------------------------------------------
Reading the actual reference workbooks in reference/ (see source_index.md)
confirms that four of this project's five approved sources are already
organized generically across product categories, not per HP product line:

  - Regulatory Requirements Summary.xlsx: one blanket "ITE Products" table
    per region (EMEA/AMS/APJ tabs) - the Safety/EMC/Energy/Telecom rows
    already generalize across nearly every category in this catalog.
  - Machinery_ITE_Import_or_Importer_controls.xlsx: a generic Y/N/D
    importer-control matrix per country, again keyed to "ITE products" as a
    whole, not a specific product line.
  - WW_Content_Requirements_FY25_FINAL.xlsx: purely per-country warranty/
    documentation rules (Electronic vs. Printed, Commercial vs. Consumer) -
    zero product-category differentiation anywhere in the sheet.
  - ER Roadmap_FY26Q3.pdf: tags each emerging regulation with explicit
    product-category icons (DT/NB/Print/Display/Tablet/Peripherals/Power
    Options/Machinery), which is what makes the cybersecurity and
    battery-safety entries below traceable to specific category groups
    rather than guessed.

Given that, hand-authoring 49 near-duplicate category blocks would not add
real distinctions - it would just retype the same generic requirement text
49 times with the category name swapped. Instead, this script:

  1. Classifies each of the (48) non-Bluetooth-Headset categories into one
     of 8 ARCHETYPES based on real, checkable properties (does the category
     actually contain a radio; is it mains-powered vs. battery; is it worn
     against the ear; does it have its own network/OS stack) - the
     classification notes below cite the actual evidence checked (mostly
     product_master.csv description text) for every judgment call, exactly
     as build_product_master.py / build_product_master_kme.py already do
     for their own category assignments.
  2. Authors requirement rows ONCE per archetype+region+domain, citing the
     same approved sources the original Bluetooth Headset rows cite.
  3. Fans each archetype's rows out to every category in that archetype.

This mirrors how the source documents themselves are organized (generic
ITE-wide tables, not per-SKU-category tables) - it is not a shortcut that
invents category-specific facts, it is declining to *pretend* per-category
granularity the source material doesn't have, while still making a real,
documented judgment call per category on the handful of properties (radio /
battery / ear-coupling / network-connectedness) the source material's own
ER Roadmap category icons AND product_master.csv description text DO
support checking per category.

Bluetooth Headset's original 48 rows (from build_data.py) are carried
forward byte-for-byte into the regenerated CSV - nothing about that
category's existing data changes.

NEW DOMAINS
-----------
Three domains are added beyond the original four, per direction to treat
them as first-class domains rather than folding them into
safety_emc_telecom:

  - cybersecurity: network-connected/"digital element" product regulation
    (EU Cyber Resilience Act, US IoT Labeling/"Cyber Trust Mark" program,
    Taiwan's new cybersecurity regulation for network-connected products).
    Source 5 (ER Roadmap) explicitly tracks these as a named, fast-growing
    category with per-product-type icons, which is what makes scoping this
    domain to actual network-connected/networked-endpoint categories
    (below) possible rather than a guess.
  - battery_safety: transport/safety/traceability rules specific to
    products that ship with a battery (UN38.3 lithium-battery transport
    testing, IEC 62133-2 cell/pack safety, the EU Battery Regulation (EU)
    2023/1542, China's Mobile Power Bank QR traceability rule, and
    Taiwan's draft BSMI Battery Standard - the last two both already
    appeared, un-domained, inside the original Bluetooth Headset dataset's
    safety_emc_telecom and environmental_sustainability rows; this script
    does not touch those original rows, it only gives the *new* categories
    a proper battery_safety row instead of folding it into another domain).
  - hearing_aid_compatibility: telecom-terminal-equipment accessibility
    rules for devices worn against or held to the ear (US FCC 47 CFR
    Section 20.19 HAC rules; EU RED Article 3(3)(f)/EN 301 406 plus the
    European Accessibility Act (EU) 2019/882; Taiwan NCC accessibility
    requirements for telecom terminal equipment). China is deliberately
    left with zero rows in this domain - no accessibility-specific
    regulation for this could be verified against this project's approved
    reference material or a citable public source with confidence, and
    Grounding Rule 3 (this app never guesses) applies to how this dataset
    gets built, not only to how it gets queried.

A handful of rows below cite the specific regulation directly (e.g. "FCC 47
CFR Section 20.19", "Regulation (EU) 2023/1542") rather than pointing into
one of the five project workbooks, because hearing_aid_compatibility and
parts of battery_safety are not covered by row-level detail in any of the
five approved workbooks - only by the ER Roadmap's category-level flags.
Citing the real external regulation directly is more honest than inventing
a fake worksheet reference that doesn't exist; every such row is called out
in a comment at the point it's authored below.
"""
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUT_PATH = os.path.join(DATA_DIR, "compliance_requirements.csv")
EXISTING_HEADSET_ROWS_SOURCE = os.path.join(DATA_DIR, "compliance_requirements.csv")

REGIONS = ["EU/UK", "US", "China", "Taiwan"]

# ---------------------------------------------------------------------------
# CATEGORY ARCHETYPES
# ---------------------------------------------------------------------------
# Every category from product_master.csv except Bluetooth Headset (which
# keeps its own hand-authored 48 rows, untouched). Grouped by the actual
# properties that change what compliance content applies. See the class-by-
# class notes for the evidence behind each judgment call.

ARCHETYPES = {

    # Notebook-class compute: WiFi/Bluetooth radio built in as standard
    # (industry-standard default for this product class), has an internal
    # battery, has its own OS/network stack (in scope for cybersecurity).
    "radio_ite_mobile": [
        "Commercial Notebook", "Consumer Notebook",
        "Commercial Mobile Workstation", "Commercial Mobile Thin Client",
    ],

    # Desktop-class / infrastructure compute: mains-powered, no built-in
    # radio by industry-standard default (wired Ethernet is the base
    # configuration; WiFi is commonly an optional add-in card, not assumed
    # here per the conservative default direction), no internal battery.
    # Display is included here but is_network_connected=False for it
    # specifically (see cybersecurity section) since a traditional external
    # display has no independent IP stack, unlike the compute/infra items.
    "wired_ite_desktop": [
        "Commercial Desktop", "Consumer Desktop", "Commercial Workstation",
        "Commercial Thin Client", "Commercial RPOS", "Docking Station",
        "Hub", "Hub Bundle", "Switch", "Expansion Module", "Display",
    ],

    # Ear-coupled audio accessories with a Bluetooth/wireless radio and an
    # internal rechargeable battery. Evidence: checked real product_master
    # description text for both categories - Phone Handset showed radio
    # keywords ("bluetooth"/"wireless") in 13 of 23 rows (majority); Earbuds
    # is a category name that is, by industry convention, true-wireless
    # Bluetooth (a wired-only in-ear product is conventionally categorized
    # as "Headset" instead) even though the sampled description text
    # ("Poly Voyager Free" naming) doesn't spell out "Bluetooth" per SKU.
    "radio_audio_accessory_ear_coupled": ["Earbuds", "Phone Handset"],

    # Bluetooth remote control - radio-bearing, not ear-coupled. Evidence:
    # both sampled product_master rows explicitly say "Bluetooth Remote
    # Control" in their description text.
    "radio_accessory_not_ear_coupled": ["Remote Control"],

    # Wired, ear-coupled devices: no radio by default. Evidence for Phone:
    # sampled product_master description text repeatedly and explicitly
    # says "No Radio" (e.g. "HP Poly Edge V200 OpenSIP DeskPhone No Radio
    # GSA/TAA WW") - these are wired desk IP phones. Wired Headset is
    # wired-only by its own category name. Both are held to/against the ear
    # in normal use (a desk phone's handset, a headset's earpiece), so
    # hearing_aid_compatibility applies to both; Phone is a networked VoIP
    # endpoint (cybersecurity in scope), a standalone Wired Headset is not.
    "wired_ite_ear_coupled": ["Phone", "Wired Headset"],

    # UC/AV endpoint devices - wired by default (near-zero radio-keyword
    # hits across every sampled category below), not worn against the ear.
    # cybersecurity is scoped to the items that are themselves networked UC
    # endpoints (Video Conferencing, Video Bar/Bundle, Video Conferencing
    # Bundle, Speaker Phone, Audio Bridge) and not to pure USB/analog
    # peripherals that ride on a host device's network connection instead
    # of having their own (Microphone, Video Camera).
    "wired_uc_av_not_ear_coupled": [
        "Video Conferencing", "Video Bar", "Video Bar Bundle",
        "Video Conferencing Bundle", "Speaker Phone", "Audio Bridge",
        "Video Camera", "Microphone",
    ],

    # Active-electronics power/adapter accessories: contain real circuitry
    # (power conversion, protocol adaptation) so RoHS/WEEE-style
    # environmental and safety/EMC rules still apply, but evidence does not
    # support a radio-by-default (Adapters/Cables sampled at 9 radio-keyword
    # hits out of 113 rows - a minority, dominated by plain wired
    # cords/cables) and Power Requirements - Battery is the one category in
    # this whole catalog where battery_safety is the PRIMARY, not
    # secondary, domain.
    "power_and_adapter_accessory": [
        "Adapter", "Adapters / Cables", "VoIP Adapter", "wall charger",
        "Power Requirements - AC Adapter", "Power Requirements - Battery",
    ],

    # Purely mechanical/passive parts with no independent active
    # electronics of their own (cushions, foam, mounting hardware, bags,
    # plastic moldings, brackets, a stylus). Evidence: zero radio-keyword
    # hits across every sampled category, and none of these are, on their
    # own, "electrical or electronic equipment" under RoHS/WEEE's own
    # definition - they only ever ship attached to or alongside a real EEE
    # product, which is where that product's own rows already apply.
    # Scoped to only the two domains that are generic across literally any
    # imported, warrantied product regardless of whether it's active
    # electronics (Source 2 and Source 3 are both confirmed fully generic
    # across ITE-adjacent products, including accessories, in the sourcing
    # pass this script's rows are drawn from).
    "mechanical_passive_accessory": [
        "Accessory / Service Part", "Bags and Cases", "BRACKET",
        "Cable Clips", "Cushion", "Foam", "Holders and Stands",
        "Mounting Kit", "Pen", "Plastic Moldings", "Plastic Plate",
        "Polarizing Filter", "RACK", "Stand",
    ],
}

# Sanity-check hook run at the bottom of this script: every category in
# product_master.csv other than Bluetooth Headset must appear in exactly
# one archetype above - if a category is renamed or a new one is added to
# the catalog later, this script fails loudly instead of silently leaving
# it with zero compliance rows.
ALL_CLASSIFIED_CATEGORIES = {c for cats in ARCHETYPES.values() for c in cats}

# ---------------------------------------------------------------------------
# Reusable citations - the ones repeated verbatim from the original,
# already-verified Bluetooth Headset rows (build_data.py), so every reuse
# below points at the exact same workbook/tab/row that was actually read.
# ---------------------------------------------------------------------------
CIT_EU_ROHS = "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU/UK RoHS reference)"
CIT_EU_WEEE = "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU WEEE Statement)"
CIT_EU_LOT7 = "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (EMEA)"
CIT_EU_DOC = "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU/UK Simplified DoC)"
CIT_EU_RED_MARK = "WW-long-form-QSG-content (2).xlsx - Sheet2 (EU RED graphic)"
CIT_EU_8021X = "WW-long-form-QSG-content (2).xlsx - Sheet2 (IEEE 802.11x note)"
CIT_EU_IMPORT = "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (EU/EEA row)"
CIT_EU_IMPORT_D = "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (EU/EEA and UK rows)"
CIT_UK_UKCA = "Regulatory Requirements Summary.xlsx - EMEA ITE tab (UK row)"
CIT_UK_WARR = "WW_Content_Requirements_FY25_FINAL.xlsx - EMEA & ISE tab (United Kingdom row)"
CIT_AT_WARR = "WW_Content_Requirements_FY25_FINAL.xlsx - EMEA & ISE tab (Austria row)"

CIT_US_ROHS = "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA row, comments)"
CIT_US_ENERGY = "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA Energy row)"
CIT_US_ROADMAP = "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (Americas)"
CIT_US_EMC = "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA EMC row)"
CIT_US_EMC_C = "Regulatory Requirements Summary.xlsx - AMS ITE tab (USA EMC row, comments)"
CIT_US_IMPORT = "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (United States row)"
CIT_US_WARR = "WW_Content_Requirements_FY25_FINAL.xlsx - AMS & LA tab (United States row)"

CIT_CN_ROHS = "WW-long-form-QSG-content (2).xlsx - Sheet2 (China RoHS)"
CIT_CN_ROADMAP = "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)"
CIT_CN_REGNOTICE = "WW-long-form-QSG-content (2).xlsx - Sheet2 (China Regulation Notice)"
CIT_CN_CCC = "Regulatory Requirements Summary.xlsx - APJ ITE tab (China row)"
CIT_CN_IMPORT = "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (China row)"
CIT_CN_WARR = "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (China row)"

CIT_TW_BSMI = "Regulatory Requirements Summary.xlsx - APJ ITE tab (Taiwan row)"
CIT_TW_NCC = "WW-long-form-QSG-content (2).xlsx - Sheet2 (NCC Statement)"
CIT_TW_EIRP = "WW-long-form-QSG-content (2).xlsx - Sheet2 (EIRP content / IEEE 802.11x note)"
CIT_TW_IMPORT = "Machinery_ITE_Import_or_Importer_controls.xlsx - Importer Invoice countries ITE tab (Taiwan row)"
CIT_TW_WARR = "WW_Content_Requirements_FY25_FINAL.xlsx - APJ tab (Taiwan row)"
CIT_TW_ROADMAP = "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ)"

# Direct-regulation citations for content not covered at row level by any of
# the five project workbooks (see module docstring - "NEW DOMAINS").
CIT_EU_BATTERY_REG = "Regulation (EU) 2023/1542 (EU Battery Regulation) - cited directly; not row-level content in the five project workbooks"
CIT_UN38_3 = "UN Manual of Tests and Criteria, Part III Subsection 38.3 (UN38.3 lithium-battery transport testing) - cited directly; not row-level content in the five project workbooks"
CIT_IEC62133 = "IEC 62133-2 (portable lithium cell/pack safety) - cited directly; not row-level content in the five project workbooks"
CIT_FCC_HAC = "FCC 47 CFR Section 20.19 (Hearing Aid Compatibility) - cited directly; not row-level content in the five project workbooks"
CIT_EU_RED_HAC = "RED 2014/53/EU Article 3(3)(f) and EN 301 406 (radio equipment accessibility) - cited directly; not row-level content in the five project workbooks"
CIT_EAA = "Directive (EU) 2019/882 (European Accessibility Act) - cited directly; not row-level content in the five project workbooks"
CIT_TW_NCC_ACCESS = "Taiwan NCC telecommunications terminal equipment accessibility technical regulations - cited directly; not row-level content in the five project workbooks"
CIT_EU_CRA = "Regulation (EU) 2024/2847 (EU Cyber Resilience Act) - cited directly; not row-level content in the five project workbooks"
CIT_US_CYBERTRUST = "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (Americas) / FCC IoT Labeling Program (\"U.S. Cyber Trust Mark\")"
CIT_TW_CYBERSEC = "ER Roadmap_FY26Q3.pdf - Emerging Regulations Roadmap (APJ) / Taiwan cybersecurity regulation for network-connected products"

TODAY = "2026-09-24"

# row tuple: (region, domain, requirement, documentation_format, status, must_comply_by, citation_source, last_verified)

TEMPLATE_ROWS = {}

# ===========================================================================
# radio_ite_mobile - Commercial Notebook, Consumer Notebook,
# Commercial Mobile Workstation, Commercial Mobile Thin Client
# ===========================================================================
TEMPLATE_ROWS["radio_ite_mobile"] = [
    ("EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances (lead, mercury, cadmium, hexavalent chromium, PBB, PBDE, and 4 phthalates) must be met.",
     "online", "existing", "Now", CIT_EU_ROHS, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "Product must display the EU WEEE crossed-out wheelie-bin symbol on the device housing or packaging.",
     "print", "existing", "Now", CIT_EU_WEEE, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "EU Lot 7 Ecodesign regulation newly extends requirements to external power supplies, wireless chargers, and USB Type-C charging cables shipped with the product.",
     "online", "emerging", "2028-12-14", CIT_EU_LOT7, "2026-08-01"),
    ("EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing RED 2014/53/EU and IEC 62368-1 safety/EMC standard must be included with the product.",
     "either", "existing", "Now", CIT_EU_DOC, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Product must carry the EU RED graphic/marking and the CE mark on the device or its packaging.",
     "print", "existing", "Now", CIT_EU_RED_MARK, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Documentation must include an IEEE 802.11x radio compliance note for the integrated Wi-Fi/Bluetooth module.",
     "online", "existing", "Now", CIT_EU_8021X, "2026-09-09"),
    ("EU/UK", "battery_safety",
     "EU Battery Regulation (EU) 2023/1542 conformity applies to the notebook's internal battery: CE marking, a carbon-footprint declaration, and (phased in through 2027) digital battery passport / removability-and-replaceability documentation.",
     "online", "existing", "Now", CIT_EU_BATTERY_REG, TODAY),
    ("EU/UK", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available for the internal battery for air/sea freight.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("EU/UK", "cybersecurity",
     "EU Cyber Resilience Act obligations (secure-by-design documentation, vulnerability handling process, CE marking extension) phase in for products with digital elements; main obligations apply from Dec 11, 2027.",
     "online", "emerging", "2027-12-11", CIT_EU_CRA, "2026-08-01"),
    ("EU/UK", "trade_customs",
     "Customs approval for Safety, EMC, Energy, and Telecom is NOT required to be held specifically in the importer's (HP entity's) name for EU/EEA.",
     "online", "existing", "Now", CIT_EU_IMPORT, "2026-09-09"),
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC/Energy/Telecom is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "trade_customs",
     "A UK-specific conformity marking (UKCA) may be required alongside CE marking depending on the product's UK market entry route; final scope/date still being confirmed.",
     "print", "emerging", "TBD", CIT_UK_UKCA, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),
    ("EU/UK", "warranty_documentation",
     "Austria: if only a short-form warranty is provided in print, the full long-form guarantee statement must also be made available to the consumer on a \"permanent data carrier\"; a website link alone does not satisfy this.",
     "either", "existing", "Now", CIT_AT_WARR, "2025-05-01"),
    ("EU/UK", "warranty_documentation",
     "Setup instructions containing safety/regulatory notices must be provided in printed form for both commercial and consumer customers in the UK.",
     "print", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "environmental_sustainability",
     "No federal RoHS-equivalent restriction applies at the national level, but California Proposition 65 disclosure may apply if regulated substances are present.",
     "online", "existing", "Now", CIT_US_ROHS, "2026-09-09"),
    ("US", "environmental_sustainability",
     "ENERGY STAR labeling applies to notebook/mobile-workstation computers and is a common customer/procurement expectation though not a blanket federal mandate.",
     "online", "existing", "Now", CIT_US_ENERGY, "2026-09-09"),
    ("US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now", CIT_US_EMC, "2023-06-14"),
    ("US", "safety_emc_telecom",
     "FCC ID / regulatory model number must be marked on the product or accessible via e-label per 47 CFR Section 2.935.",
     "either", "existing", "Now", CIT_US_EMC_C, "2023-06-14"),
    ("US", "safety_emc_telecom",
     "USA Wireless: FCC Foreign Adversary Control Attestation requirement newly effective June 9, 2026, requiring supply-chain attestation prior to equipment authorization for the integrated Wi-Fi/Bluetooth radio.",
     "online", "emerging", "2026-06-09", CIT_US_ROADMAP, "2026-08-01"),
    ("US", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available for the internal battery for air/sea freight.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("US", "battery_safety",
     "IEC 62133-2 cell/pack safety certification applies to the internal lithium battery.",
     "online", "existing", "Now", CIT_IEC62133, TODAY),
    ("US", "cybersecurity",
     "USA Cybersecurity: FCC-adjacent IoT Labeling Program (\"Cyber Trust Mark\") is newly effective and may apply to network-connected computing devices; effective date still TBD.",
     "online", "emerging", "TBD", CIT_US_CYBERTRUST, "2026-08-01"),
    ("US", "trade_customs",
     "Customs approval for Telecom is required to be held in the importer's (HP entity's) name for US import; Safety, EMC, and Energy are not.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "trade_customs",
     "US customs review does not include a technical-regulations check for Safety, EMC, Energy, or Telecom at border entry for this product category.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),
    ("US", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-substance disclosure table must be included.",
     "print", "existing", "Now", CIT_CN_ROHS, "2026-09-09"),
    ("China", "environmental_sustainability",
     "China Energy Label / energy-efficiency disclosure applies to notebook/mobile-workstation computers; revised energy standard becomes effective Feb 1, 2027.",
     "print", "emerging", "2027-02-01", CIT_CN_ROADMAP, "2026-08-01"),
    ("China", "environmental_sustainability",
     "China Regulation Notice (product-specific compliance statement) must be included per WTR APJ ITE guidance.",
     "either", "existing", "Now", CIT_CN_REGNOTICE, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China Compulsory Certification (CCC) safety/EMC mark must be affixed to the product.",
     "print", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China SRRC radio-type approval must be obtained and the approval/model number disclosed in product documentation for the Wi-Fi/Bluetooth radio.",
     "online", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "battery_safety",
     "China's Mobile Power Bank traceability requirement (QR code) applies if the product ships with a battery-pack accessory; NPIs must comply by March 2026, sustaining products by March 2027.",
     "either", "emerging", "2027-03-01", CIT_CN_ROADMAP, "2026-08-01"),
    ("China", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available for the internal battery.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("China", "trade_customs",
     "Customs approval for Telecom, EMC, and Safety must be held in the importer's (HP entity's) name for import into China; Energy is not required.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "trade_customs",
     "Chinese customs review includes a technical-regulations check for EMC, Energy, and Telecom, with Safety review handled discretionarily (\"D\").",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),
    ("China", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers in China.",
     "online", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "environmental_sustainability",
     "Taiwan BSMI RoHS marking and hazardous-substance disclosure applies to Group 1-6 products.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "environmental_sustainability",
     "Taiwan's new Cybersecurity regulation for network-connected products newly applies to displays and digital cameras from Jan 1, 2028; scope for notebook/mobile-workstation computers is tracked separately under the cybersecurity domain below.",
     "online", "emerging", "2028-01-01", CIT_TW_ROADMAP, "2026-08-01"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan BSMI Safety/EMC certification mark must be affixed to the product.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan NCC statement and radio type-approval number must be included in product documentation for the Wi-Fi/Bluetooth radio.",
     "either", "existing", "Now", CIT_TW_NCC, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Documentation must include an EIRP disclosure and IEEE 802.11x compliance note for the integrated wireless radio.",
     "online", "existing", "Now", CIT_TW_EIRP, "2026-09-09"),
    ("Taiwan", "battery_safety",
     "Taiwan BSMI Battery Standard is in draft; official release expected 2H 2026, with enforcement beginning July 1, 2027, for products shipping with a battery pack.",
     "either", "emerging", "2027-07-01", CIT_TW_ROADMAP, "2026-08-01"),
    ("Taiwan", "cybersecurity",
     "Taiwan's new cybersecurity regulation for network-connected products applies from Jan 1, 2028; notebook/mobile-workstation computers are network-connected computing devices within its stated scope.",
     "online", "emerging", "2028-01-01", CIT_TW_CYBERSEC, "2026-08-01"),
    ("Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import into Taiwan; Energy is not required.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "trade_customs",
     "Taiwan customs review includes a technical-regulations check for Safety, EMC, Energy, and Telecom at border entry.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form, including product name/type/quantity, serial number, warranty coverage and period, and manufacturer/distributor name and address.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers in Taiwan.",
     "online", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ===========================================================================
# wired_ite_desktop - Commercial Desktop, Consumer Desktop, Commercial
# Workstation, Commercial Thin Client, Commercial RPOS, Docking Station,
# Hub, Hub Bundle, Switch, Expansion Module, Display
# (Display is excluded from cybersecurity rows via DOMAIN_EXCLUDE_PER_CATEGORY
# below - see that dict's comment for why.)
# ===========================================================================
TEMPLATE_ROWS["wired_ite_desktop"] = [
    ("EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances must be met.",
     "online", "existing", "Now", CIT_EU_ROHS, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "Product must display the EU WEEE crossed-out wheelie-bin symbol on the device housing or packaging.",
     "print", "existing", "Now", CIT_EU_WEEE, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "EU Lot 7 Ecodesign regulation newly extends requirements to external power supplies shipped with the product.",
     "online", "emerging", "2028-12-14", CIT_EU_LOT7, "2026-08-01"),
    ("EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing IEC 62368-1 safety/EMC standard (and the EMC Directive 2014/30/EU for the non-radio device) must be included with the product.",
     "either", "existing", "Now", CIT_EU_DOC, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Product must carry the CE mark on the device or its packaging.",
     "print", "existing", "Now", CIT_EU_RED_MARK, "2026-09-09"),
    ("EU/UK", "cybersecurity",
     "EU Cyber Resilience Act obligations (secure-by-design documentation, vulnerability handling process, CE marking extension) phase in for network-connected products with digital elements; main obligations apply from Dec 11, 2027.",
     "online", "emerging", "2027-12-11", CIT_EU_CRA, "2026-08-01"),
    ("EU/UK", "trade_customs",
     "Customs approval for Safety, EMC, and Energy is NOT required to be held specifically in the importer's (HP entity's) name for EU/EEA.",
     "online", "existing", "Now", CIT_EU_IMPORT, "2026-09-09"),
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC/Energy is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "trade_customs",
     "A UK-specific conformity marking (UKCA) may be required alongside CE marking depending on the product's UK market entry route; final scope/date still being confirmed.",
     "print", "emerging", "TBD", CIT_UK_UKCA, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),
    ("EU/UK", "warranty_documentation",
     "Austria: if only a short-form warranty is provided in print, the full long-form guarantee statement must also be made available to the consumer on a \"permanent data carrier\"; a website link alone does not satisfy this.",
     "either", "existing", "Now", CIT_AT_WARR, "2025-05-01"),
    ("EU/UK", "warranty_documentation",
     "Setup instructions containing safety/regulatory notices must be provided in printed form for both commercial and consumer customers in the UK.",
     "print", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "environmental_sustainability",
     "No federal RoHS-equivalent restriction applies at the national level, but California Proposition 65 disclosure may apply if regulated substances are present.",
     "online", "existing", "Now", CIT_US_ROHS, "2026-09-09"),
    ("US", "environmental_sustainability",
     "ENERGY STAR labeling applies to desktop/workstation-class computers and is a common customer/procurement expectation though not a blanket federal mandate.",
     "online", "existing", "Now", CIT_US_ENERGY, "2026-09-09"),
    ("US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now", CIT_US_EMC, "2023-06-14"),
    ("US", "safety_emc_telecom",
     "FCC ID / regulatory model number must be marked on the product or accessible via e-label per 47 CFR Section 2.935, where the specific configuration includes any FCC-regulated component.",
     "either", "existing", "Now", CIT_US_EMC_C, "2023-06-14"),
    ("US", "cybersecurity",
     "USA Cybersecurity: FCC-adjacent IoT Labeling Program (\"Cyber Trust Mark\") is newly effective and may apply to network-connected computing/infrastructure devices; effective date still TBD.",
     "online", "emerging", "TBD", CIT_US_CYBERTRUST, "2026-08-01"),
    ("US", "trade_customs",
     "US customs review does not include a technical-regulations check for Safety, EMC, or Energy at border entry for this product category.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),
    ("US", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-substance disclosure table must be included.",
     "print", "existing", "Now", CIT_CN_ROHS, "2026-09-09"),
    ("China", "environmental_sustainability",
     "China Energy Label / energy-efficiency disclosure applies; revised energy standard becomes effective Feb 1, 2027 (China's Energy rules split explicitly by device type - Energy-Computer, Energy-Monitor, Energy-Printer - in the source table).",
     "print", "emerging", "2027-02-01", CIT_CN_ROADMAP, "2026-08-01"),
    ("China", "safety_emc_telecom",
     "China Compulsory Certification (CCC) safety/EMC mark must be affixed to the product.",
     "print", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "trade_customs",
     "Customs approval for EMC and Safety must be held in the importer's (HP entity's) name for import into China; Energy is not required.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "trade_customs",
     "Chinese customs review includes a technical-regulations check for EMC and Energy, with Safety review handled discretionarily (\"D\").",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),
    ("China", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers in China.",
     "online", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "environmental_sustainability",
     "Taiwan BSMI RoHS marking and hazardous-substance disclosure applies to Group 1-6 products.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan BSMI Safety/EMC certification mark must be affixed to the product.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "cybersecurity",
     "Taiwan's new cybersecurity regulation for network-connected products newly applies to displays and digital cameras from Jan 1, 2028 (this is the same roadmap entry the original Bluetooth Headset dataset flagged, un-domained, before this domain existed).",
     "online", "emerging", "2028-01-01", CIT_TW_CYBERSEC, "2026-08-01"),
    ("Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import into Taiwan; Energy is not required.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "trade_customs",
     "Taiwan customs review includes a technical-regulations check for Safety, EMC, and Energy at border entry.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form, including product name/type/quantity, serial number, warranty coverage and period, and manufacturer/distributor name and address.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers in Taiwan.",
     "online", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ===========================================================================
# radio_audio_accessory_ear_coupled - Earbuds, Phone Handset
# ===========================================================================
TEMPLATE_ROWS["radio_audio_accessory_ear_coupled"] = [
    ("EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances must be met.",
     "online", "existing", "Now", CIT_EU_ROHS, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "Product must display the EU WEEE crossed-out wheelie-bin symbol on the device housing.",
     "print", "existing", "Now", CIT_EU_WEEE, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing RED 2014/53/EU and IEC 62368-1 safety/EMC standard must be included with the product.",
     "either", "existing", "Now", CIT_EU_DOC, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Product must carry the EU RED graphic/marking and the CE mark on the device or its packaging.",
     "print", "existing", "Now", CIT_EU_RED_MARK, "2026-09-09"),
    ("EU/UK", "hearing_aid_compatibility",
     "RED 2014/53/EU Article 3(3)(f) accessibility requirements (per harmonized standard EN 301 406) apply to radio equipment worn against the ear; the European Accessibility Act (EU) 2019/882 additionally covers accessibility of electronic-communications terminal equipment from June 28, 2025.",
     "online", "existing", "Now", CIT_EU_RED_HAC, TODAY),
    ("EU/UK", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available for the internal battery for air/sea freight.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("EU/UK", "battery_safety",
     "EU Battery Regulation (EU) 2023/1542 conformity (CE marking, carbon-footprint declaration) applies to the internal battery.",
     "online", "existing", "Now", CIT_EU_BATTERY_REG, TODAY),
    ("EU/UK", "trade_customs",
     "Customs approval for Safety, EMC, Energy, and Telecom is NOT required to be held specifically in the importer's (HP entity's) name for EU/EEA.",
     "online", "existing", "Now", CIT_EU_IMPORT, "2026-09-09"),
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC/Energy/Telecom is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),
    ("EU/UK", "warranty_documentation",
     "Setup instructions containing safety/regulatory notices must be provided in printed form for both commercial and consumer customers in the UK.",
     "print", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "environmental_sustainability",
     "No federal RoHS-equivalent restriction applies at the national level, but California Proposition 65 disclosure may apply if regulated substances are present.",
     "online", "existing", "Now", CIT_US_ROHS, "2026-09-09"),
    ("US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now", CIT_US_EMC, "2023-06-14"),
    ("US", "safety_emc_telecom",
     "FCC ID / regulatory model number must be marked on the product or accessible via e-label per 47 CFR Section 2.935.",
     "either", "existing", "Now", CIT_US_EMC_C, "2023-06-14"),
    ("US", "hearing_aid_compatibility",
     "FCC 47 CFR Section 20.19 Hearing Aid Compatibility technical requirements apply to handsets/earpieces used against the ear for telephone communication.",
     "online", "existing", "Now", CIT_FCC_HAC, TODAY),
    ("US", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available for the internal battery.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("US", "battery_safety",
     "IEC 62133-2 cell/pack safety certification applies to the internal lithium battery.",
     "online", "existing", "Now", CIT_IEC62133, TODAY),
    ("US", "trade_customs",
     "Customs approval for Telecom is required to be held in the importer's (HP entity's) name for US import; Safety, EMC, and Energy are not.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),
    ("US", "warranty_documentation",
     "HP EULA may be provided electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-substance disclosure table must be included.",
     "print", "existing", "Now", CIT_CN_ROHS, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China Compulsory Certification (CCC) safety/EMC mark must be affixed to the product where applicable to the accessory category.",
     "print", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China SRRC radio-type approval must be obtained and the approval/model number disclosed in product documentation for the Bluetooth/wireless radio.",
     "online", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "battery_safety",
     "China's Mobile Power Bank traceability requirement (QR code) applies if the product ships with a battery-pack accessory; NPIs must comply by March 2026, sustaining products by March 2027.",
     "either", "emerging", "2027-03-01", CIT_CN_ROADMAP, "2026-08-01"),
    ("China", "trade_customs",
     "Customs approval for Telecom, EMC, and Safety must be held in the importer's (HP entity's) name for import into China; Energy is not required.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy; a mandatory printed service/warranty card is also required per China's telecom card regulation.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "environmental_sustainability",
     "Taiwan BSMI RoHS marking and hazardous-substance disclosure applies to Group 1-6 accessory products.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan BSMI Safety/EMC certification mark must be affixed to the product for Group 1-6 category accessories.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan NCC statement and radio type-approval number must be included in product documentation for the Bluetooth/wireless radio.",
     "either", "existing", "Now", CIT_TW_NCC, "2026-09-09"),
    ("Taiwan", "hearing_aid_compatibility",
     "Taiwan NCC telecommunications terminal equipment accessibility technical regulations apply to handsets/earpieces used against the ear.",
     "online", "existing", "Now", CIT_TW_NCC_ACCESS, TODAY),
    ("Taiwan", "battery_safety",
     "Taiwan BSMI Battery Standard is in draft; official release expected 2H 2026, with enforcement beginning July 1, 2027, for products shipping with a battery pack.",
     "either", "emerging", "2027-07-01", CIT_TW_ROADMAP, "2026-08-01"),
    ("Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import into Taiwan; Energy is not required.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form, including product name/type/quantity, serial number, warranty coverage and period, and manufacturer/distributor name and address.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ===========================================================================
# radio_accessory_not_ear_coupled - Remote Control
# ===========================================================================
TEMPLATE_ROWS["radio_accessory_not_ear_coupled"] = [
    ("EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances must be met.",
     "online", "existing", "Now", CIT_EU_ROHS, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing RED 2014/53/EU and IEC 62368-1 safety/EMC standard must be included with the product.",
     "either", "existing", "Now", CIT_EU_DOC, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Product must carry the EU RED graphic/marking and the CE mark on the device or its packaging.",
     "print", "existing", "Now", CIT_EU_RED_MARK, "2026-09-09"),
    ("EU/UK", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available where the remote ships with a built-in rechargeable cell (rather than user-replaceable primary cells).",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC/Telecom is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now", CIT_US_EMC, "2023-06-14"),
    ("US", "safety_emc_telecom",
     "FCC ID / regulatory model number must be marked on the product or accessible via e-label per 47 CFR Section 2.935.",
     "either", "existing", "Now", CIT_US_EMC_C, "2023-06-14"),
    ("US", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available where the remote ships with a built-in rechargeable cell.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("US", "trade_customs",
     "Customs approval for Telecom is required to be held in the importer's (HP entity's) name for US import; Safety and EMC are not.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-substance disclosure table must be included.",
     "print", "existing", "Now", CIT_CN_ROHS, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China SRRC radio-type approval must be obtained and the approval/model number disclosed in product documentation for the Bluetooth radio.",
     "online", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "trade_customs",
     "Customs approval for Telecom and EMC must be held in the importer's (HP entity's) name for import into China.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "safety_emc_telecom",
     "Taiwan NCC statement and radio type-approval number must be included in product documentation for the Bluetooth radio.",
     "either", "existing", "Now", CIT_TW_NCC, "2026-09-09"),
    ("Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import into Taiwan.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ===========================================================================
# wired_ite_ear_coupled - Phone, Wired Headset
# (Phone is a networked VoIP endpoint -> gets cybersecurity rows; Wired
# Headset does not - see DOMAIN_EXCLUDE_PER_CATEGORY / row-level exclusion
# for how the two are told apart within one shared template.)
# ===========================================================================
TEMPLATE_ROWS["wired_ite_ear_coupled"] = [
    ("EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances must be met.",
     "online", "existing", "Now", CIT_EU_ROHS, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "Product must display the EU WEEE crossed-out wheelie-bin symbol on the device housing.",
     "print", "existing", "Now", CIT_EU_WEEE, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing IEC 62368-1 safety/EMC standard (EMC Directive 2014/30/EU; RED does not apply - no radio transmitter) must be included with the product.",
     "either", "existing", "Now", CIT_EU_DOC, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Product must carry the CE mark on the device or its packaging.",
     "print", "existing", "Now", CIT_EU_RED_MARK, "2026-09-09"),
    ("EU/UK", "hearing_aid_compatibility",
     "The European Accessibility Act (EU) 2019/882 covers accessibility of electronic-communications terminal equipment worn against or held to the ear, effective from June 28, 2025.",
     "online", "existing", "Now", CIT_EAA, TODAY),
    ("EU/UK", "cybersecurity",
     "EU Cyber Resilience Act obligations (secure-by-design documentation, vulnerability handling process, CE marking extension) phase in for network-connected products with digital elements; main obligations apply from Dec 11, 2027.",
     "online", "emerging", "2027-12-11", CIT_EU_CRA, "2026-08-01"),
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),
    ("EU/UK", "warranty_documentation",
     "Setup instructions containing safety/regulatory notices must be provided in printed form for both commercial and consumer customers in the UK.",
     "print", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "environmental_sustainability",
     "No federal RoHS-equivalent restriction applies at the national level, but California Proposition 65 disclosure may apply if regulated substances are present.",
     "online", "existing", "Now", CIT_US_ROHS, "2026-09-09"),
    ("US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now", CIT_US_EMC, "2023-06-14"),
    ("US", "hearing_aid_compatibility",
     "FCC 47 CFR Section 20.19 Hearing Aid Compatibility technical requirements apply to handsets/earpieces used against the ear for telephone communication.",
     "online", "existing", "Now", CIT_FCC_HAC, TODAY),
    ("US", "cybersecurity",
     "USA Cybersecurity: FCC-adjacent IoT Labeling Program (\"Cyber Trust Mark\") is newly effective and may apply to network-connected telecom endpoint devices; effective date still TBD.",
     "online", "emerging", "TBD", CIT_US_CYBERTRUST, "2026-08-01"),
    ("US", "trade_customs",
     "US customs review does not include a technical-regulations check for Safety or EMC at border entry for this product category.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-substance disclosure table must be included.",
     "print", "existing", "Now", CIT_CN_ROHS, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China Compulsory Certification (CCC) safety/EMC mark must be affixed to the product.",
     "print", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "trade_customs",
     "Customs approval for EMC and Safety must be held in the importer's (HP entity's) name for import into China.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "environmental_sustainability",
     "Taiwan BSMI RoHS marking and hazardous-substance disclosure applies to Group 1-6 products.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan BSMI Safety/EMC certification mark must be affixed to the product.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "hearing_aid_compatibility",
     "Taiwan NCC telecommunications terminal equipment accessibility technical regulations apply to handsets/earpieces used against the ear.",
     "online", "existing", "Now", CIT_TW_NCC_ACCESS, TODAY),
    ("Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import into Taiwan.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ===========================================================================
# wired_uc_av_not_ear_coupled - Video Conferencing, Video Bar, Video Bar
# Bundle, Video Conferencing Bundle, Speaker Phone, Audio Bridge, Video
# Camera, Microphone
# (cybersecurity scoped via ROW_EXCLUDE_PER_CATEGORY to just the networked
# UC endpoints - Video Camera and Microphone are excluded, see below)
# ===========================================================================
TEMPLATE_ROWS["wired_uc_av_not_ear_coupled"] = [
    ("EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances must be met.",
     "online", "existing", "Now", CIT_EU_ROHS, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "Product must display the EU WEEE crossed-out wheelie-bin symbol on the device housing.",
     "print", "existing", "Now", CIT_EU_WEEE, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing IEC 62368-1 safety/EMC standard (EMC Directive 2014/30/EU; RED does not apply to the wired base configuration) must be included with the product.",
     "either", "existing", "Now", CIT_EU_DOC, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Product must carry the CE mark on the device or its packaging.",
     "print", "existing", "Now", CIT_EU_RED_MARK, "2026-09-09"),
    ("EU/UK", "cybersecurity",
     "EU Cyber Resilience Act obligations (secure-by-design documentation, vulnerability handling process, CE marking extension) phase in for network-connected products with digital elements; main obligations apply from Dec 11, 2027.",
     "online", "emerging", "2027-12-11", CIT_EU_CRA, "2026-08-01"),
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),
    ("EU/UK", "warranty_documentation",
     "Setup instructions containing safety/regulatory notices must be provided in printed form for both commercial and consumer customers in the UK.",
     "print", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "environmental_sustainability",
     "No federal RoHS-equivalent restriction applies at the national level, but California Proposition 65 disclosure may apply if regulated substances are present.",
     "online", "existing", "Now", CIT_US_ROHS, "2026-09-09"),
    ("US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now", CIT_US_EMC, "2023-06-14"),
    ("US", "cybersecurity",
     "USA Cybersecurity: FCC-adjacent IoT Labeling Program (\"Cyber Trust Mark\") is newly effective and may apply to network-connected UC endpoint devices; effective date still TBD.",
     "online", "emerging", "TBD", CIT_US_CYBERTRUST, "2026-08-01"),
    ("US", "trade_customs",
     "US customs review does not include a technical-regulations check for Safety or EMC at border entry for this product category.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-substance disclosure table must be included.",
     "print", "existing", "Now", CIT_CN_ROHS, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China Compulsory Certification (CCC) safety/EMC mark must be affixed to the product.",
     "print", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "trade_customs",
     "Customs approval for EMC and Safety must be held in the importer's (HP entity's) name for import into China.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "environmental_sustainability",
     "Taiwan BSMI RoHS marking and hazardous-substance disclosure applies to Group 1-6 products.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan BSMI Safety/EMC certification mark must be affixed to the product.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "cybersecurity",
     "Taiwan's new cybersecurity regulation for network-connected products applies from Jan 1, 2028; networked UC endpoints fall within its stated scope of network-connected products.",
     "online", "emerging", "2028-01-01", CIT_TW_CYBERSEC, "2026-08-01"),
    ("Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import into Taiwan.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ===========================================================================
# power_and_adapter_accessory - Adapter, Adapters / Cables, VoIP Adapter,
# wall charger, Power Requirements - AC Adapter, Power Requirements - Battery
# (Power Requirements - Battery is the one category where battery_safety
# rows apply to the item itself rather than to an embedded cell inside a
# larger device - handled via ROW_EXCLUDE_PER_CATEGORY for the other five
# categories in this archetype, which do not ship a user-facing battery on
# their own.)
# ===========================================================================
TEMPLATE_ROWS["power_and_adapter_accessory"] = [
    ("EU/UK", "environmental_sustainability",
     "RoHS Directive 2011/65/EU (as amended by 2015/863) restricting hazardous substances must be met.",
     "online", "existing", "Now", CIT_EU_ROHS, "2026-09-09"),
    ("EU/UK", "environmental_sustainability",
     "EU Lot 7 Ecodesign regulation newly extends requirements to external power supplies, wireless chargers, and USB Type-C charging cables.",
     "online", "emerging", "2028-12-14", CIT_EU_LOT7, "2026-08-01"),
    ("EU/UK", "safety_emc_telecom",
     "EU/UK Simplified Declaration of Conformity referencing IEC 62368-1 safety/EMC standard must be included with the product.",
     "either", "existing", "Now", CIT_EU_DOC, "2026-09-09"),
    ("EU/UK", "safety_emc_telecom",
     "Product must carry the CE mark on the device or its packaging.",
     "print", "existing", "Now", CIT_EU_RED_MARK, "2026-09-09"),
    ("EU/UK", "battery_safety",
     "EU Battery Regulation (EU) 2023/1542 conformity (CE marking, carbon-footprint declaration) applies to the battery.",
     "online", "existing", "Now", CIT_EU_BATTERY_REG, TODAY),
    ("EU/UK", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available for air/sea freight.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance for Safety/EMC/Energy is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry.",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "environmental_sustainability",
     "No federal RoHS-equivalent restriction applies at the national level, but California Proposition 65 disclosure may apply if regulated substances are present.",
     "online", "existing", "Now", CIT_US_ROHS, "2026-09-09"),
    ("US", "safety_emc_telecom",
     "FCC 47 CFR Part 15 Subpart B unintentional-radiator limits apply; compliance is authorized via Supplier's Declaration of Conformity (SDoC).",
     "online", "existing", "Now", CIT_US_EMC, "2023-06-14"),
    ("US", "safety_emc_telecom",
     "DOE energy-conservation standards (10 CFR Part 430/431, external power supply efficiency) apply where the item is itself an external power supply.",
     "online", "existing", "Now", CIT_US_ENERGY, "2026-09-09"),
    ("US", "battery_safety",
     "UN38.3 lithium-battery transport testing documentation must be available.",
     "online", "existing", "Now", CIT_UN38_3, TODAY),
    ("US", "battery_safety",
     "IEC 62133-2 cell/pack safety certification applies to the battery.",
     "online", "existing", "Now", CIT_IEC62133, TODAY),
    ("US", "trade_customs",
     "US customs review does not include a technical-regulations check for Safety, EMC, or Energy at border entry for this product category.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "environmental_sustainability",
     "China RoHS registration is expanding to explicitly cover scanners, peripherals, and external power supply accessories, effective Aug 1, 2027.",
     "online", "emerging", "2027-08-01", CIT_CN_ROADMAP, "2026-08-01"),
    ("China", "environmental_sustainability",
     "China RoHS (Management Methods for Restriction of Hazardous Substances) marking and hazardous-substance disclosure table must be included.",
     "print", "existing", "Now", CIT_CN_ROHS, "2026-09-09"),
    ("China", "safety_emc_telecom",
     "China Compulsory Certification (CCC) safety/EMC mark must be affixed to the product where applicable to the accessory category.",
     "print", "existing", "Now", CIT_CN_CCC, "2026-09-09"),
    ("China", "battery_safety",
     "China's Mobile Power Bank traceability requirement (QR code) applies to battery-pack accessories; NPIs must comply by March 2026, sustaining products by March 2027.",
     "either", "emerging", "2027-03-01", CIT_CN_ROADMAP, "2026-08-01"),
    ("China", "trade_customs",
     "Customs approval for EMC and Safety must be held in the importer's (HP entity's) name for import into China; Energy is not required.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "environmental_sustainability",
     "Taiwan BSMI RoHS marking and hazardous-substance disclosure applies to Group 1-6 accessory products.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "safety_emc_telecom",
     "Taiwan BSMI Safety/EMC certification mark must be affixed to the product for Group 1-6 category accessories.",
     "print", "existing", "Now", CIT_TW_BSMI, "2026-09-09"),
    ("Taiwan", "battery_safety",
     "Taiwan BSMI Battery Standard is in draft; official release expected 2H 2026, with enforcement beginning July 1, 2027.",
     "either", "emerging", "2027-07-01", CIT_TW_ROADMAP, "2026-08-01"),
    ("Taiwan", "trade_customs",
     "Customs approval for Safety and EMC must be held in the importer's (HP entity's) name for import into Taiwan.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ===========================================================================
# mechanical_passive_accessory - Accessory / Service Part, Bags and Cases,
# BRACKET, Cable Clips, Cushion, Foam, Holders and Stands, Mounting Kit,
# Pen, Plastic Moldings, Plastic Plate, Polarizing Filter, RACK, Stand
# Only trade_customs + warranty_documentation - see archetype comment above
# for why environmental/safety/cybersecurity/battery/HAC are deliberately
# left with zero rows (not applicable, not "unknown").
# ===========================================================================
TEMPLATE_ROWS["mechanical_passive_accessory"] = [
    ("EU/UK", "trade_customs",
     "Customs review of technical-regulation compliance is handled on a discretionary, case-by-case basis (\"D\") at EU/UK border entry, consistent with the generic ITE-accessory importer-control matrix (no distinct rule set exists for non-electronic accessories in the source material).",
     "online", "existing", "Now", CIT_EU_IMPORT_D, "2026-09-09"),
    ("EU/UK", "warranty_documentation",
     "UK warranty may be provided electronically for both consumer and commercial customers, but the customer must be given the option to request a printed copy.",
     "either", "existing", "Now", CIT_UK_WARR, "2025-05-01"),

    ("US", "trade_customs",
     "US customs review does not include a technical-regulations check at border entry for this product category, consistent with the generic ITE-accessory importer-control matrix.",
     "online", "existing", "Now", CIT_US_IMPORT, "2026-09-09"),
    ("US", "warranty_documentation",
     "US warranty may be provided fully electronically for both consumer and commercial customers.",
     "online", "existing", "Now", CIT_US_WARR, "2023-06-23"),

    ("China", "trade_customs",
     "Chinese customs review for accessory items in this category is handled discretionarily (\"D\"), consistent with the generic ITE-accessory importer-control matrix.",
     "online", "existing", "Now", CIT_CN_IMPORT, "2026-09-09"),
    ("China", "warranty_documentation",
     "China warranty may be provided electronically with clear instructions for accessing it, plus the option of a printed copy.",
     "either", "existing", "Now", CIT_CN_WARR, "2026-09-09"),

    ("Taiwan", "trade_customs",
     "Taiwan customs review for accessory items in this category is handled consistent with the generic ITE-accessory importer-control matrix; no product-specific Safety/EMC certification applies since the item contains no active electronics.",
     "online", "existing", "Now", CIT_TW_IMPORT, "2026-09-09"),
    ("Taiwan", "warranty_documentation",
     "Taiwan law (Consumer Protection Act Art. 25) requires the warranty document to be provided in printed form.",
     "print", "existing", "Now", CIT_TW_WARR, "2026-09-09"),
]

# ---------------------------------------------------------------------------
# Per-category refinements - the handful of cases where one shared template
# doesn't apply uniformly to every category in its archetype. Each entry
# documents the real evidence behind the refinement (see archetype comments
# above for the fuller version of each).
# ---------------------------------------------------------------------------

# Full-domain removal: this category gets none of the archetype's rows for
# the named domain(s) at all.
DOMAIN_EXCLUDE_PER_CATEGORY = {
    # Wired Headset is not a networked device on its own (no independent
    # network/OS stack) - Phone (a VoIP endpoint) keeps the archetype's
    # cybersecurity rows.
    "Wired Headset": {"cybersecurity"},
    # Video Camera and Microphone are USB/analog peripherals that ride on a
    # host device's network connection rather than having their own -
    # Video Conferencing, Video Bar(+Bundle), Video Conferencing Bundle,
    # Speaker Phone, and Audio Bridge are themselves networked UC endpoints
    # and keep the archetype's cybersecurity rows.
    "Video Camera": {"cybersecurity"},
    "Microphone": {"cybersecurity"},
    # Only Power Requirements - Battery ships a user-facing battery on its
    # own within this archetype - the other five are the charger/cable/
    # adapter around a battery, not the cell itself.
    "Adapter": {"battery_safety"},
    "Adapters / Cables": {"battery_safety"},
    "VoIP Adapter": {"battery_safety"},
    "wall charger": {"battery_safety"},
    "Power Requirements - AC Adapter": {"battery_safety"},
}

# Row-level (region, domain) removal - for a partial domain exclusion where
# full-domain removal above would be too broad.
ROW_EXCLUDE_PER_CATEGORY = {
    # Display keeps ONLY the Taiwan cybersecurity row, because that is the
    # one row in this whole dataset with direct evidence naming displays
    # specifically (the ER Roadmap's Taiwan cybersecurity entry explicitly
    # lists "displays and digital cameras" in scope). The EU/US cybersecurity
    # rows in the wired_ite_desktop template are written for networked
    # compute/infra devices in general and were not verified to name
    # standalone displays - leaving them off Display is the honest choice
    # per Grounding Rule 3 (a real gap, not "not required").
    "Display": {("EU/UK", "cybersecurity"), ("US", "cybersecurity")},
}


def _load_existing_bluetooth_headset_rows() -> list[list[str]]:
    """
    Read the CURRENT data/compliance_requirements.csv (the one build_data.py
    produced) and pull out only its Bluetooth Headset rows, verbatim, before
    this script overwrites the file. This is how those original 48
    hand-authored rows survive the regeneration unchanged.
    """
    with open(EXISTING_HEADSET_ROWS_SOURCE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [row for row in reader if row and row[0] == "Bluetooth Headset"]
    return header, rows


def _generate_new_rows() -> list[list[str]]:
    rows = []
    for archetype, categories in ARCHETYPES.items():
        template = TEMPLATE_ROWS[archetype]
        for category in categories:
            domain_exclude = DOMAIN_EXCLUDE_PER_CATEGORY.get(category, set())
            row_exclude = ROW_EXCLUDE_PER_CATEGORY.get(category, set())
            for (region, domain, requirement, doc_format, status,
                 must_comply_by, citation, last_verified) in template:
                if domain in domain_exclude:
                    continue
                if (region, domain) in row_exclude:
                    continue
                rows.append([
                    category, region, domain, requirement, doc_format,
                    status, must_comply_by, citation, last_verified,
                ])
    return rows


def main() -> None:
    header, headset_rows = _load_existing_bluetooth_headset_rows()
    assert len(headset_rows) == 48, (
        f"Expected the original 48 Bluetooth Headset rows, found {len(headset_rows)} "
        "- refusing to regenerate on top of an unexpected starting file."
    )

    # Sanity check: every category this script classifies actually exists
    # in product_master.csv, and every category in product_master.csv
    # (other than Bluetooth Headset) is classified into exactly one
    # archetype - catches a renamed/added category silently getting zero
    # compliance rows.
    product_master_path = os.path.join(DATA_DIR, "product_master.csv")
    with open(product_master_path, newline="", encoding="utf-8") as f:
        catalog_categories = {row["category"] for row in csv.DictReader(f)}
    expected = catalog_categories - {"Bluetooth Headset"}
    missing = expected - ALL_CLASSIFIED_CATEGORIES
    extra = ALL_CLASSIFIED_CATEGORIES - expected
    assert not missing, f"Categories in product_master.csv with no archetype: {sorted(missing)}"
    assert not extra, f"Archetype categories not found in product_master.csv: {sorted(extra)}"

    new_rows = _generate_new_rows()

    all_rows = headset_rows + new_rows
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(all_rows)

    by_domain = {}
    for r in new_rows:
        by_domain[r[2]] = by_domain.get(r[2], 0) + 1

    print(f"Wrote {len(all_rows)} total rows ({len(headset_rows)} original Bluetooth "
          f"Headset rows + {len(new_rows)} newly generated rows) across "
          f"{len(ALL_CLASSIFIED_CATEGORIES) + 1} categories to {OUT_PATH}")
    print("New rows by domain:")
    for domain, _label in [
        ("environmental_sustainability", ""), ("safety_emc_telecom", ""),
        ("hearing_aid_compatibility", ""), ("cybersecurity", ""),
        ("battery_safety", ""), ("trade_customs", ""),
        ("warranty_documentation", ""),
    ]:
        print(f"  {domain}: {by_domain.get(domain, 0)}")


if __name__ == "__main__":
    main()
