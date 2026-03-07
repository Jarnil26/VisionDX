"""
VisionDX — ML Modules for Healthcare Predictions

Disease prediction, risk scoring, anomaly detection, and trend analysis.
"""
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from visiondx.database.models import (
    WeeklyFollowUp,
    Report,
    Parameter,
    HealthMetric,
)


@dataclass
class SymptomPrediction:
    """Symptom prediction result."""
    condition: str
    confidence: float
    severity: str  # low, medium, high, critical
    description: str
    required_tests: List[str]
    recommended_actions: List[str]


# ─────────────────────────────────────────────────────────────────────────
# 1️⃣ SYMPTOM CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────

class SymptomClassifier:
    """Classify symptoms and predict possible conditions."""

    # Rule-based symptom to condition mapping
    SYMPTOM_CONDITIONS = {
        "headache": {
            "conditions": [
                {
                    "name": "Migraine",
                    "confidence": 0.65,
                    "severity": "medium",
                    "tests": ["MRI", "Neurology Consult"],
                },
                {
                    "name": "Tension Headache",
                    "confidence": 0.45,
                    "severity": "low",
                    "tests": ["Physical Exam"],
                },
            ]
        },
        "stomach_pain": {
            "conditions": [
                {
                    "name": "Gastritis",
                    "confidence": 0.7,
                    "severity": "medium",
                    "tests": ["Endoscopy", "H. pylori Test"],
                },
                {
                    "name": "Indigestion",
                    "confidence": 0.5,
                    "severity": "low",
                    "tests": ["Ultrasound"],
                },
                {
                    "name": "IBS",
                    "confidence": 0.4,
                    "severity": "low",
                    "tests": ["Colonoscopy", "Dietary Assessment"],
                },
            ]
        },
        "chest_pain": {
            "conditions": [
                {
                    "name": "Angina",
                    "confidence": 0.85,
                    "severity": "critical",
                    "tests": ["ECG", "Cardiac Enzymes", "Angiography"],
                },
                {
                    "name": "Anxiety",
                    "confidence": 0.4,
                    "severity": "low",
                    "tests": ["Mental Health Evaluation"],
                },
            ]
        },
        "shortness_of_breath": {
            "conditions": [
                {
                    "name": "Asthma",
                    "confidence": 0.6,
                    "severity": "medium",
                    "tests": ["Spirometry", "Chest X-ray"],
                },
                {
                    "name": "COPD",
                    "confidence": 0.55,
                    "severity": "high",
                    "tests": ["Spirometry", "CT Scan"],
                },
                {
                    "name": "Heart Failure",
                    "confidence": 0.65,
                    "severity": "critical",
                    "tests": ["Echocardiogram", "BNP Test"],
                },
            ]
        },
        "fatigue": {
            "conditions": [
                {
                    "name": "Anemia",
                    "confidence": 0.6,
                    "severity": "medium",
                    "tests": ["CBC", "Iron Levels", "Vitamin B12"],
                },
                {
                    "name": "Thyroid Disorder",
                    "confidence": 0.55,
                    "severity": "medium",
                    "tests": ["TSH", "Free T3", "Free T4"],
                },
                {
                    "name": "Depression",
                    "confidence": 0.5,
                    "severity": "medium",
                    "tests": ["Mental Health Evaluation"],
                },
            ]
        },
        "fever": {
            "conditions": [
                {
                    "name": "Infection",
                    "confidence": 0.8,
                    "severity": "high",
                    "tests": ["CBC", "Blood Culture", "Inflammatory Markers"],
                },
                {
                    "name": "COVID-19",
                    "confidence": 0.7,
                    "severity": "high",
                    "tests": ["Rapid Antigen Test", "RT-PCR", "Chest X-ray"],
                },
            ]
        },
    }

    @classmethod
    def predict_from_symptoms(
        cls, symptoms: List[str], medical_history: Optional[dict] = None
    ) -> List[SymptomPrediction]:
        """Predict possible conditions from symptoms."""
        predictions = []
        seen_conditions = set()

        for symptom in symptoms:
            if symptom in cls.SYMPTOM_CONDITIONS:
                conditions = cls.SYMPTOM_CONDITIONS[symptom]["conditions"]

                for cond in conditions:
                    if cond["name"] not in seen_conditions:
                        predictions.append(
                            SymptomPrediction(
                                condition=cond["name"],
                                confidence=cond["confidence"],
                                severity=cond["severity"],
                                description=f"Possible {cond['name']} based on symptoms",
                                required_tests=cond["tests"],
                                recommended_actions=cls._get_recommendations(
                                    cond["name"]
                                ),
                            )
                        )
                        seen_conditions.add(cond["name"])

        # Sort by confidence
        predictions.sort(key=lambda x: x.confidence, reverse=True)
        return predictions[:5]  # Top 5 predictions

    @classmethod
    def _get_recommendations(cls, condition: str) -> List[str]:
        """Get recommendations for a condition."""
        recommendations = {
            "Migraine": [
                "Rest in quiet, dark room",
                "Stay hydrated",
                "Avoid triggers",
                "Consult neurologist",
            ],
            "Gastritis": [
                "Avoid spicy, fatty foods",
                "Eat small, frequent meals",
                "Avoid alcohol and smoking",
                "Stay hydrated",
                "Consult gastroenterologist",
            ],
            "Asthma": [
                "Use prescribed inhaler",
                "Avoid allergens and air pollution",
                "Regular exercise",
                "Maintain healthy weight",
            ],
            "Anemia": [
                "Eat iron-rich foods",
                "Take iron supplements if prescribed",
                "Increase vitamin C intake",
                "Consult hematologist",
            ],
        }

        return recommendations.get(condition, ["Consult with a healthcare provider"])


