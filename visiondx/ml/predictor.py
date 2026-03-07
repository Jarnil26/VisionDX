"""
VisionDX — Disease Predictor (Unified Inference Engine)

Three-layer prediction pipeline:
  Layer 1: Dynamic Disease Engine (disease_knowledge.json + LOINC + risk_scoring)
           → Evidence-based, works on ALL parameters, no fixed disease list
  Layer 2: Medical Rules Engine (medical_rules.py)
           → Clinical rules for 18 conditions, catches edge cases
  Layer 3: ML Model (XGBoost/RandomForest)
           → Trained classifier for 15 diseases when model is available

All three layers run in parallel. Results are merged, de-duplicated,
and returned sorted by confidence. Only conditions with actual biomarker
support appear in the output.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from visiondx.database.schemas import ParsedParameter, PredictionOut

_MODEL_DIR = Path(__file__).parent / "models"

# 20-feature ML model feature set
FEATURES = [
    "Hemoglobin", "WBC", "Platelets", "Glucose", "Total Cholesterol",
    "RBC", "Creatinine", "TSH",
    "HbA1c", "Vitamin D", "Vitamin B12", "IgE", "Homocysteine",
    "ALT", "AST", "LDL Cholesterol", "Triglycerides", "Ferritin", "CRP", "Uric Acid",
]

# Mapping: disease engine names → ML class names (for merging)
_ENGINE_TO_ML: dict[str, str] = {
    "Diabetes Mellitus (Type 2)":           "Diabetes",
    "Pre-Diabetes / Impaired Glucose":      "Diabetes",
    "Anemia (General)":                     "Anemia",
    "Iron Deficiency Anemia":               "Iron Deficiency",
    "Thyroid Hypothyroidism":               "Thyroid Imbalance",
    "Thyroid Hyperthyroidism":              "Thyroid Imbalance",
    "Hypothyroidism — Subclinical":         "Thyroid Imbalance",
    "Chronic Kidney Disease":               "Kidney Disorder",
    "Kidney Function — Low BUN/Urea":       "Kidney Disorder",
    "Acute Liver Disease":                  "Liver Disease",
    "Fatty Liver Disease (NAFLD)":          "Liver Disease",
    "Hyperlipidemia":                       "Hyperlipidemia",
    "Systemic Infection / Sepsis Risk":     "Infection",
    "Viral Infection / Leukopenia":         "Infection",
    "Allergic Disease / Atopy":             "Allergy / High IgE",
}


class DiseasePredictor:
    """
    Unified disease predictor — combines three layers:
    1. Dynamic knowledge engine (JSON KB + LOINC + risk scoring)
    2. Rule-based medical engine
    3. ML classification model
    """

    _instance: "DiseasePredictor | None" = None

    def __init__(self) -> None:
        self._model         = None
        self._label_encoder = None
        self._loaded        = False
        self._load()

    @classmethod
    def get(cls) -> "DiseasePredictor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        import os
        model_env = os.getenv("MODEL_PATH")
        if model_env:
            model_path = Path(model_env)
            le_path    = model_path.parent / "label_encoder.pkl"
        else:
            model_path = _MODEL_DIR / "disease_predictor.pkl"
            le_path    = _MODEL_DIR / "label_encoder.pkl"

        if not model_path.exists():
            logger.warning(f"ML model not found at {model_path}. Run `python -m visiondx.ml.train_model` to train.")
            return
        try:
            with open(model_path, "rb") as f:
                self._model = pickle.load(f)
            with open(le_path, "rb") as f:
                self._label_encoder = pickle.load(f)
            self._loaded = True
            logger.success("Disease prediction model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    def predict(
        self,
        parameters: list[ParsedParameter],
        top_n: int = 12,
    ) -> list[PredictionOut]:
        """
        Full three-layer disease prediction.

        Layer 1 — Dynamic engine (always runs; no training needed)
        Layer 2 — Medical rules engine (always runs)
        Layer 3 — ML model (only when trained model exists)

        All layers merged → sorted by confidence → top_n returned.
        """
        merged: dict[str, float] = {}  # {disease_name: confidence}

        # ── Layer 1: Dynamic Disease Engine ──────────────────────────────────
        try:
            from visiondx.ml.disease_engine import analyze_lab_report
            engine_results = analyze_lab_report(parameters)
            for r in engine_results:
                merged[r["disease"]] = r["confidence"]
            logger.info(f"[Layer 1] Dynamic engine: {len(engine_results)} conditions")
        except Exception as e:
            logger.error(f"[Layer 1] Disease engine failed: {e}")

        # ── Layer 2: Medical Rules Engine ────────────────────────────────────
        try:
            from visiondx.ml.medical_rules import apply_medical_rules
            rule_results = apply_medical_rules(parameters, threshold=0.40)
            for r in rule_results:
                existing = merged.get(r.disease)
                if existing is not None:
                    # Both engines agree — slight boost
                    merged[r.disease] = min(0.98, max(existing, r.confidence) + 0.02)
                else:
                    merged[r.disease] = r.confidence
            logger.info(f"[Layer 2] Rules engine: {len(rule_results)} conditions")
        except Exception as e:
            logger.error(f"[Layer 2] Rules engine failed: {e}")

        # ── Layer 3: ML Model ─────────────────────────────────────────────────
        if self._loaded and self._model is not None:
            try:
                X = np.array([self._build_feature_vector(parameters)])
                proba   = self._model.predict_proba(X)[0]
                classes = self._label_encoder.classes_
                for i, cls in enumerate(classes):
                    if proba[i] < 0.05 or cls.lower() == "normal":
                        continue
                    ml_conf = float(proba[i])
                    # Find if this ML class maps to an existing engine disease
                    matched = False
                    for eng_name, ml_name in _ENGINE_TO_ML.items():
                        if ml_name == cls and eng_name in merged:
                            merged[eng_name] = min(0.98, max(merged[eng_name], ml_conf) + 0.03)
                            matched = True
                    if not matched:
                        existing = merged.get(cls)
                        if existing:
                            merged[cls] = min(0.98, max(existing, ml_conf) + 0.03)
                        elif ml_conf >= 0.15:
                            merged[cls] = ml_conf
                logger.info(f"[Layer 3] ML model: integrated")
            except Exception as e:
                logger.error(f"[Layer 3] ML model failed: {e}")

        # ── Final sort & output ───────────────────────────────────────────────
        # Remove "Normal" from results
        merged.pop("Normal", None)
        sorted_items = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        predictions = [
            PredictionOut(disease=d, confidence=round(c, 4))
            for d, c in sorted_items[:top_n]
            if c >= 0.05
        ]

        logger.info(
            f"Unified engine: {len(predictions)} final predictions "
            f"(Dynamic={len(merged)} pre-dedup)"
        )
        return predictions

    def predict_from_dict(
        self,
        param_dict: dict[str, float],
        top_n: int = 12,
    ) -> list[PredictionOut]:
        """Predict from a raw {param_name: value} dict — for API/testing."""
        from visiondx.ml.disease_engine import DynamicDiseaseEngine
        engine = DynamicDiseaseEngine()
        results = engine.analyze_from_dict(param_dict)
        return [
            PredictionOut(disease=r["disease"], confidence=round(r["confidence"], 4))
            for r in results[:top_n]
        ]

    def _build_feature_vector(self, parameters: list[ParsedParameter]) -> list[float]:
        """Build ML 20-feature vector using LOINC normalization."""
        from visiondx.loinc.loinc_mapper import normalize_lab_name
        from visiondx.ml.medical_rules import ALIASES, _normalize

        pm: dict[str, float] = {}
        for p in parameters:
            if p.value is None:
                continue
            try:
                val = float(p.value)
                canonical = normalize_lab_name(p.name)
                pm[canonical] = val
                pm[p.name] = val
                # Medical rules aliases
                alias_key = ALIASES.get(_normalize(p.name))
                if alias_key:
                    pm[alias_key] = val
            except (ValueError, TypeError):
                pass

        return [pm.get(feat, np.nan) for feat in FEATURES]

    @property
    def is_ready(self) -> bool:
        return self._loaded
