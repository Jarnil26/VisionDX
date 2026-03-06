"""
VisionDX — Dynamic Disease Engine

Master orchestrator for the knowledge-driven disease analysis pipeline:

  Extracted Parameters
        ↓
  LOINC Normalization (loinc_mapper.py)
        ↓
  Abnormal Status per Parameter
        ↓
  Risk Scoring against Disease KB (risk_scoring.py + disease_knowledge.json)
        ↓
  DiseaseScore list (only conditions with biomarker support)

Key design principle:
  IF no biomarkers support a disease → it is NEVER returned.
  The list is 100% driven by what's actually abnormal in the patient's report.
"""
from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache
from typing import Any

from loguru import logger

_KB_PATH = Path(__file__).parent / "disease_knowledge.json"


@lru_cache(maxsize=1)
def _load_knowledge_base() -> dict:
    """Load disease knowledge base from JSON (cached after first load)."""
    if not _KB_PATH.exists():
        logger.error(f"Disease knowledge base not found: {_KB_PATH}")
        return {}
    with open(_KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)
    logger.info(f"Disease KB loaded: {len(kb.get('diseases', {}))} diseases")
    return kb


class DynamicDiseaseEngine:
    """
    Analyzes a patient's lab parameters against the disease knowledge base
    and returns evidence-backed disease risk scores.

    This is NOT a fixed classifier. It only returns diseases that have
    actual biomarker support from the patient's lab report.
    """

    def __init__(self, score_threshold: float = 0.40):
        self.threshold = score_threshold
        self._kb = _load_knowledge_base()

    def analyze(
        self,
        parameters: list[Any],  # list of ParsedParameter objects
    ) -> list[dict]:
        """
        Full pipeline: normalize → abnormal detect → score → return.

        Args:
            parameters: list of ParsedParameter with .name, .value, .status

        Returns:
            List of dicts sorted by confidence desc, only biomarker-supported diseases.
        """
        from visiondx.loinc.loinc_mapper import normalize_lab_name
        from visiondx.ml.risk_scoring import run_risk_scoring

        if not self._kb:
            logger.warning("Disease KB not loaded — engine cannot run")
            return []

        # ── 1. Build normalized parameter map ─────────────────────────────────
        normalized_params: dict[str, float] = {}
        param_statuses: dict[str, str] = {}

        for p in parameters:
            if p.value is None:
                continue
            try:
                canonical = normalize_lab_name(p.name)
                val = float(p.value)
                normalized_params[canonical] = val
                param_statuses[canonical] = getattr(p, "status", "NORMAL") or "NORMAL"

                # Also index by original name (some reports use non-standard names)
                if p.name != canonical:
                    normalized_params[p.name] = val
                    param_statuses[p.name] = param_statuses[canonical]
            except (ValueError, TypeError):
                pass

        logger.debug(
            f"Disease engine: {len(normalized_params)} params normalized, "
            f"{sum(1 for s in param_statuses.values() if s != 'NORMAL')} abnormal"
        )

        # ── 2. Run risk scoring ────────────────────────────────────────────────
        scores = run_risk_scoring(
            disease_knowledge=self._kb,
            normalized_params=normalized_params,
            param_statuses=param_statuses,
            threshold=self.threshold,
        )

        logger.info(
            f"Disease engine: {len(scores)} conditions detected "
            f"(threshold={self.threshold:.0%})"
        )

        # ── 3. Format output ───────────────────────────────────────────────────
        results = []
        for s in scores:
            results.append({
                "disease":     s.disease,
                "confidence":  s.confidence,
                "icd10":       s.icd10,
                "category":    s.category,
                "reason":      s.reason,
                "is_critical": s.is_critical,
                "markers_fired": [
                    {
                        "name":          e.name,
                        "value":         e.value,
                        "direction":     e.direction,
                        "deviation_pct": e.deviation_pct,
                        "is_critical":   e.is_critical,
                    }
                    for e in s.evidence
                ],
            })

        return results

    def analyze_from_dict(
        self,
        param_dict: dict[str, float | str],  # {"Glucose": 141, "IgE": 492, ...}
        abnormal_override: dict[str, str] | None = None,
    ) -> list[dict]:
        """
        Analyze from a raw dictionary of {parameter_name: value}.
        Useful for API testing without a parsed PDF.

        If abnormal_override is not provided, uses a mock detector
        that compares to standard thresholds.
        """
        from visiondx.loinc.loinc_mapper import normalize_lab_name
        from visiondx.ml.risk_scoring import run_risk_scoring

        if not self._kb:
            return []

        normalized_params: dict[str, float] = {}
        param_statuses: dict[str, str] = {}

        for raw_name, raw_value in param_dict.items():
            try:
                val = float(raw_value)
                canonical = normalize_lab_name(raw_name)
                normalized_params[canonical] = val
                # Use override if provided, otherwise mark unknown
                status = "NORMAL"
                if abnormal_override:
                    status = abnormal_override.get(raw_name,
                               abnormal_override.get(canonical, "NORMAL"))
                param_statuses[canonical] = status
            except (ValueError, TypeError):
                pass

        scores = run_risk_scoring(
            disease_knowledge=self._kb,
            normalized_params=normalized_params,
            param_statuses=param_statuses,
            threshold=self.threshold,
        )

        return [
            {
                "disease":    s.disease,
                "confidence": s.confidence,
                "icd10":      s.icd10,
                "category":   s.category,
                "reason":     s.reason,
                "is_critical":s.is_critical,
            }
            for s in scores
        ]

    def format_report(self, results: list[dict]) -> str:
        """
        Format analysis results as a plain-text clinical report.
        Matches the output format specified in the architecture requirements.
        """
        if not results:
            return "No significant health risks detected based on available lab parameters."

        lines = ["AI Lab Report Analysis", "=" * 50, "", "Possible Health Risks", "-" * 30]
        for r in results:
            pct = int(r["confidence"] * 100)
            crit = " ⚠ CRITICAL" if r["is_critical"] else ""
            category = f"[{r['category']}]" if r["category"] else ""
            lines.append(f"  {r['disease']}{crit} — {pct}%  {category}")
            if r.get("reason"):
                lines.append(f"    ↳ {r['reason']}")
        lines += [
            "",
            "─" * 50,
            "⚕ IMPORTANT: This analysis is AI-generated.",
            "  Always consult a qualified physician before",
            "  making any clinical decisions.",
        ]
        return "\n".join(lines)


# Singleton
_engine = DynamicDiseaseEngine()


def analyze_lab_report(parameters: list) -> list[dict]:
    """Convenience function — run full engine on parameter list."""
    return _engine.analyze(parameters)


def format_analysis_report(results: list[dict]) -> str:
    """Format results as a printable report."""
    return _engine.format_report(results)