# ─────────────────────────────────────────────────────────────────────────
# 2️⃣ RISK SCORER
# ─────────────────────────────────────────────────────────────────────────

class RiskScorer:
    """Score overall health risk (0-100)."""

    @staticmethod
    def calculate_risk_score(
        predictions: List[SymptomPrediction],
        health_metrics: Optional[dict] = None,
        weekly_followups: Optional[List[dict]] = None,
    ) -> tuple[int, str]:  # (score, risk_level)
        """
        Calculate health risk score.

        **Returns:**
        - score: 0-100
        - risk_level: low (<25), medium (25-50), high (50-75), critical (>75)
        """
        score = 0

        # Factor 1: Condition severity (40 points)
        if predictions:
            max_severity_score = {
                "low": 10,
                "medium": 25,
                "high": 35,
                "critical": 40,
            }
            max_severity = max(p.severity for p in predictions)
            score += max_severity_score.get(max_severity, 0)

        # Factor 2: Health metrics (30 points)
        if health_metrics:
            # Check for critical metrics
            if health_metrics.get("glucose") and health_metrics["glucose"] > 300:
                score += 25  # Dangerously high glucose
            elif health_metrics.get("glucose") and health_metrics["glucose"] > 200:
                score += 15  # High glucose

            if health_metrics.get("bp_systolic") and health_metrics["bp_systolic"] > 180:
                score += 25  # Hypertensive crisis
            elif health_metrics.get("bp_systolic") and health_metrics["bp_systolic"] > 140:
                score += 10  # Hypertension

        # Factor 3: Recent trends (20 points)
        if weekly_followups and len(weekly_followups) >= 2:
            recent = weekly_followups[0]
            previous = weekly_followups[1]

            # Weight change
            if (
                recent.get("weight")
                and previous.get("weight")
                and (previous["weight"] - recent["weight"]) > 5
            ):
                score += 10  # Rapid weight loss

            # Stress trend
            if (
                recent.get("stress_level")
                and previous.get("stress_level")
                and recent["stress_level"] > previous["stress_level"] + 3
            ):
                score += 10  # Rising stress

        # Factor 4: Confidence in predictions (10 points)
        if predictions and predictions[0].confidence > 0.8:
            score += 10

        # Cap at 100
        score = min(score, 100)

        # Determine risk level
        if score < 25:
            risk_level = "low"
        elif score < 50:
            risk_level = "medium"
        elif score < 75:
            risk_level = "high"
        else:
            risk_level = "critical"

        return int(score), risk_level


# ─────────────────────────────────────────────────────────────────────────
# 3️⃣ TREND ANALYZER
# ─────────────────────────────────────────────────────────────────────────

class TrendAnalyzer:
    """Analyze health trends over time."""

    @staticmethod
    def analyze_weight_trend(metrics: List[dict], days: int = 30) -> dict:
        """
        Analyze weight trend.

        **Returns:**
        - trend: increasing | decreasing | stable
        - rate_per_week: kg/week
        - is_concerning: bool
        """
        if not metrics or len(metrics) < 2:
            return {"trend": "unknown", "rate_per_week": 0, "is_concerning": False}

        weights = [m["value"] for m in metrics if m["metric_name"] == "weight"]

        if len(weights) < 2:
            return {"trend": "unknown", "rate_per_week": 0, "is_concerning": False}

        first_weight = weights[0]
        last_weight = weights[-1]
        weight_change = last_weight - first_weight
        rate_per_week = (weight_change / days) * 7

        if abs(rate_per_week) < 0.5:
            trend = "stable"
            is_concerning = False
        elif rate_per_week < -2:
            trend = "decreasing"
            is_concerning = True  # Rapid weight loss
        elif rate_per_week > 2:
            trend = "increasing"
            is_concerning = True  # Rapid weight gain
        elif rate_per_week < 0:
            trend = "decreasing"
            is_concerning = False
        else:
            trend = "increasing"
            is_concerning = False

        return {
            "trend": trend,
            "rate_per_week": round(rate_per_week, 2),
            "is_concerning": is_concerning,
            "total_change": round(weight_change, 2),
        }

    @staticmethod
    def analyze_stress_trend(followups: List[dict], weeks: int = 4) -> dict:
        """Analyze stress level trend."""
        if not followups:
            return {"trend": "unknown", "average": 0, "is_concerning": False}

        stress_levels = [
            f.get("stress_level", 0) for f in followups if f.get("stress_level")
        ]

        if not stress_levels:
            return {"trend": "unknown", "average": 0, "is_concerning": False}

        average_stress = np.mean(stress_levels)
        is_concerning = average_stress > 7  # > 7/10 is concerning

        if len(stress_levels) >= 2:
            trend_slope = (
                stress_levels[-1] - stress_levels[0]
            ) / len(stress_levels)
            if trend_slope > 0.5:
                trend = "increasing"
            elif trend_slope < -0.5:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "unknown"

        return {
            "trend": trend,
            "average": round(average_stress, 1),
            "is_concerning": is_concerning,
        }


