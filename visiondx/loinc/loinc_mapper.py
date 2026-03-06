"""
VisionDX — LOINC Parameter Mapper

Maps lab parameter names (in any format) to LOINC codes and canonical names.
Used to normalize extracted parameters before running the disease engine.

Supports:
  - Exact match
  - Alias match (150+ variants)
  - Fuzzy match (difflib) as fallback
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field


@dataclass
class LoincEntry:
    code: str                  # LOINC code e.g. "2345-7"
    canonical: str             # Standard display name e.g. "Glucose"
    aliases: list[str] = field(default_factory=list)
    unit: str = ""
    category: str = ""         # Blood, Urine, Hormone, etc.
    description: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Embedded LOINC Reference Table (Top 200 common lab tests)
# Source: https://loinc.org/  (embedded subset for offline use)
# ─────────────────────────────────────────────────────────────────────────────
LOINC_TABLE: list[LoincEntry] = [
    # ── Glucose / Diabetes ────────────────────────────────────────────────────
    LoincEntry("2345-7", "Glucose", ["glucose", "fbs", "fasting blood sugar", "fasting glucose",
        "blood glucose", "rbs", "random blood sugar", "blood sugar", "bs"], "mg/dL", "Metabolic"),
    LoincEntry("4548-4", "HbA1c",  ["hba1c", "hb a1c", "hemoglobin a1c", "glycated hemoglobin",
        "glycosylated hemoglobin", "hb a", "hb a l", "a1c", "hba1%"], "%", "Metabolic"),
    LoincEntry("20448-7","Insulin", ["insulin", "fasting insulin", "serum insulin"], "μIU/mL","Hormone"),

    # ── Hemoglobin / Blood Count ──────────────────────────────────────────────
    LoincEntry("718-7",  "Hemoglobin",  ["hemoglobin", "haemoglobin", "hgb", "hb", "hb conc"], "g/dL","Hematology"),
    LoincEntry("789-8",  "RBC",         ["rbc", "red blood cells", "red blood cell count", "erythrocytes"], "×10⁶/μL","Hematology"),
    LoincEntry("4544-3", "Hematocrit",  ["hematocrit", "haematocrit", "hct", "pcv", "packed cell volume"], "%", "Hematology"),
    LoincEntry("787-2",  "MCV",         ["mcv", "mean corpuscular volume", "mean cell volume"], "fL","Hematology"),
    LoincEntry("785-6",  "MCH",         ["mch", "mean corpuscular hemoglobin"], "pg","Hematology"),
    LoincEntry("786-4",  "MCHC",        ["mchc", "mean corpuscular hemoglobin concentration"], "g/dL","Hematology"),
    LoincEntry("788-0",  "RDW",         ["rdw", "red cell distribution width"], "%","Hematology"),

    # ── WBC ──────────────────────────────────────────────────────────────────
    LoincEntry("6690-2", "WBC",         ["wbc", "white blood cells", "leukocytes", "white cell count",
        "total wbc", "total leukocyte count", "tlc"], "×10³/μL","Hematology"),
    LoincEntry("26505-0","Neutrophils", ["neutrophils", "neut", "neutrophil count", "polymorphs",
        "segmented neutrophils", "polys"], "%","Hematology"),
    LoincEntry("26474-7","Lymphocytes", ["lymphocytes", "lymph", "lymphocyte count"], "%","Hematology"),
    LoincEntry("26484-6","Monocytes",   ["monocytes", "mono"], "%","Hematology"),
    LoincEntry("26449-9","Eosinophils", ["eosinophils", "eo", "eos", "eosinophil count"], "%","Hematology"),
    LoincEntry("26450-7","Basophils",   ["basophils", "baso"], "%","Hematology"),

    # ── Platelets ─────────────────────────────────────────────────────────────
    LoincEntry("777-3",  "Platelets",   ["platelets", "platelet count", "plt", "thrombocytes"], "×10³/μL","Hematology"),
    LoincEntry("32623-1","MPV",         ["mpv", "mpv h", "mean platelet volume"], "fL","Hematology"),

    # ── Iron ─────────────────────────────────────────────────────────────────
    LoincEntry("2498-4", "Serum Iron",  ["serum iron", "iron", "fe", "s-iron"], "μg/dL","Hematology"),
    LoincEntry("2276-4", "Ferritin",    ["ferritin", "serum ferritin", "s-ferritin"], "ng/mL","Hematology"),
    LoincEntry("2500-7", "TIBC",        ["tibc", "total iron binding capacity", "iron binding capacity"], "μg/dL","Hematology"),
    LoincEntry("35215-3","Transferrin Saturation",["transferrin saturation", "tsat", "sat%"], "%","Hematology"),

    # ── Kidney ────────────────────────────────────────────────────────────────
    LoincEntry("2160-0", "Creatinine",  ["creatinine", "serum creatinine", "s-creatinine", "crea"], "mg/dL","Renal"),
    LoincEntry("3094-0", "BUN",         ["bun", "blood urea nitrogen", "urea nitrogen"], "mg/dL","Renal"),
    LoincEntry("22664-7","Urea",        ["urea", "serum urea", "urea l", "blood urea"], "mg/dL","Renal"),
    LoincEntry("33914-3","eGFR",        ["egfr", "estimated gfr", "glomerular filtration rate", "gfr"], "mL/min","Renal"),
    LoincEntry("3084-1", "Uric Acid",   ["uric acid", "urate", "uric acid serum"], "mg/dL","Renal"),
    LoincEntry("2823-3", "Potassium",   ["potassium", "k", "k+", "serum potassium"], "mEq/L","Electrolyte"),
    LoincEntry("2951-2", "Sodium",      ["sodium", "na", "na+", "serum sodium"], "mEq/L","Electrolyte"),
    LoincEntry("2075-0", "Chloride",    ["chloride", "cl", "cl-"], "mEq/L","Electrolyte"),
    LoincEntry("17861-6","Calcium",     ["calcium", "ca", "serum calcium"], "mg/dL","Electrolyte"),
    LoincEntry("19123-9","Magnesium",   ["magnesium", "mg", "serum magnesium"], "mg/dL","Electrolyte"),
    LoincEntry("2777-1", "Phosphorus",  ["phosphorus", "phosphate", "p", "serum phosphorus"], "mg/dL","Electrolyte"),

    # ── Liver ─────────────────────────────────────────────────────────────────
    LoincEntry("1742-6", "ALT",         ["alt", "sgpt", "alanine aminotransferase", "alanine transaminase"], "U/L","Hepatic"),
    LoincEntry("1920-8", "AST",         ["ast", "sgot", "aspartate aminotransferase", "aspartate transaminase"], "U/L","Hepatic"),
    LoincEntry("1975-2", "Bilirubin Total",["bilirubin", "total bilirubin", "bilirubin total", "t-bil"], "mg/dL","Hepatic"),
    LoincEntry("1968-7", "Bilirubin Direct",["direct bilirubin", "direct bil", "conjugated bilirubin", "d-bil"], "mg/dL","Hepatic"),
    LoincEntry("6768-6", "ALP",         ["alp", "alkaline phosphatase", "alk phos"], "U/L","Hepatic"),
    LoincEntry("2324-2", "GGT",         ["ggt", "gamma gt", "gamma-glutamyl transferase", "gamma glutamyl", "ggt h"], "U/L","Hepatic"),
    LoincEntry("1751-7", "Albumin",     ["albumin", "serum albumin", "alb"], "g/dL","Hepatic"),
    LoincEntry("2885-2", "Total Protein",["protein", "total protein", "tp", "serum protein"], "g/dL","Hepatic"),

    # ── Lipids ────────────────────────────────────────────────────────────────
    LoincEntry("2093-3", "Total Cholesterol",["cholesterol", "total cholesterol", "chol", "tc"], "mg/dL","Lipid"),
    LoincEntry("2089-1", "LDL Cholesterol",  ["ldl", "ldl cholesterol", "ldl-c", "low density lipoprotein"], "mg/dL","Lipid"),
    LoincEntry("2085-9", "HDL Cholesterol",  ["hdl", "hdl cholesterol", "hdl-c", "high density lipoprotein"], "mg/dL","Lipid"),
    LoincEntry("2571-8", "Triglycerides",    ["triglycerides", "tg", "trig", "trigs", "tag"], "mg/dL","Lipid"),
    LoincEntry("13457-7","LDL/HDL Ratio",   ["ldl/hdl ratio", "ldl hdl ratio"], "ratio","Lipid"),
    LoincEntry("10835-7","Non-HDL Cholesterol",["non-hdl", "non hdl cholesterol", "non-hdl chol"], "mg/dL","Lipid"),

    # ── Thyroid ───────────────────────────────────────────────────────────────
    LoincEntry("3016-3", "TSH",         ["tsh", "thyroid stimulating hormone", "thyrotropin"], "mIU/L","Endocrine"),
    LoincEntry("3051-0", "T3",          ["t3", "triiodothyronine", "total t3"], "ng/dL","Endocrine"),
    LoincEntry("3053-6", "T4",          ["t4", "thyroxine", "total t4"], "μg/dL","Endocrine"),
    LoincEntry("3052-8", "Free T3",     ["free t3", "ft3", "free triiodothyronine", "ft3 h", "ft3 l"], "pg/mL","Endocrine"),
    LoincEntry("3054-4", "Free T4",     ["free t4", "ft4", "free thyroxine"], "ng/dL","Endocrine"),

    # ── Vitamins ──────────────────────────────────────────────────────────────
    LoincEntry("1989-3", "Vitamin D",   ["vitamin d", "vitamin d3", "25-oh vitamin d", "25 oh vitamin d",
        "25-hydroxyvitamin d", "vitd", "25(oh)d", "25 ohd"], "ng/mL","Nutritional"),
    LoincEntry("2132-9", "Vitamin B12", ["vitamin b12", "b12", "cyanocobalamin", "cobalamin",
        "serum b12", "vit b12"], "pg/mL","Nutritional"),
    LoincEntry("2284-8", "Folate",      ["folate", "folic acid", "vitamin b9", "serum folate",
        "fol", "pteroylglutamic acid"], "ng/mL","Nutritional"),
    LoincEntry("2741-7", "Vitamin B6",  ["vitamin b6", "pyridoxine", "vit b6", "b6"], "nmol/L","Nutritional"),

    # ── Cardiovascular / Inflammatory ─────────────────────────────────────────
    LoincEntry("13965-9","Homocysteine",["homocysteine", "homocysteine serum", "homocysteine, serum",
        "homocysteine, serum h", "serum h", "hcy"], "μmol/L","Cardiovascular"),
    LoincEntry("30522-7","hs-CRP",      ["hs-crp", "high sensitivity crp", "hscrp", "hsCRP",
        "high sens crp", "crp hs"], "mg/L","Inflammatory"),
    LoincEntry("1988-5", "CRP",         ["crp", "c-reactive protein", "c reactive protein"], "mg/L","Inflammatory"),
    LoincEntry("4537-7", "ESR",         ["esr", "erythrocyte sedimentation rate", "sed rate",
        "sedimentation rate", "westergren"], "mm/hr","Inflammatory"),

    # ── Allergy / Immunology ──────────────────────────────────────────────────
    LoincEntry("19113-0","IgE",         ["ige", "ige h", "total ige", "immunoglobulin e",
        "serum ige", "ige total"], "IU/mL","Immunologic"),
    LoincEntry("2465-3", "IgA",         ["iga", "immunoglobulin a", "serum iga"], "mg/dL","Immunologic"),
    LoincEntry("2460-4", "IgG",         ["igg", "immunoglobulin g", "serum igg"], "mg/dL","Immunologic"),
    LoincEntry("2472-9", "IgM",         ["igm", "immunoglobulin m", "serum igm"], "mg/dL","Immunologic"),

    # ── Hormones ──────────────────────────────────────────────────────────────
    LoincEntry("20448-7","Cortisol",    ["cortisol", "serum cortisol", "morning cortisol"], "μg/dL","Hormone"),
    LoincEntry("2986-8", "Testosterone",["testosterone", "total testosterone", "serum testosterone"], "ng/dL","Hormone"),
    LoincEntry("2243-4", "Estradiol",   ["estradiol", "e2", "serum estradiol", "17-beta estradiol"], "pg/mL","Hormone"),
    LoincEntry("2857-1", "Prolactin",   ["prolactin", "serum prolactin", "prl"], "ng/mL","Hormone"),
    LoincEntry("10501-5","LH",          ["lh", "luteinizing hormone", "luteinising hormone"], "IU/L","Hormone"),
    LoincEntry("15067-2","FSH",         ["fsh", "follicle stimulating hormone"], "IU/L","Hormone"),

    # ── Pancreatic ────────────────────────────────────────────────────────────
    LoincEntry("1798-8", "Amylase",     ["amylase", "serum amylase", "salivary amylase"], "U/L","Pancreatic"),
    LoincEntry("3040-3", "Lipase",      ["lipase", "serum lipase"], "U/L","Pancreatic"),

    # ── Infection Markers ─────────────────────────────────────────────────────
    LoincEntry("75241-0","Procalcitonin",["procalcitonin", "pct", "serum procalcitonin"], "ng/mL","Infectious"),
]


# ── Build lookup index ────────────────────────────────────────────────────────
_CODE_INDEX: dict[str, LoincEntry] = {e.code: e for e in LOINC_TABLE}
_CANONICAL_INDEX: dict[str, LoincEntry] = {e.canonical.lower(): e for e in LOINC_TABLE}
_ALIAS_INDEX: dict[str, LoincEntry] = {}
for entry in LOINC_TABLE:
    for alias in entry.aliases:
        _ALIAS_INDEX[alias.lower()] = entry


def _clean(name: str) -> str:
    """Normalize a parameter name for lookup."""
    import re
    n = name.lower().strip()
    # Remove trailing HIGH/LOW flags (lab reports often append " H" or " L")
    n = re.sub(r"\s+[hl]$", "", n).strip()
    return n


def map_parameter_to_loinc(parameter_name: str) -> LoincEntry | None:
    """
    Attempt to map a lab parameter name to its LOINC entry.

    Lookup order:
      1. Exact canonical match
      2. Alias match
      3. Fuzzy match (difflib, ratio > 0.80)

    Returns None if no match found.
    """
    key = _clean(parameter_name)

    # 1. Canonical match
    if key in _CANONICAL_INDEX:
        return _CANONICAL_INDEX[key]

    # 2. Alias match
    if key in _ALIAS_INDEX:
        return _ALIAS_INDEX[key]

    # 3. Fuzzy match against all aliases
    all_keys = list(_ALIAS_INDEX.keys()) + list(_CANONICAL_INDEX.keys())
    matches = difflib.get_close_matches(key, all_keys, n=1, cutoff=0.80)
    if matches:
        m = matches[0]
        return _ALIAS_INDEX.get(m) or _CANONICAL_INDEX.get(m)

    return None


def normalize_lab_name(parameter_name: str) -> str:
    """
    Return the canonical LOINC display name for a parameter.
    Falls back to the original name if not found.
    """
    entry = map_parameter_to_loinc(parameter_name)
    return entry.canonical if entry else parameter_name


def get_loinc_code(parameter_name: str) -> str | None:
    """Return the LOINC code string, or None if not found."""
    entry = map_parameter_to_loinc(parameter_name)
    return entry.code if entry else None


def normalize_parameter_list(raw_names: list[str]) -> dict[str, str]:
    """
    Normalize a list of raw parameter names.
    Returns {raw_name: canonical_name}.
    """
    return {name: normalize_lab_name(name) for name in raw_names}
