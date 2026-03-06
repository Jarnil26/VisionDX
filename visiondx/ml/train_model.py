"""
VisionDX — ML Model Trainer

Trains RandomForest and XGBoost classifiers on blood test data,
evaluates both, and saves the best performer.

Run:
    python -m visiondx.ml.train_model

Outputs:
    visiondx/ml/models/disease_predictor.pkl
    visiondx/ml/models/label_encoder.pkl
    visiondx/ml/models/feature_names.pkl
    visiondx/ml/models/training_report.txt
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available, using RandomForest only")

DATA_PATH = Path(__file__).parent / "training_data.csv"
MODEL_DIR = Path(__file__).parent / "models"

# 20-feature set — must match generate_data.py and predictor.py
FEATURES = [
    "Hemoglobin", "WBC", "Platelets", "Glucose", "Total Cholesterol",
    "RBC", "Creatinine", "TSH",
    "HbA1c", "Vitamin D", "Vitamin B12", "IgE", "Homocysteine",
    "ALT", "AST", "LDL Cholesterol", "Triglycerides", "Ferritin", "CRP", "Uric Acid",
]


def load_data() -> tuple[np.ndarray, np.ndarray, LabelEncoder]:
    if not DATA_PATH.exists():
        logger.info("Data not found — generating synthetic dataset first...")
        from visiondx.ml.generate_data import generate_dataset
        df = generate_dataset()
        df.to_csv(DATA_PATH, index=False)
    else:
        df = pd.read_csv(DATA_PATH)

    logger.info(f"Loaded {len(df)} samples, {df['Disease'].nunique()} classes")

    le = LabelEncoder()
    X = df[FEATURES].values
    y = le.fit_transform(df["Disease"].values)
    return X, y, le


def train_and_evaluate() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    X, y, le = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ── Random Forest ─────────────────────────────────────────────────────────
    rf_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clf", RandomForestClassifier(
            n_estimators=300,
            max_depth=15,
            min_samples_split=3,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])
    logger.info("Training RandomForest...")
    rf_pipeline.fit(X_train, y_train)
    rf_preds = rf_pipeline.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_preds)
    logger.info(f"RandomForest Test Accuracy: {rf_acc:.4f}")

    best_model = rf_pipeline
    best_name = "RandomForest"
    best_acc = rf_acc

    # ── XGBoost ───────────────────────────────────────────────────────────────
    if XGBOOST_AVAILABLE:
        xgb_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                use_label_encoder=False,
                eval_metric="mlogloss",
                random_state=42,
                n_jobs=-1,
            )),
        ])
        logger.info("Training XGBoost...")
        xgb_pipeline.fit(X_train, y_train)
        xgb_preds = xgb_pipeline.predict(X_test)
        xgb_acc = accuracy_score(y_test, xgb_preds)
        logger.info(f"XGBoost Test Accuracy: {xgb_acc:.4f}")

        if xgb_acc > best_acc:
            best_model = xgb_pipeline
            best_name = "XGBoost"
            best_acc = xgb_acc

    logger.success(f"Best model: {best_name} (accuracy: {best_acc:.4f})")

    # ── Classification Report ─────────────────────────────────────────────────
    final_preds = best_model.predict(X_test)
    report_str = classification_report(
        y_test, final_preds, target_names=le.classes_
    )
    logger.info(f"\n{report_str}")

    # Save report
    report_path = MODEL_DIR / "training_report.txt"
    with open(report_path, "w") as f:
        f.write(f"Best Model: {best_name}\n")
        f.write(f"Test Accuracy: {best_acc:.4f}\n\n")
        f.write(report_str)

    # ── Cross Validation ──────────────────────────────────────────────────────
    cv_scores = cross_val_score(
        best_model, X, y,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring="accuracy",
        n_jobs=-1,
    )
    logger.info(f"5-fold CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Save Artifacts ────────────────────────────────────────────────────────
    model_path = MODEL_DIR / "disease_predictor.pkl"
    le_path = MODEL_DIR / "label_encoder.pkl"
    feat_path = MODEL_DIR / "feature_names.pkl"
    meta_path = MODEL_DIR / "model_meta.json"

    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)

    with open(le_path, "wb") as f:
        pickle.dump(le, f)

    with open(feat_path, "wb") as f:
        pickle.dump(FEATURES, f)

    with open(meta_path, "w") as f:
        json.dump({
            "model_name": best_name,
            "accuracy": float(best_acc),
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "features": FEATURES,
            "classes": list(le.classes_),
            "n_samples": len(X),
        }, f, indent=2)

    logger.success(f"Model saved to {model_path}")
    logger.success(f"Training complete! Artifacts in {MODEL_DIR}")


if __name__ == "__main__":
    train_and_evaluate()
