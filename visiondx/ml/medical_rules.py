"""
VisionDX — Medical Reasoning Engine

A clinical rule-based engine that analyzes ALL extracted blood parameters
and returns disease predictions with confidence and reasoning.

This runs ALONGSIDE the ML model and catches conditions that the ML model
cannot detect (e.g. Vitamin D deficiency, B12 deficiency, high IgE allergy,
Homocysteine-based cardiovascular risk, etc.).

Architecture:
    parameters (ALL) → rule evaluation → merge with ML predictions
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RuleResult:
    disease: str
    confidence: float       # 0.0 – 1.0
    reason: str             # human-readable explanation
    markers: list[str] = field(default_factory=list)  # which params fired
    source: str = "rules"   # "rules" | "ml" | "merged"


# ─────────────────────────────────────────────────────────────────────────────
# LOINC-aligned parameter name aliases
# (maps variants from lab reports → canonical name used in rules)
# ─────────────────────────────────────────────────────────────────────────────

ALIASES: dict[str, str] = {
    # Glucose / Diabetes
    "glucose":                     "Glucose",
    "fbs":                         "Glucose",
    "fasting blood sugar":         "Glucose",
    "fasting glucose":             "Glucose",
    "blood glucose":               "Glucose",
    "rbs":                         "Glucose",
    "random blood sugar":          "Glucose",
    "hba1c":                       "HbA1c",
    "hb a1c":                      "HbA1c",
    "hemoglobin a1c":              "HbA1c",
    "glycated hemoglobin":         "HbA1c",
    "hb a":                        "HbA1c",          # "Hb A L" in report
    "hb a l":                      "HbA1c",

    # Hemoglobin / Anemia
    "hemoglobin":                  "Hemoglobin",
    "haemoglobin":                 "Hemoglobin",
    "hgb":                         "Hemoglobin",
    "hb":                          "Hemoglobin",
    "rbc":                         "RBC",
    "red blood cells":             "RBC",
    "red blood cell count":        "RBC",
    "hematocrit":                  "Hematocrit",
    "hct":                         "Hematocrit",
    "pcv":                         "Hematocrit",
    "mcv":                         "MCV",
    "mch":                         "MCH",
    "mchc":                        "MCHC",
    "rdw":                         "RDW",

    # Iron
    "serum iron":                  "Serum Iron",
    "iron":                        "Serum Iron",
    "ferritin":                    "Ferritin",
    "serum ferritin":              "Ferritin",
    "tibc":                        "TIBC",
    "total iron binding capacity": "TIBC",
    "transferrin saturation":      "Transferrin Saturation",

    # WBC / Infection
    "wbc":                         "WBC",
    "white blood cells":           "WBC",
    "total wbc":                   "WBC",
    "leukocytes":                  "WBC",
    "neutrophils":                 "Neutrophils",
    "lymphocytes":                 "Lymphocytes",
    "monocytes":                   "Monocytes",
    "eosinophils":                 "Eosinophils",
    "crp":                         "CRP",
    "c-reactive protein":          "CRP",
    "c reactive protein":          "CRP",
    "esr":                         "ESR",

    # Platelets
    "platelets":                   "Platelets",
    "platelet count":              "Platelets",
    "plt":                         "Platelets",
    "mpv":                         "MPV",
    "mpv h":                       "MPV",
    "mean platelet volume":        "MPV",

    # Kidney
    "creatinine":                  "Creatinine",
    "serum creatinine":            "Creatinine",
    "urea":                        "Urea",
    "serum urea":                  "Urea",
    "urea l":                      "Urea",
    "blood urea nitrogen":         "BUN",
    "bun":                         "BUN",
    "egfr":                        "eGFR",
    "estimated gfr":               "eGFR",
    "uric acid":                   "Uric Acid",

    # Liver
    "alt":                         "ALT",
    "sgpt":                        "ALT",
    "alanine aminotransferase":    "ALT",
    "ast":                         "AST",
    "sgot":                        "AST",
    "aspartate aminotransferase":  "AST",
    "bilirubin":                   "Bilirubin Total",
    "total bilirubin":             "Bilirubin Total",
    "bilirubin total":             "Bilirubin Total",
    "direct bilirubin":            "Bilirubin Direct",
    "alp":                         "ALP",
    "alkaline phosphatase":        "ALP",
    "ggt":                         "GGT",
    "gamma gt":                    "GGT",
    "albumin":                     "Albumin",
    "protein":                     "Total Protein",
    "total protein":               "Total Protein",

    # Lipids
    "cholesterol":                 "Total Cholesterol",
    "total cholesterol":           "Total Cholesterol",
    "ldl":                         "LDL Cholesterol",
    "ldl cholesterol":             "LDL Cholesterol",
    "ldl-c":                       "LDL Cholesterol",
    "hdl":                         "HDL Cholesterol",
    "hdl cholesterol":             "HDL Cholesterol",
    "hdl-c":                       "HDL Cholesterol",
    "triglycerides":               "Triglycerides",
    "tg":                          "Triglycerides",
    "vldl":                        "VLDL",
    "non-hdl cholesterol":         "Non-HDL Cholesterol",

    # Thyroid
    "tsh":                         "TSH",
    "thyroid stimulating hormone": "TSH",
    "t3":                          "T3",
    "triiodothyronine":            "T3",
    "t4":                          "T4",
    "thyroxine":                   "T4",
    "free t3":                     "Free T3",
    "ft3":                         "Free T3",
    "free t4":                     "Free T4",
    "ft4":                         "Free T4",

    # Vitamins
    "vitamin d":                   "Vitamin D",
    "vitamin d3":                  "Vitamin D",
    "25-oh vitamin d":             "Vitamin D",
    "25 oh vitamin d":             "Vitamin D",
    "25-hydroxyvitamin d":         "Vitamin D",
    "vitd":                        "Vitamin D",
    "vitamin b12":                 "Vitamin B12",
    "b12":                         "Vitamin B12",
    "cyanocobalamin":              "Vitamin B12",
    "cobalamin":                   "Vitamin B12",
    "folate":                      "Folate",
    "folic acid":                  "Folate",
    "vitamin b9":                  "Folate",
    "serum folate":                "Folate",
    "vitamin b6":                  "Vitamin B6",
    "pyridoxine":                  "Vitamin B6",

    # Cardiovascular / Inflammation
    "homocysteine":                "Homocysteine",
    "homocysteine serum":         "Homocysteine",
    "homocysteine, serum":        "Homocysteine",
    "homocysteine, serum h":      "Homocysteine",
    "hs-crp":                      "hs-CRP",
    "high sensitivity crp":        "hs-CRP",
    "hsCRP":                       "hs-CRP",

    # Allergy / Immune
    "ige":                         "IgE",
    "ige h":                       "IgE",
    "total ige":                   "IgE",
    "immunoglobulin e":            "IgE",
    "serum ige":                   "IgE",
    "serum h":                     "Homocysteine",  # common lab label variant

    # Hormones
    "insulin":                     "Insulin",
    "fasting insulin":             "Insulin",
    "cortisol":                    "Cortisol",
    "testosterone":                "Testosterone",
    "estradiol":                   "Estradiol",
    "prolactin":                   "Prolactin",
    "lh":                          "LH",
    "fsh":                         "FSH",

    # Electrolytes
    "sodium":                      "Sodium",
    "potassium":                   "Potassium",
    "chloride":                    "Chloride",
    "calcium":                     "Calcium",
    "magnesium":                   "Magnesium",
    "phosphorus":                  "Phosphorus",
    "bicarbonate":                 "Bicarbonate",
}


def _normalize(name: str) -> str:
    """Lower-case, strip trailing H/L markers and extra spaces."""
    n = name.lower().strip()
    # remove trailing flag markers like " H", " L", " h", " l"
    n = re.sub(r"\s+[hl]$", "", n).strip()
    return n


def _lookup(name: str, param_map: dict[str, float]) -> float | None:
    """Look up a canonical parameter value using aliases."""
    canon = ALIASES.get(_normalize(name))
    if canon:
        return param_map.get(canon)
    return param_map.get(name)


def _severity(deviation_pct: float) -> float:
    """
    Convert % deviation from normal boundary to a confidence modifier.
    0–10% deviation → 0.55–0.70
    10–25%          → 0.70–0.85
    >25%            → 0.85–0.97
    """
    if deviation_pct < 10:
        return 0.55 + deviation_pct * 0.015
    elif deviation_pct < 25:
        return 0.70 + (deviation_pct - 10) * 0.01
    else:
        return min(0.97, 0.85 + (deviation_pct - 25) * 0.004)


def _pct_above(value: float, limit: float) -> float:
    return abs(value - limit) / limit * 100 if limit else 0


def _pct_below(value: float, limit: float) -> float:
    return abs(limit - value) / limit * 100 if limit else 0


# ─────────────────────────────────────────────────────────────────────────────
# Medical Rules
# ─────────────────────────────────────────────────────────────────────────────

class MedicalRulesEngine:
    """
    Evaluates clinical rules for 20+ conditions directly from
    extracted lab parameters (no ML model needed).
    """

    RULES = [
        "_check_diabetes",
        "_check_anemia",
        "_check_iron_deficiency",
        "_check_vitamin_d",
        "_check_vitamin_b12",
        "_check_folate",
        "_check_thyroid",
        "_check_kidney_disease",
        "_check_liver_disease",
        "_check_hyperlipidemia",
        "_check_cardiovascular_risk",
        "_check_allergy_high_ige",
        "_check_infection",
        "_check_platelet_disorder",
        "_check_metabolic_syndrome",
        "_check_vitamin_b6",
        "_check_hyponatremia",
        "_check_hypocalcemia",
    ]

    def apply(
        self,
        parameters: list[Any],
        threshold: float = 0.40,
    ) -> list[RuleResult]:
        """
        Run all rules and return conditions with confidence ≥ threshold.

        Args:
            parameters: list of ParsedParameter objects with .name and .value
            threshold: minimum confidence to include in results
        """
        # Build canonical lookup map
        param_map: dict[str, float] = {}
        for p in parameters:
            if p.value is not None:
                canonical = ALIASES.get(_normalize(p.name), p.name)
                param_map[canonical] = float(p.value)
                # also store by original name
                param_map[p.name] = float(p.value)

        results: list[RuleResult] = []
        for rule_name in self.RULES:
            try:
                rule_fn = getattr(self, rule_name)
                result = rule_fn(param_map)
                if result and result.confidence >= threshold:
                    results.append(result)
                    logger.debug(
                        f"[RULES] {result.disease}: {result.confidence:.0%} — {result.reason}"
                    )
            except Exception as e:
                logger.warning(f"Rule {rule_name} failed: {e}")

        results.sort(key=lambda r: r.confidence, reverse=True)
        logger.info(f"Medical rules engine: {len(results)} conditions detected (threshold={threshold:.0%})")
        return results

    # ── Diabetes ─────────────────────────────────────────────────────────────
    def _check_diabetes(self, pm: dict) -> RuleResult | None:
        glucose = pm.get("Glucose")
        hba1c   = pm.get("HbA1c")
        markers, conf, reasons = [], 0.0, []

        if glucose is not None:
            if glucose >= 200:
                conf = max(conf, _severity(_pct_above(glucose, 106)))
                markers.append(f"Glucose {glucose} mg/dL (≥200, diabetic range)")
                reasons.append("Glucose ≥200 mg/dL")
            elif glucose >= 126:
                conf = max(conf, _severity(_pct_above(glucose, 106)) * 0.9)
                markers.append(f"Glucose {glucose} mg/dL (fasting ≥126)")
                reasons.append("Fasting glucose ≥126 mg/dL")
            elif glucose > 106:
                conf = max(conf, 0.50)
                markers.append(f"Glucose {glucose} mg/dL (slightly elevated)")
                reasons.append("Glucose above normal")

        if hba1c is not None:
            # HbA1c % — normal 96.8-97.8 in some formats or 4.0-5.6 standard
            # Handle both: if >6.5% → diabetic
            if hba1c >= 6.5:
                conf = max(conf, 0.92)
                markers.append(f"HbA1c {hba1c}% (≥6.5 diabetic)")
                reasons.append("HbA1c ≥6.5%")
            elif hba1c >= 5.7:
                conf = max(conf, 0.65)
                markers.append(f"HbA1c {hba1c}% (pre-diabetic 5.7-6.4%)")
                reasons.append("HbA1c pre-diabetic range")
            # LOW HbA1c in 96.8-97.8 format means LOW % => possible issue
            elif hba1c < 88 and hba1c > 20:  # someone reported in % of total Hb
                conf = max(conf, 0.75)
                markers.append(f"HbA1c {hba1c}% [below normal ref 96.8-97.8, LOW]")
                reasons.append("HbA1c below normal range — possible glycation issue")

        if not markers:
            return None
        return RuleResult(
            disease="Diabetes / Pre-diabetes",
            confidence=min(conf, 0.97),
            reason="; ".join(reasons),
            markers=markers,
        )

    # ── Anemia ───────────────────────────────────────────────────────────────
    def _check_anemia(self, pm: dict) -> RuleResult | None:
        hb  = pm.get("Hemoglobin")
        rbc = pm.get("RBC")
        hct = pm.get("Hematocrit")
        markers, conf, reasons = [], 0.0, []

        if hb is not None:
            if hb < 7:
                conf = max(conf, 0.95); markers.append(f"Hb {hb} (severe anemia <7)"); reasons.append("Severely low Hemoglobin")
            elif hb < 10:
                conf = max(conf, 0.88); markers.append(f"Hb {hb} (anemia <10)"); reasons.append("Low Hemoglobin (<10)")
            elif hb < 12:
                conf = max(conf, 0.72); markers.append(f"Hb {hb}"); reasons.append("Low Hemoglobin (<12)")
            elif hb < 13:
                conf = max(conf, 0.55); markers.append(f"Hb {hb} (borderline)"); reasons.append("Borderline low Hemoglobin")

        if rbc is not None and rbc < 4.0:
            conf = max(conf, 0.60); markers.append(f"RBC {rbc}"); reasons.append("Low RBC count")

        if hct is not None and hct < 37:
            conf = max(conf, 0.65); markers.append(f"Hct {hct}%"); reasons.append("Low Hematocrit")

        if not markers:
            return None
        return RuleResult(disease="Anemia", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Iron Deficiency ───────────────────────────────────────────────────────
    def _check_iron_deficiency(self, pm: dict) -> RuleResult | None:
        hb      = pm.get("Hemoglobin")
        iron    = pm.get("Serum Iron")
        ferr    = pm.get("Ferritin")
        tibc    = pm.get("TIBC")
        mcv     = pm.get("MCV")
        markers, conf, reasons = [], 0.0, []

        if ferr is not None and ferr < 12:
            conf = max(conf, 0.88)
            markers.append(f"Ferritin {ferr} ng/mL (critically low <12)")
            reasons.append("Low Ferritin — iron stores depleted")
        elif ferr is not None and ferr < 30:
            conf = max(conf, 0.70)
            markers.append(f"Ferritin {ferr} ng/mL (low)")
            reasons.append("Low Ferritin")

        if iron is not None and iron < 60:
            conf = max(conf, 0.65)
            markers.append(f"Serum Iron {iron} μg/dL (low)")
            reasons.append("Low Serum Iron")

        if tibc is not None and tibc > 400:
            conf = max(conf, 0.65)
            markers.append(f"TIBC {tibc} (elevated — iron deficiency pattern)")
            reasons.append("Elevated TIBC")

        if mcv is not None and mcv < 80:
            conf = max(conf, 0.60)
            markers.append(f"MCV {mcv} fL (microcytic <80)")
            reasons.append("Microcytic red cells")

        if hb is not None and hb < 12 and not ferr and not iron:
            conf = max(conf, 0.45)
            markers.append(f"Hb {hb} — possible iron deficiency")

        if not markers:
            return None
        return RuleResult(disease="Iron Deficiency Anemia", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Vitamin D ─────────────────────────────────────────────────────────────
    def _check_vitamin_d(self, pm: dict) -> RuleResult | None:
        vd = pm.get("Vitamin D")
        if vd is None:
            return None
        if vd < 10:
            conf, reason = 0.94, f"Vitamin D {vd} ng/mL — severely deficient (<10)"
        elif vd < 20:
            conf, reason = 0.88, f"Vitamin D {vd} ng/mL — deficient (<20)"
        elif vd < 30:
            conf, reason = 0.65, f"Vitamin D {vd} ng/mL — insufficient (20-30)"
        else:
            return None
        return RuleResult(
            disease="Vitamin D Deficiency",
            confidence=conf,
            reason=reason,
            markers=[f"Vitamin D {vd} ng/mL"],
        )

    # ── Vitamin B12 ───────────────────────────────────────────────────────────
    def _check_vitamin_b12(self, pm: dict) -> RuleResult | None:
        b12 = pm.get("Vitamin B12")
        if b12 is None:
            return None
        if b12 < 100:
            conf, reason = 0.93, f"Vitamin B12 {b12} pg/mL — severely deficient (<100)"
        elif b12 < 187:
            conf, reason = 0.87, f"Vitamin B12 {b12} pg/mL — deficient (<187)"
        elif b12 < 250:
            conf, reason = 0.60, f"Vitamin B12 {b12} pg/mL — borderline low (187-250)"
        else:
            return None
        return RuleResult(
            disease="Vitamin B12 Deficiency",
            confidence=conf,
            reason=reason,
            markers=[f"B12 {b12} pg/mL"],
        )

    # ── Folate ────────────────────────────────────────────────────────────────
    def _check_folate(self, pm: dict) -> RuleResult | None:
        fol = pm.get("Folate")
        if fol is None:
            return None
        if fol < 3:
            conf, reason = 0.90, f"Folate {fol} ng/mL — deficient (<3)"
        elif fol < 5.4:
            conf, reason = 0.70, f"Folate {fol} ng/mL — low"
        else:
            return None
        return RuleResult(disease="Folate Deficiency", confidence=conf, reason=reason, markers=[f"Folate {fol}"])

    # ── Thyroid ───────────────────────────────────────────────────────────────
    def _check_thyroid(self, pm: dict) -> RuleResult | None:
        tsh = pm.get("TSH")
        ft3 = pm.get("Free T3")
        ft4 = pm.get("Free T4")
        markers, conf, reasons = [], 0.0, []

        if tsh is not None:
            if tsh > 10:
                conf = max(conf, _severity(_pct_above(tsh, 4.5)))
                markers.append(f"TSH {tsh} mIU/L (HIGH — hypothyroid)")
                reasons.append("Elevated TSH — hypothyroidism")
            elif tsh > 4.5:
                conf = max(conf, 0.65)
                markers.append(f"TSH {tsh} mIU/L (borderline high)")
                reasons.append("TSH above normal")
            elif tsh < 0.4:
                conf = max(conf, _severity(_pct_below(tsh, 0.4)))
                markers.append(f"TSH {tsh} mIU/L (LOW — hyperthyroid)")
                reasons.append("Suppressed TSH — hyperthyroidism")

        if ft4 is not None:
            if ft4 < 0.8:
                conf = max(conf, 0.70)
                markers.append(f"Free T4 {ft4} ng/dL (LOW)")
                reasons.append("Low Free T4")
            elif ft4 > 1.8:
                conf = max(conf, 0.70)
                markers.append(f"Free T4 {ft4} ng/dL (HIGH)")
                reasons.append("High Free T4")

        if not markers:
            return None
        return RuleResult(disease="Thyroid Imbalance", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Kidney Disease ────────────────────────────────────────────────────────
    def _check_kidney_disease(self, pm: dict) -> RuleResult | None:
        creat  = pm.get("Creatinine")
        urea   = pm.get("Urea")
        bun    = pm.get("BUN")
        egfr   = pm.get("eGFR")
        uric   = pm.get("Uric Acid")
        markers, conf, reasons = [], 0.0, []

        if creat is not None and creat > 1.2:
            conf = max(conf, _severity(_pct_above(creat, 1.2)))
            markers.append(f"Creatinine {creat} mg/dL (HIGH)")
            reasons.append("Elevated Creatinine")

        if bun is not None and bun < 9:
            conf = max(conf, 0.58)
            markers.append(f"BUN {bun} mg/dL (LOW <9)")
            reasons.append("Low BUN")
        elif bun is not None and bun > 20:
            conf = max(conf, _severity(_pct_above(bun, 20)))
            markers.append(f"BUN {bun} mg/dL (HIGH)")
            reasons.append("Elevated BUN")

        if urea is not None and urea < 19.3:
            conf = max(conf, 0.52)
            markers.append(f"Urea {urea} mg/dL (LOW <19.3)")
            reasons.append("Low Urea — reduced protein metabolism or dilution")

        if egfr is not None and egfr < 60:
            conf = max(conf, 0.85)
            markers.append(f"eGFR {egfr} mL/min (impaired <60)")
            reasons.append("Low eGFR — kidney function impaired")

        if uric is not None and uric > 7:
            conf = max(conf, 0.55)
            markers.append(f"Uric Acid {uric} mg/dL (HIGH)")
            reasons.append("Elevated Uric Acid — gout / kidney risk")

        if not markers:
            return None
        return RuleResult(disease="Kidney Dysfunction", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Liver Disease ─────────────────────────────────────────────────────────
    def _check_liver_disease(self, pm: dict) -> RuleResult | None:
        alt   = pm.get("ALT")
        ast   = pm.get("AST")
        bili  = pm.get("Bilirubin Total")
        alp   = pm.get("ALP")
        ggt   = pm.get("GGT")
        alb   = pm.get("Albumin")
        markers, conf, reasons = [], 0.0, []

        if alt is not None and alt > 40:
            conf = max(conf, _severity(_pct_above(alt, 40)))
            markers.append(f"ALT {alt} U/L (HIGH)")
            reasons.append("Elevated ALT — liver stress")

        if ast is not None and ast > 40:
            conf = max(conf, _severity(_pct_above(ast, 40)) * 0.9)
            markers.append(f"AST {ast} U/L (HIGH)")
            reasons.append("Elevated AST")

        if bili is not None and bili > 1.2:
            conf = max(conf, 0.65)
            markers.append(f"Bilirubin {bili} mg/dL (HIGH)")
            reasons.append("Elevated Bilirubin")

        if alp is not None and alp > 130:
            conf = max(conf, 0.60)
            markers.append(f"ALP {alp} U/L (HIGH)")
            reasons.append("Elevated ALP")

        if alb is not None and alb < 3.5:
            conf = max(conf, 0.65)
            markers.append(f"Albumin {alb} g/dL (LOW)")
            reasons.append("Low Albumin — liver synthetic function impaired")

        if not markers:
            return None
        return RuleResult(disease="Liver Dysfunction", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Hyperlipidemia ────────────────────────────────────────────────────────
    def _check_hyperlipidemia(self, pm: dict) -> RuleResult | None:
        tc   = pm.get("Total Cholesterol")
        ldl  = pm.get("LDL Cholesterol")
        hdl  = pm.get("HDL Cholesterol")
        tg   = pm.get("Triglycerides")
        markers, conf, reasons = [], 0.0, []

        if tc is not None and tc > 200:
            conf = max(conf, _severity(_pct_above(tc, 200)) * 0.9)
            markers.append(f"Total Cholesterol {tc} mg/dL (HIGH >200)")
            reasons.append("High Total Cholesterol")

        if ldl is not None and ldl > 130:
            conf = max(conf, _severity(_pct_above(ldl, 130)))
            markers.append(f"LDL {ldl} mg/dL (HIGH >130)")
            reasons.append("High LDL — atherogenic risk")

        if hdl is not None and hdl < 40:
            conf = max(conf, 0.65)
            markers.append(f"HDL {hdl} mg/dL (LOW <40 — protective HDL reduced)")
            reasons.append("Low HDL")

        if tg is not None and tg > 150:
            conf = max(conf, _severity(_pct_above(tg, 150)) * 0.85)
            markers.append(f"Triglycerides {tg} mg/dL (HIGH >150)")
            reasons.append("High Triglycerides")

        if not markers:
            return None
        return RuleResult(disease="Hyperlipidemia / Dyslipidemia", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Cardiovascular Risk (Homocysteine) ────────────────────────────────────
    def _check_cardiovascular_risk(self, pm: dict) -> RuleResult | None:
        hcy  = pm.get("Homocysteine")
        ldl  = pm.get("LDL Cholesterol")
        hscrp = pm.get("hs-CRP") or pm.get("CRP")
        markers, conf, reasons = [], 0.0, []

        if hcy is not None:
            if hcy > 30:
                conf = max(conf, 0.91)
                markers.append(f"Homocysteine {hcy} μmol/L (severely HIGH >30)")
                reasons.append("Severe hyperhomocysteinemia — high CVD risk")
            elif hcy > 14.8:
                conf = max(conf, _severity(_pct_above(hcy, 14.8)))
                markers.append(f"Homocysteine {hcy} μmol/L (HIGH, ref 6-14.8)")
                reasons.append("Elevated Homocysteine — cardiovascular & stroke risk")

        if ldl is not None and ldl > 160:
            conf = max(conf, 0.70)
            markers.append(f"LDL {ldl} mg/dL (HIGH)")

        if hscrp is not None and hscrp > 3:
            conf = max(conf, 0.68)
            markers.append(f"hs-CRP {hscrp} mg/L (elevated inflammation marker)")
            reasons.append("Elevated CRP — systemic inflammation / CVD risk")

        if not markers:
            return None
        return RuleResult(disease="Cardiovascular Risk (Elevated Homocysteine)", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Allergy / High IgE ────────────────────────────────────────────────────
    def _check_allergy_high_ige(self, pm: dict) -> RuleResult | None:
        ige  = pm.get("IgE")
        eos  = pm.get("Eosinophils")
        markers, conf, reasons = [], 0.0, []

        if ige is not None:
            if ige > 1000:
                conf = max(conf, 0.93)
                markers.append(f"IgE {ige} IU/mL (severely elevated >1000)")
                reasons.append("Very high IgE — severe allergy / parasitic infection")
            elif ige > 200:
                conf = max(conf, _severity(_pct_above(ige, 87)))
                markers.append(f"IgE {ige} IU/mL (HIGH >200, ref 0-87)")
                reasons.append("High IgE — allergic sensitization")
            elif ige > 87:
                conf = max(conf, 0.72)
                markers.append(f"IgE {ige} IU/mL (above normal >87)")
                reasons.append("Elevated IgE — possible allergy")

        if eos is not None and eos > 6:
            conf = max(conf, 0.65)
            markers.append(f"Eosinophils {eos}% (elevated)")
            reasons.append("Elevated Eosinophils — allergy / parasitic response")

        if not markers:
            return None
        return RuleResult(disease="Allergic Reaction / High IgE", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Infection / Sepsis ────────────────────────────────────────────────────
    def _check_infection(self, pm: dict) -> RuleResult | None:
        wbc   = pm.get("WBC")
        neut  = pm.get("Neutrophils")
        crp   = pm.get("CRP") or pm.get("hs-CRP")
        esr   = pm.get("ESR")
        markers, conf, reasons = [], 0.0, []

        if wbc is not None:
            if wbc > 20:
                conf = max(conf, 0.88)
                markers.append(f"WBC {wbc} ×10³/μL (severely HIGH >20)")
                reasons.append("Severely elevated WBC — acute infection / sepsis")
            elif wbc > 11:
                conf = max(conf, _severity(_pct_above(wbc, 11)))
                markers.append(f"WBC {wbc} ×10³/μL (HIGH)")
                reasons.append("Elevated WBC — infection / inflammation")
            elif wbc < 4:
                conf = max(conf, 0.60)
                markers.append(f"WBC {wbc} ×10³/μL (LOW — leukopenia)")
                reasons.append("Low WBC — viral infection / immunosuppression")

        if neut is not None and neut > 75:
            conf = max(conf, 0.65)
            markers.append(f"Neutrophils {neut}% (HIGH)")
            reasons.append("Neutrophilia — bacterial infection")

        if crp is not None and crp > 5:
            conf = max(conf, 0.70)
            markers.append(f"CRP {crp} mg/L (elevated inflammation)")
            reasons.append("Elevated CRP")

        if esr is not None and esr > 20:
            conf = max(conf, 0.55)
            markers.append(f"ESR {esr} mm/hr (elevated)")
            reasons.append("Elevated ESR")

        if not markers:
            return None
        return RuleResult(disease="Active Infection / Inflammation", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Platelet Disorder ─────────────────────────────────────────────────────
    def _check_platelet_disorder(self, pm: dict) -> RuleResult | None:
        plt = pm.get("Platelets")
        mpv = pm.get("MPV")
        markers, conf, reasons = [], 0.0, []

        if plt is not None:
            if plt < 50:
                conf = max(conf, 0.90)
                markers.append(f"Platelets {plt} ×10³/μL (severe thrombocytopenia <50)")
                reasons.append("Severe thrombocytopenia")
            elif plt < 150:
                conf = max(conf, 0.72)
                markers.append(f"Platelets {plt} (low <150)")
                reasons.append("Low platelets — bleeding risk")
            elif plt > 450:
                conf = max(conf, 0.65)
                markers.append(f"Platelets {plt} (HIGH >450 — thrombocytosis)")
                reasons.append("High platelets — thrombocytosis")

        if mpv is not None and mpv > 10.3:
            conf = max(conf, 0.55)
            markers.append(f"MPV {mpv} fL (HIGH >10.3) — large platelets")
            reasons.append("Elevated MPV — platelet activation / cardiovascular risk")

        if not markers:
            return None
        return RuleResult(disease="Platelet Disorder", confidence=min(conf, 0.97), reason="; ".join(reasons), markers=markers)

    # ── Metabolic Syndrome ────────────────────────────────────────────────────
    def _check_metabolic_syndrome(self, pm: dict) -> RuleResult | None:
        glucose = pm.get("Glucose")
        tg      = pm.get("Triglycerides")
        hdl     = pm.get("HDL Cholesterol")
        tc      = pm.get("Total Cholesterol")
        markers, conf, reasons = [], 0.0, []
        score = 0

        if glucose is not None and glucose > 100:
            score += 1; markers.append(f"Glucose {glucose}"); reasons.append("Impaired fasting glucose")
        if tg is not None and tg > 150:
            score += 1; markers.append(f"TG {tg}"); reasons.append("High Triglycerides")
        if hdl is not None and hdl < 40:
            score += 1; markers.append(f"HDL {hdl}"); reasons.append("Low HDL")
        if tc is not None and tc > 200:
            score += 1; markers.append(f"TC {tc}"); reasons.append("High Cholesterol")

        if score < 2:
            return None
        conf = 0.50 + score * 0.12
        return RuleResult(disease="Metabolic Syndrome", confidence=min(conf, 0.87), reason="; ".join(reasons), markers=markers)

    # ── Vitamin B6 ────────────────────────────────────────────────────────────
    def _check_vitamin_b6(self, pm: dict) -> RuleResult | None:
        b6 = pm.get("Vitamin B6")
        if b6 is None:
            return None
        if b6 < 5:
            return RuleResult(disease="Vitamin B6 Deficiency", confidence=0.82, reason=f"Vitamin B6 {b6} nmol/L (deficient <5)", markers=[f"B6 {b6}"])
        return None

    # ── Hyponatremia ──────────────────────────────────────────────────────────
    def _check_hyponatremia(self, pm: dict) -> RuleResult | None:
        na = pm.get("Sodium")
        if na is not None and na < 135:
            conf = 0.80 if na < 125 else 0.65
            return RuleResult(disease="Hyponatremia (Low Sodium)", confidence=conf, reason=f"Sodium {na} mEq/L (low <135)", markers=[f"Na {na}"])
        return None

    # ── Hypocalcemia ──────────────────────────────────────────────────────────
    def _check_hypocalcemia(self, pm: dict) -> RuleResult | None:
        ca = pm.get("Calcium")
        if ca is not None and ca < 8.5:
            conf = 0.82 if ca < 7.5 else 0.60
            return RuleResult(disease="Hypocalcemia (Low Calcium)", confidence=conf, reason=f"Calcium {ca} mg/dL (low <8.5)", markers=[f"Ca {ca}"])
        return None


# Singleton
_engine = MedicalRulesEngine()


def apply_medical_rules(parameters: list, threshold: float = 0.40) -> list[RuleResult]:
    """Convenience function — run all medical rules on parameter list."""
    return _engine.apply(parameters, threshold)
