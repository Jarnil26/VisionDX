"""
VisionDX — Report Highlight Engine

Generates human-readable clinical summaries of blood test results,
listing ALL detected conditions with confidence and clinical reasoning.
"""
from __future__ import annotations

from visiondx.core.abnormal_detector import HIGH, LOW, NORMAL
from visiondx.database.schemas import ParsedParameter, PredictionOut

# Disease → clinical reasoning hint
_CONDITION_HINTS: dict[str, str] = {
    "Anemia":                                    "low hemoglobin or red blood cell count",
    "Iron Deficiency":                           "low ferritin, serum iron, or microcytic RBCs",
    "Iron Deficiency Anemia":                    "low hemoglobin combined with depleted iron stores",
    "Diabetes":                                  "elevated blood glucose or HbA1c",
    "Diabetes / Pre-diabetes":                   "elevated blood glucose or HbA1c above normal range",
    "Infection":                                 "elevated white blood cell count or CRP",
    "Active Infection / Inflammation":           "elevated WBC, neutrophils, or CRP",
    "Liver Disease":                             "elevated ALT, AST, or bilirubin",
    "Liver Dysfunction":                         "elevated liver enzymes (ALT/AST)",
    "Fatty Liver":                               "elevated ALT/AST with high triglycerides",
    "Kidney Disorder":                           "elevated creatinine, BUN, or low eGFR",
    "Kidney Dysfunction":                        "elevated creatinine, BUN, or below-normal urea",
    "Thyroid Imbalance":                         "abnormal TSH or free thyroid hormone levels",
    "Hyperlipidemia":                            "elevated total cholesterol or LDL",
    "Hyperlipidemia / Dyslipidemia":             "elevated LDL, triglycerides, or total cholesterol",
    "Vitamin D Deficiency":                      "Vitamin D below 30 ng/mL",
    "Vitamin B12 Deficiency":                    "Vitamin B12 below 187 pg/mL",
    "Folate Deficiency":                         "folate below normal reference range",
    "Vitamin B6 Deficiency":                     "Vitamin B6 below normal",
    "Allergic Reaction / High IgE":             "total IgE significantly above 87 IU/mL",
    "Allergy / High IgE":                        "total IgE significantly above 87 IU/mL",
    "Cardiovascular Risk (Elevated Homocysteine)":"Homocysteine above 14.8 μmol/L — stroke and CVD risk",
    "Cardiovascular Risk":                       "elevated Homocysteine, LDL, or hs-CRP",
    "Metabolic Syndrome":                        "combination of high glucose, triglycerides, and low HDL",
    "Platelet Disorder":                         "abnormal platelet count or elevated MPV",
    "Hyponatremia (Low Sodium)":                 "sodium below 135 mEq/L",
    "Hypocalcemia (Low Calcium)":                "calcium below 8.5 mg/dL",
    "Normal":                                    "all parameters within normal range",
}


class HighlightEngine:
    """Generate human-readable multi-condition clinical report summaries."""

    def generate_summary(
        self,
        parameters: list[ParsedParameter],
        predictions: list[PredictionOut] | None = None,
    ) -> str:
        """Compose a plain-English clinical summary mentioning ALL detected conditions."""
        abnormal = [p for p in parameters if p.status != NORMAL]
        normal   = [p for p in parameters if p.status == NORMAL]

        lines: list[str] = []

        # ── Parameter counts ──────────────────────────────────────────────────
        if not abnormal:
            lines.append(f"All {len(normal)} tested parameters are within normal reference ranges.")
        else:
            high_params = [p for p in abnormal if p.status == HIGH]
            low_params  = [p for p in abnormal if p.status == LOW]
            lines.append(
                f"Out of {len(parameters)} tested parameters, "
                f"{len(abnormal)} value(s) are outside the normal range."
            )
            if high_params:
                names = ", ".join(p.name for p in high_params)
                lines.append(f"Elevated (HIGH): {names}.")
            if low_params:
                names = ", ".join(p.name for p in low_params)
                lines.append(f"Below normal (LOW): {names}.")

        # ── Disease predictions — ALL above 30% confidence ────────────────────
        if predictions:
            relevant = [
                p for p in predictions
                if p.disease.lower() not in ("normal",) and p.confidence >= 0.30
            ]
            # Sort by confidence, show ALL
            relevant.sort(key=lambda x: x.confidence, reverse=True)

            if relevant:
                mentions = []
                for pred in relevant:
                    hint = _CONDITION_HINTS.get(pred.disease, "")
                    pct  = int(pred.confidence * 100)
                    if hint:
                        mentions.append(f"{pred.disease} ({pct}% probability, indicated by {hint})")
                    else:
                        mentions.append(f"{pred.disease} ({pct}% probability)")

                if len(relevant) == 1:
                    lines.append(f"Based on the AI analysis, results may suggest: {mentions[0]}.")
                else:
                    formatted = "; ".join(mentions[:-1]) + f"; and {mentions[-1]}"
                    lines.append(
                        f"Based on the combined AI and clinical rule analysis, "
                        f"results may suggest: {formatted}."
                    )

                lines.append(
                    "Medical consultation with a qualified physician is strongly "
                    "recommended before making any clinical decisions."
                )

        return " ".join(lines)

    def format_abnormal_list(self, parameters: list[ParsedParameter]) -> list[dict]:
        """Return structured list of abnormal parameters with display metadata."""
        from visiondx.core.abnormal_detector import STATUS_COLORS
        result = []
        for p in parameters:
            if p.status == NORMAL:
                continue
            result.append({
                "name": p.name,
                "value": p.value,
                "unit": p.unit or "",
                "reference_range": p.reference_range or "N/A",
                "status": p.status,
                "color": STATUS_COLORS.get(p.status, "#ffffff"),
                "message": (
                    f"{p.name} is {'above' if p.status == HIGH else 'below'} "
                    f"normal range ({p.reference_range})"
                ),
            })
        return result
