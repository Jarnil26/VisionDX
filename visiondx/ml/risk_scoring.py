"""
VisionDX — Risk Scoring Engine

Converts biomarker evidence into probability scores for each disease.

Algorithm:
  For each disease in the knowledge base:
    1. Check which biomarkers are present AND abnormal in the patient data
    2. Calculate deviation severity for each abnormal marker
    3. Apply weighted sum of evidence
    4. Normalize to probability [0, 1]
    5. Apply critical escalation if any marker is in critical range
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BiomarkerEvidence:
    name: str
    canonical: str
    value: float
    direction: str          # "HIGH" | "LOW"
    threshold: float
    critical: float | None
    weight: float
    deviation_pct: float    # % deviation beyond threshold
    is_critical: bool
    contribution: float     # 0–1 weighted contribution


@dataclass
class DiseaseScore:
    disease: str
    confidence: float          # 0.0 – 1.0
    evidence: list[BiomarkerEvidence] = field(default_factory=list)
    icd10: str = ""
    category: str = ""
    reason: str = ""
    is_critical: bool = False


def _deviation(value: float, threshold: float, direction: str) -> float:
    """Return % deviation beyond the threshold boundary."""
    if direction == "HIGH":
        if value <= threshold:
            return 0.0
        return (value - threshold) / threshold * 100
    else:  # LOW
        if value >= threshold:
            return 0.0
        return (threshold - value) / threshold * 100


def _severity_curve(deviation_pct: float) -> float:
    """
    Map % deviation from threshold to a base score [0, 1].
    Uses a smooth S-curve:
      0%   → 0.50  (just exceeded threshold)
      10%  → 0.68
      25%  → 0.82
      50%  → 0.92
      100% → 0.97
    """
    import math
    if deviation_pct <= 0:
        return 0.0
    # Logistic function tuned for medical severity
    k = 0.05  # growth rate
    x0 = 20   # midpoint at 20% deviation
    score = 1 / (1 + math.exp(-k * (deviation_pct - x0)))
    # Scale so minimum at 0 deviation = 0.50
    score = 0.50 + score * 0.47
    return round(min(score, 0.97), 4)


def score_disease(
    disease_name: str,
    disease_def: dict,
    normalized_params: dict[str, float],  # {canonical_name: value}
    param_statuses: dict[str, str],       # {canonical_name: "HIGH"|"LOW"|"NORMAL"}
) -> DiseaseScore | None:
    """
    Evaluate a single disease against the patient's lab results.

    Returns a DiseaseScore, or None if the minimum evidence threshold is not met.

    Args:
        disease_name:     Name of the disease from the knowledge base.
        disease_def:      The disease definition dict from disease_knowledge.json.
        normalized_params: {canonical_name: float value} for all extracted params.
        param_statuses:   {canonical_name: HIGH/LOW/NORMAL} from abnormal detector.
    """
    biomarkers_def = disease_def.get("biomarkers", [])
    min_markers    = disease_def.get("min_markers", 1)
    logic          = disease_def.get("logic", "ANY")  # ANY | ALL

    evidence: list[BiomarkerEvidence] = []
    total_weight = 0.0

    for bm in biomarkers_def:
        name      = bm["name"]
        direction = bm["direction"]     # "HIGH" | "LOW"
        threshold = bm["threshold"]
        critical  = bm.get("critical")
        weight    = bm["weight"]

        value = normalized_params.get(name)
        if value is None:
            continue  # parameter not in patient report — skip

        # Check if abnormal in the expected direction
        status = param_statuses.get(name, "NORMAL")
        if status != direction:
            continue  # parameter present but not abnormal in right direction

        dev = _deviation(value, threshold, direction)
        if dev <= 0:
            continue  # numerical check confirms not beyond threshold

        is_crit = (critical is not None and (
            (direction == "HIGH" and value >= critical) or
            (direction == "LOW"  and value <= critical)
        ))

        base_score = _severity_curve(dev)
        contribution = base_score * weight

        evidence.append(BiomarkerEvidence(
            name=name,
            canonical=name,
            value=value,
            direction=direction,
            threshold=threshold,
            critical=critical,
            weight=weight,
            deviation_pct=round(dev, 1),
            is_critical=is_crit,
            contribution=round(contribution, 4),
        ))
        total_weight += weight

    # Check minimum evidence requirement
    required = min_markers
    if logic == "ALL":
        required = len(biomarkers_def)

    if len(evidence) < required:
        return None  # Not enough supporting biomarkers

    if not evidence:
        return None

    # ── Compute confidence ────────────────────────────────────────────────────
    # Weighted average of contributions, normalized to total possible weight
    max_possible = sum(bm["weight"] for bm in biomarkers_def)
    raw_score = sum(e.contribution for e in evidence) / max(max_possible, 0.01)

    # Bonus for multiple supporting markers
    multi_marker_bonus = min(0.06 * (len(evidence) - 1), 0.18)
    confidence = min(raw_score + multi_marker_bonus, 0.98)

    # Escalation for critical values
    any_critical = any(e.is_critical for e in evidence)
    if any_critical:
        confidence = min(confidence + 0.08, 0.98)

    # Minimum floor when we have any evidence = 0.45
    confidence = max(confidence, 0.45) if evidence else 0.0

    # Build reason string
    reason_parts = []
    for e in sorted(evidence, key=lambda x: x.weight, reverse=True):
        arrow = "↑" if e.direction == "HIGH" else "↓"
        crit  = " ⚠ CRITICAL" if e.is_critical else ""
        reason_parts.append(f"{e.name} {arrow}{e.value} (+{e.deviation_pct:.0f}%){crit}")

    return DiseaseScore(
        disease=disease_name,
        confidence=round(confidence, 4),
        evidence=evidence,
        icd10=disease_def.get("icd10", ""),
        category=disease_def.get("category", ""),
        reason="; ".join(reason_parts),
        is_critical=any_critical,
    )


def run_risk_scoring(
    disease_knowledge: dict,
    normalized_params: dict[str, float],
    param_statuses: dict[str, str],
    threshold: float = 0.40,
) -> list[DiseaseScore]:
    """
    Run the risk scoring engine over ALL diseases in the knowledge base.

    Args:
        disease_knowledge: Loaded disease_knowledge.json → "diseases" dict.
        normalized_params: {canonical_name: value}.
        param_statuses: {canonical_name: HIGH/LOW/NORMAL}.
        threshold: Minimum confidence to include in results.

    Returns:
        Sorted list of DiseaseScore (highest confidence first).
        Only diseases with evidence >= threshold are returned.
        If no biomarkers support a disease → it is NEVER returned.
    """
    scores: list[DiseaseScore] = []

    diseases = disease_knowledge.get("diseases", {})
    for disease_name, disease_def in diseases.items():
        result = score_disease(disease_name, disease_def, normalized_params, param_statuses)
        if result and result.confidence >= threshold:
            scores.append(result)

    scores.sort(key=lambda s: (s.confidence, s.is_critical), reverse=True)
    return scores
