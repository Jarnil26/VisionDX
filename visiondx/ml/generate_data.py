"""
VisionDX — Synthetic Training Data Generator (v2)

Generates realistic blood test training data for 15 disease classes.
Features cover 20 blood parameters including vitamins, lipids, liver,
and kidney markers for comprehensive disease prediction.

Run:
    python -m visiondx.ml.generate_data
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from loguru import logger

RNG = np.random.default_rng(42)
OUTPUT_PATH = Path(__file__).parent / "training_data.csv"

# ── 20 features ──────────────────────────────────────────────────────────────
#  0  Hemoglobin       g/dL      normal: M 13.5-17.5, F 12-15.5
#  1  WBC              ×10³/μL   normal: 4.5-11
#  2  Platelets        ×10³/μL   normal: 150-400
#  3  Glucose          mg/dL     fasting normal: 74-106
#  4  Total Cholesterol mg/dL   normal: <200
#  5  RBC              ×10⁶/μL   normal: 4.5-5.5
#  6  Creatinine       mg/dL     normal: 0.6-1.2
#  7  TSH              mIU/L     normal: 0.4-4.5
#  8  HbA1c            %         normal: 4.0-5.6  (standard %)
#  9  Vitamin D        ng/mL     normal: 30-100
# 10  Vitamin B12      pg/mL     normal: 187-833
# 11  IgE              IU/mL     normal: 0-87
# 12  Homocysteine     μmol/L    normal: 6.0-14.8
# 13  ALT              U/L       normal: 7-40
# 14  AST              U/L       normal: 10-40
# 15  LDL Cholesterol  mg/dL     normal: <130
# 16  Triglycerides    mg/dL     normal: <150
# 17  Ferritin         ng/mL     normal: M 30-300, F 12-150
# 18  CRP              mg/L      normal: <5
# 19  Uric Acid        mg/dL     normal: M 3.4-7.0, F 2.4-6.0

FEATURES = [
    "Hemoglobin", "WBC", "Platelets", "Glucose", "Total Cholesterol",
    "RBC", "Creatinine", "TSH",
    "HbA1c", "Vitamin D", "Vitamin B12", "IgE", "Homocysteine",
    "ALT", "AST", "LDL Cholesterol", "Triglycerides", "Ferritin", "CRP", "Uric Acid",
]

# Each class: {feature: (mean, std)}   (NaN → not typically altered)
DISEASE_PROFILES: dict[str, dict[str, tuple[float, float]]] = {
    "Normal": {
        "Hemoglobin": (14.0, 1.0), "WBC": (7.0, 1.5), "Platelets": (250, 40),
        "Glucose": (90, 10), "Total Cholesterol": (175, 20), "RBC": (4.8, 0.3),
        "Creatinine": (0.9, 0.15), "TSH": (2.0, 0.8), "HbA1c": (5.2, 0.3),
        "Vitamin D": (38, 8), "Vitamin B12": (450, 100), "IgE": (40, 20),
        "Homocysteine": (10, 2), "ALT": (22, 8), "AST": (24, 8),
        "LDL Cholesterol": (100, 20), "Triglycerides": (100, 30),
        "Ferritin": (80, 30), "CRP": (1.5, 1.0), "Uric Acid": (5.0, 1.0),
    },
    "Anemia": {
        "Hemoglobin": (8.5, 1.5), "WBC": (7.0, 2.0), "Platelets": (180, 50),
        "Glucose": (88, 12), "Total Cholesterol": (170, 25), "RBC": (3.2, 0.5),
        "Creatinine": (0.9, 0.2), "TSH": (2.1, 1.0), "HbA1c": (5.1, 0.3),
        "Vitamin D": (30, 10), "Vitamin B12": (350, 100), "IgE": (45, 25),
        "Homocysteine": (11, 3), "ALT": (20, 7), "AST": (22, 7),
        "LDL Cholesterol": (100, 20), "Triglycerides": (95, 30),
        "Ferritin": (8, 5), "CRP": (2.0, 1.5), "Uric Acid": (4.8, 1.0),
    },
    "Iron Deficiency": {
        "Hemoglobin": (10.0, 1.5), "WBC": (6.5, 1.5), "Platelets": (320, 70),
        "Glucose": (87, 10), "Total Cholesterol": (168, 22), "RBC": (3.8, 0.4),
        "Creatinine": (0.85, 0.15), "TSH": (2.2, 0.9), "HbA1c": (5.1, 0.3),
        "Vitamin D": (28, 8), "Vitamin B12": (320, 90), "IgE": (42, 22),
        "Homocysteine": (12, 3), "ALT": (18, 6), "AST": (20, 6),
        "LDL Cholesterol": (95, 18), "Triglycerides": (90, 28),
        "Ferritin": (6, 4), "CRP": (1.8, 1.2), "Uric Acid": (4.5, 0.8),
    },
    "Diabetes": {
        "Hemoglobin": (13.5, 1.2), "WBC": (8.0, 2.0), "Platelets": (240, 50),
        "Glucose": (200, 45), "Total Cholesterol": (215, 30), "RBC": (4.7, 0.4),
        "Creatinine": (1.1, 0.3), "TSH": (2.0, 0.8), "HbA1c": (8.2, 1.5),
        "Vitamin D": (22, 8), "Vitamin B12": (380, 100), "IgE": (55, 30),
        "Homocysteine": (13, 3), "ALT": (28, 10), "AST": (30, 10),
        "LDL Cholesterol": (135, 30), "Triglycerides": (200, 60),
        "Ferritin": (75, 30), "CRP": (4.0, 2.0), "Uric Acid": (5.8, 1.5),
    },
    "Infection": {
        "Hemoglobin": (12.5, 1.5), "WBC": (18.0, 4.0), "Platelets": (350, 80),
        "Glucose": (100, 15), "Total Cholesterol": (165, 20), "RBC": (4.5, 0.4),
        "Creatinine": (1.0, 0.25), "TSH": (2.0, 0.9), "HbA1c": (5.2, 0.3),
        "Vitamin D": (22, 8), "Vitamin B12": (400, 120), "IgE": (60, 35),
        "Homocysteine": (11, 3), "ALT": (35, 15), "AST": (38, 15),
        "LDL Cholesterol": (95, 20), "Triglycerides": (140, 40),
        "Ferritin": (200, 80), "CRP": (30, 15), "Uric Acid": (5.5, 1.2),
    },
    "Liver Disease": {
        "Hemoglobin": (11.0, 1.5), "WBC": (8.5, 2.5), "Platelets": (120, 30),
        "Glucose": (95, 20), "Total Cholesterol": (155, 30), "RBC": (3.8, 0.5),
        "Creatinine": (0.95, 0.2), "TSH": (2.1, 0.8), "HbA1c": (5.0, 0.3),
        "Vitamin D": (18, 7), "Vitamin B12": (280, 80), "IgE": (50, 30),
        "Homocysteine": (14, 4), "ALT": (120, 60), "AST": (110, 55),
        "LDL Cholesterol": (88, 22), "Triglycerides": (170, 55),
        "Ferritin": (280, 100), "CRP": (12, 8), "Uric Acid": (6.2, 1.5),
    },
    "Kidney Disorder": {
        "Hemoglobin": (10.5, 1.5), "WBC": (9.0, 2.5), "Platelets": (210, 50),
        "Glucose": (95, 15), "Total Cholesterol": (200, 30), "RBC": (3.5, 0.5),
        "Creatinine": (2.8, 0.7), "TSH": (2.3, 1.0), "HbA1c": (5.3, 0.5),
        "Vitamin D": (15, 6), "Vitamin B12": (350, 100), "IgE": (55, 30),
        "Homocysteine": (18, 5), "ALT": (25, 10), "AST": (28, 10),
        "LDL Cholesterol": (115, 25), "Triglycerides": (175, 55),
        "Ferritin": (120, 50), "CRP": (8, 5), "Uric Acid": (8.5, 1.5),
    },
    "Thyroid Imbalance": {
        "Hemoglobin": (12.8, 1.5), "WBC": (7.5, 2.0), "Platelets": (245, 45),
        "Glucose": (92, 12), "Total Cholesterol": (215, 35), "RBC": (4.5, 0.4),
        "Creatinine": (0.9, 0.2), "TSH": (9.0, 3.0), "HbA1c": (5.1, 0.3),
        "Vitamin D": (26, 8), "Vitamin B12": (380, 100), "IgE": (48, 25),
        "Homocysteine": (13, 4), "ALT": (22, 8), "AST": (24, 8),
        "LDL Cholesterol": (128, 28), "Triglycerides": (130, 40),
        "Ferritin": (60, 25), "CRP": (2.5, 1.5), "Uric Acid": (5.5, 1.2),
    },
    "Hyperlipidemia": {
        "Hemoglobin": (13.8, 1.2), "WBC": (7.2, 1.5), "Platelets": (255, 40),
        "Glucose": (100, 12), "Total Cholesterol": (260, 35), "RBC": (4.8, 0.3),
        "Creatinine": (0.9, 0.15), "TSH": (2.1, 0.8), "HbA1c": (5.4, 0.4),
        "Vitamin D": (30, 8), "Vitamin B12": (420, 110), "IgE": (45, 25),
        "Homocysteine": (13, 3), "ALT": (30, 10), "AST": (28, 10),
        "LDL Cholesterol": (175, 35), "Triglycerides": (250, 70),
        "Ferritin": (85, 30), "CRP": (3.0, 1.8), "Uric Acid": (5.8, 1.2),
    },
    "Vitamin D Deficiency": {
        "Hemoglobin": (13.5, 1.0), "WBC": (7.0, 1.5), "Platelets": (255, 40),
        "Glucose": (92, 10), "Total Cholesterol": (178, 22), "RBC": (4.7, 0.3),
        "Creatinine": (0.9, 0.15), "TSH": (2.2, 0.8), "HbA1c": (5.2, 0.3),
        "Vitamin D": (9, 3), "Vitamin B12": (400, 100), "IgE": (42, 22),
        "Homocysteine": (11, 2.5), "ALT": (22, 8), "AST": (24, 8),
        "LDL Cholesterol": (105, 20), "Triglycerides": (110, 30),
        "Ferritin": (70, 25), "CRP": (2.5, 1.5), "Uric Acid": (5.0, 1.0),
    },
    "Vitamin B12 Deficiency": {
        "Hemoglobin": (11.5, 1.5), "WBC": (6.5, 1.5), "Platelets": (180, 45),
        "Glucose": (90, 10), "Total Cholesterol": (172, 22), "RBC": (3.6, 0.4),
        "Creatinine": (0.88, 0.15), "TSH": (2.1, 0.8), "HbA1c": (5.1, 0.3),
        "Vitamin D": (28, 8), "Vitamin B12": (130, 40), "IgE": (44, 22),
        "Homocysteine": (22, 6), "ALT": (20, 7), "AST": (22, 7),
        "LDL Cholesterol": (98, 18), "Triglycerides": (100, 28),
        "Ferritin": (65, 25), "CRP": (2.0, 1.2), "Uric Acid": (4.8, 0.9),
    },
    "Allergy / High IgE": {
        "Hemoglobin": (13.8, 1.0), "WBC": (7.5, 1.8), "Platelets": (255, 40),
        "Glucose": (91, 10), "Total Cholesterol": (175, 22), "RBC": (4.7, 0.3),
        "Creatinine": (0.9, 0.15), "TSH": (2.0, 0.8), "HbA1c": (5.2, 0.3),
        "Vitamin D": (29, 8), "Vitamin B12": (420, 100), "IgE": (520, 200),
        "Homocysteine": (10, 2.5), "ALT": (22, 8), "AST": (24, 8),
        "LDL Cholesterol": (100, 20), "Triglycerides": (105, 30),
        "Ferritin": (72, 25), "CRP": (2.0, 1.0), "Uric Acid": (4.9, 0.9),
    },
    "Cardiovascular Risk": {
        "Hemoglobin": (13.8, 1.0), "WBC": (7.5, 1.5), "Platelets": (270, 50),
        "Glucose": (105, 15), "Total Cholesterol": (235, 30), "RBC": (4.8, 0.3),
        "Creatinine": (1.0, 0.2), "TSH": (2.1, 0.8), "HbA1c": (5.6, 0.4),
        "Vitamin D": (24, 7), "Vitamin B12": (280, 80), "IgE": (55, 28),
        "Homocysteine": (22, 6), "ALT": (28, 10), "AST": (30, 10),
        "LDL Cholesterol": (158, 30), "Triglycerides": (180, 55),
        "Ferritin": (95, 35), "CRP": (6.0, 3.0), "Uric Acid": (6.5, 1.5),
    },
    "Metabolic Syndrome": {
        "Hemoglobin": (13.5, 1.2), "WBC": (8.0, 2.0), "Platelets": (255, 45),
        "Glucose": (118, 20), "Total Cholesterol": (228, 28), "RBC": (4.7, 0.3),
        "Creatinine": (1.0, 0.2), "TSH": (2.2, 0.8), "HbA1c": (6.0, 0.6),
        "Vitamin D": (20, 7), "Vitamin B12": (360, 100), "IgE": (58, 30),
        "Homocysteine": (15, 4), "ALT": (38, 14), "AST": (36, 14),
        "LDL Cholesterol": (148, 28), "Triglycerides": (220, 60),
        "Ferritin": (110, 40), "CRP": (5.0, 2.5), "Uric Acid": (7.0, 1.5),
    },
    "Fatty Liver": {
        "Hemoglobin": (13.8, 1.2), "WBC": (7.8, 2.0), "Platelets": (235, 45),
        "Glucose": (108, 18), "Total Cholesterol": (218, 28), "RBC": (4.7, 0.3),
        "Creatinine": (0.95, 0.2), "TSH": (2.1, 0.8), "HbA1c": (5.7, 0.5),
        "Vitamin D": (22, 7), "Vitamin B12": (380, 100), "IgE": (52, 28),
        "Homocysteine": (14, 4), "ALT": (70, 30), "AST": (60, 25),
        "LDL Cholesterol": (135, 28), "Triglycerides": (190, 55),
        "Ferritin": (200, 80), "CRP": (4.5, 2.5), "Uric Acid": (6.0, 1.5),
    },
}

SAMPLES_PER_CLASS = 800


def _clip_values(row: dict) -> dict:
    row["Hemoglobin"]       = max(4.0,  min(22.0,  row["Hemoglobin"]))
    row["WBC"]              = max(1.0,  min(50.0,  row["WBC"]))
    row["Platelets"]        = max(20,   min(800,   row["Platelets"]))
    row["Glucose"]          = max(40,   min(500,   row["Glucose"]))
    row["Total Cholesterol"]= max(80,   min(450,   row["Total Cholesterol"]))
    row["RBC"]              = max(1.5,  min(7.0,   row["RBC"]))
    row["Creatinine"]       = max(0.3,  min(12.0,  row["Creatinine"]))
    row["TSH"]              = max(0.01, min(30.0,  row["TSH"]))
    row["HbA1c"]            = max(3.5,  min(15.0,  row["HbA1c"]))
    row["Vitamin D"]        = max(2.0,  min(100,   row["Vitamin D"]))
    row["Vitamin B12"]      = max(50,   min(2000,  row["Vitamin B12"]))
    row["IgE"]              = max(0,    min(3000,  row["IgE"]))
    row["Homocysteine"]     = max(3.0,  min(50.0,  row["Homocysteine"]))
    row["ALT"]              = max(5,    min(500,   row["ALT"]))
    row["AST"]              = max(5,    min(500,   row["AST"]))
    row["LDL Cholesterol"]  = max(30,   min(350,   row["LDL Cholesterol"]))
    row["Triglycerides"]    = max(30,   min(800,   row["Triglycerides"]))
    row["Ferritin"]         = max(1.0,  min(800,   row["Ferritin"]))
    row["CRP"]              = max(0.1,  min(200,   row["CRP"]))
    row["Uric Acid"]        = max(1.0,  min(15.0,  row["Uric Acid"]))
    return row


def generate_dataset() -> pd.DataFrame:
    records = []
    for disease, profile in DISEASE_PROFILES.items():
        for _ in range(SAMPLES_PER_CLASS):
            row: dict = {}
            for feat in FEATURES:
                mean, std = profile[feat]
                row[feat] = float(RNG.normal(mean, std))
            row = _clip_values(row)
            row["Disease"] = disease
            records.append(row)

    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    logger.info("Generating synthetic blood test dataset (v2 — 20 features, 15 diseases)...")
    df = generate_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved {len(df)} records to {OUTPUT_PATH}")
    logger.info(f"Class distribution:\n{df['Disease'].value_counts()}")