# ─────────────────────────────────────────────────────────────────────────
# 4️⃣ ANOMALY DETECTOR
# ─────────────────────────────────────────────────────────────────────────

class AnomalyDetector:
    """Detect anomalies in health data."""

    @staticmethod
    def detect_parameter_anomalies(
        parameters: List[dict],
    ) -> List[dict]:
        """Detect abnormal lab parameters."""
        anomalies = []

        reference_ranges = {
            "Hemoglobin": {"L": {"min": 13, "max": 17}, "M": {"min": 13.5, "max": 17.5}},
            "WBC": {"min": 4, "max": 11},
            "Platelets": {"min": 150, "max": 400},
            "Glucose": {"min": 70, "max": 100},
            "Cholesterol": {"min": 0, "max": 200},
            "TSH": {"min": 0.4, "max": 4},
        }

        for param in parameters:
            name = param.get("name")
            value = param.get("value")

            if not name or value is None:
                continue

            if name in reference_ranges:
                ranges = reference_ranges[name]
                if isinstance(ranges, dict) and "min" in ranges:
                    min_val, max_val = ranges["min"], ranges["max"]
                    if value < min_val:
                        anomalies.append(
                            {
                                "parameter": name,
                                "value": value,
                                "status": "LOW",
                                "severity": "warning" if value > min_val - 5 else "critical",
                            }
                        )
                    elif value > max_val:
                        anomalies.append(
                            {
                                "parameter": name,
                                "value": value,
                                "status": "HIGH",
                                "severity": "warning" if value < max_val + 10 else "critical",
                            }
                        )

        return anomalies


# ─────────────────────────────────────────────────────────────────────────
# 5️⃣ HEALTH PREDICTOR (Main Orchestrator)
# ─────────────────────────────────────────────────────────────────────────

class HealthPredictor:
    """Main ML orchestrator for health predictions."""

    def __init__(self):
        self.symptom_classifier = SymptomClassifier()
        self.risk_scorer = RiskScorer()
        self.trend_analyzer = TrendAnalyzer()
        self.anomaly_detector = AnomalyDetector()

    def predict_health_status(
        self,
        symptoms: List[str],
        medical_history: Optional[dict] = None,
        health_metrics: Optional[dict] = None,
        recent_reports: Optional[List[dict]] = None,
        weekly_followups: Optional[List[dict]] = None,
    ) -> dict:
        """
        Complete health prediction workflow.

        **Returns:**
        {
            "conditions": [...],
            "risk_score": 0-100,
            "risk_level": "low|medium|high|critical",
            "trends": {...},
            "anomalies": [...],
            "recommendations": [...]
        }
        """
        # 1. Predict conditions from symptoms
        conditions = self.symptom_classifier.predict_from_symptoms(
            symptoms, medical_history
        )

        # 2. Score risk
        risk_score, risk_level = self.risk_scorer.calculate_risk_score(
            conditions, health_metrics, weekly_followups
        )

        # 3. Analyze trends
        trends = {}
        if health_metrics:
            trends["weight"] = self.trend_analyzer.analyze_weight_trend(
                health_metrics.get("weight_history", [])
            )
            trends["stress"] = self.trend_analyzer.analyze_stress_trend(
                weekly_followups or []
            )

        # 4. Detect anomalies
        anomalies = []
        if recent_reports:
            for report in recent_reports:
                anomalies.extend(
                    self.anomaly_detector.detect_parameter_anomalies(
                        report.get("parameters", [])
                    )
                )

        # 5. Compile recommendations
        recommendations = []
        for condition in conditions[:3]:  # Top 3 conditions
            recommendations.extend(condition.recommended_actions)

        if risk_level == "critical":
            recommendations.insert(
                0, "URGENT: Seek immediate medical attention"
            )

        return {
            "conditions": [
                {
                    "condition": c.condition,
                    "confidence": c.confidence,
                    "severity": c.severity,
                    "required_tests": c.required_tests,
                }
                for c in conditions
            ],
            "risk_score": risk_score,
            "risk_level": risk_level,
            "trends": trends,
            "anomalies": anomalies,
            "recommendations": list(set(recommendations))[:10],  # Top 10 unique recommendations
            "urgent_action_needed": risk_level == "critical",
        }


# ─────────────────────────────────────────────────────────────────────────
# Singleton Instance
# ─────────────────────────────────────────────────────────────────────────

_predictor_instance = None


def get_health_predictor() -> HealthPredictor:
    """Get singleton instance of health predictor."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = HealthPredictor()
    return _predictor_instance
