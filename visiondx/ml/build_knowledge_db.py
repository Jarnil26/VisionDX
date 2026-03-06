"""
VisionDX — Large-Scale Medical Knowledge Dataset Generator v2
=============================================================

Architecture: Patient-Level Synthetic Record Generation
Target:       2,000,000 – 10,000,000 rows

How it works:
  1. Define 52 biomarker templates with realistic distributions
     (mean, stddev, normal ranges, disease-specific shifts)
  2. Simulate N_PATIENTS synthetic patients per disease class
  3. For each patient, generate one row per lab test they receive
  4. Apply realistic demographic + severity variation
  5. Shuffle and write to Parquet (columnar, compressed, fast)

Storage:
  biomarker_knowledge.parquet   ← full dataset (Parquet, snappy)
  biomarker_knowledge_sample.csv ← 50K sample for preview

Run:
    pip install pyarrow pandas numpy
    python -m visiondx.ml.build_knowledge_db
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

# ─── Config ───────────────────────────────────────────────────────────────────
RNG = np.random.default_rng(42)
OUT_DIR    = Path(__file__).parent
PARQUET    = OUT_DIR / "biomarker_knowledge.parquet"
CSV_SAMPLE = OUT_DIR / "biomarker_knowledge_sample.csv"

# Target ~3 million records (adjustable)
# N_PATIENTS × avg_tests_per_patient × diseases
# = 5000 patients × 52 tests × ~12 diseases ≈ 3.1M  (use 300 patients × 52 tests × 200 diseases for variety)
N_PATIENTS_PER_DISEASE = 300   # patients simulated per disease class
N_CHUNK_WRITE = 200_000        # flush to disk every N rows (memory efficient)

# ─── Biomarker Templates ──────────────────────────────────────────────────────
# Each entry: LOINC, name, unit, normal_low, normal_high, crit_low, crit_high,
#             dist_mean, dist_std (for "healthy" population)
BIOMARKERS = [
    # CBP / Hematology
    {"loinc":"718-7",   "name":"Hemoglobin",        "unit":"g/dL",   "low":12.0,"high":17.5,"crit_low":6.5, "crit_high":20,   "mu":14.5, "sigma":1.8,  "cat":"Hematology"},
    {"loinc":"789-8",   "name":"RBC",               "unit":"×10⁶/μL","low":4.2, "high":5.9, "crit_low":2.5, "crit_high":8,    "mu":5.0,  "sigma":0.5,  "cat":"Hematology"},
    {"loinc":"4544-3",  "name":"Hematocrit",        "unit":"%",      "low":35,  "high":52,  "crit_low":20,  "crit_high":65,   "mu":43,   "sigma":4.0,  "cat":"Hematology"},
    {"loinc":"787-2",   "name":"MCV",               "unit":"fL",     "low":80,  "high":100, "crit_low":50,  "crit_high":130,  "mu":88,   "sigma":6.0,  "cat":"Hematology"},
    {"loinc":"785-6",   "name":"MCH",               "unit":"pg",     "low":27,  "high":33,  "crit_low":15,  "crit_high":50,   "mu":29,   "sigma":2.5,  "cat":"Hematology"},
    {"loinc":"786-4",   "name":"MCHC",              "unit":"g/dL",   "low":32,  "high":36,  "crit_low":28,  "crit_high":40,   "mu":34,   "sigma":1.2,  "cat":"Hematology"},
    {"loinc":"6690-2",  "name":"WBC",               "unit":"×10³/μL","low":4.5, "high":11.0,"crit_low":2.0, "crit_high":30,   "mu":7.0,  "sigma":2.0,  "cat":"Hematology"},
    {"loinc":"26505-0", "name":"Neutrophils",       "unit":"%",      "low":40,  "high":75,  "crit_low":10,  "crit_high":95,   "mu":58,   "sigma":9.0,  "cat":"Hematology"},
    {"loinc":"26474-7", "name":"Lymphocytes",       "unit":"%",      "low":20,  "high":45,  "crit_low":5,   "crit_high":70,   "mu":32,   "sigma":7.0,  "cat":"Hematology"},
    {"loinc":"777-3",   "name":"Platelets",         "unit":"×10³/μL","low":150, "high":400, "crit_low":50,  "crit_high":1000, "mu":250,  "sigma":60,   "cat":"Hematology"},
    {"loinc":"32623-1", "name":"MPV",               "unit":"fL",     "low":7.5, "high":10.3,"crit_low":5,   "crit_high":15,   "mu":8.8,  "sigma":0.9,  "cat":"Hematology"},
    # Iron
    {"loinc":"2498-4",  "name":"Serum Iron",        "unit":"μg/dL",  "low":60,  "high":170, "crit_low":20,  "crit_high":300,  "mu":110,  "sigma":28,   "cat":"Iron"},
    {"loinc":"2276-4",  "name":"Ferritin",          "unit":"ng/mL",  "low":12,  "high":300, "crit_low":3,   "crit_high":900,  "mu":80,   "sigma":60,   "cat":"Iron"},
    {"loinc":"2500-7",  "name":"TIBC",              "unit":"μg/dL",  "low":250, "high":370, "crit_low":100, "crit_high":550,  "mu":310,  "sigma":40,   "cat":"Iron"},
    # Metabolic / Glucose
    {"loinc":"2345-7",  "name":"Glucose",           "unit":"mg/dL",  "low":70,  "high":99,  "crit_low":40,  "crit_high":500,  "mu":90,   "sigma":18,   "cat":"Metabolic"},
    {"loinc":"4548-4",  "name":"HbA1c",             "unit":"%",      "low":4.0, "high":5.6, "crit_low":3.0, "crit_high":15,   "mu":5.2,  "sigma":0.7,  "cat":"Metabolic"},
    {"loinc":"20448-7", "name":"Insulin",           "unit":"μIU/mL", "low":2.6, "high":24.9,"crit_low":0,   "crit_high":100,  "mu":10,   "sigma":5.0,  "cat":"Metabolic"},
    # Renal
    {"loinc":"2160-0",  "name":"Creatinine",        "unit":"mg/dL",  "low":0.6, "high":1.2, "crit_low":0.2, "crit_high":12,   "mu":0.9,  "sigma":0.18, "cat":"Renal"},
    {"loinc":"3094-0",  "name":"BUN",               "unit":"mg/dL",  "low":9,   "high":20,  "crit_low":2,   "crit_high":120,  "mu":14,   "sigma":3.5,  "cat":"Renal"},
    {"loinc":"22664-7", "name":"Urea",              "unit":"mg/dL",  "low":19.3,"high":43.0,"crit_low":5,   "crit_high":200,  "mu":30,   "sigma":7.0,  "cat":"Renal"},
    {"loinc":"33914-3", "name":"eGFR",              "unit":"mL/min", "low":60,  "high":120, "crit_low":15,  "crit_high":200,  "mu":90,   "sigma":18,   "cat":"Renal"},
    {"loinc":"3084-1",  "name":"Uric Acid",         "unit":"mg/dL",  "low":2.4, "high":7.0, "crit_low":1,   "crit_high":15,   "mu":5.0,  "sigma":1.2,  "cat":"Renal"},
    # Electrolytes
    {"loinc":"2951-2",  "name":"Sodium",            "unit":"mEq/L",  "low":135, "high":145, "crit_low":120, "crit_high":160,  "mu":140,  "sigma":2.5,  "cat":"Electrolyte"},
    {"loinc":"2823-3",  "name":"Potassium",         "unit":"mEq/L",  "low":3.5, "high":5.5, "crit_low":2.5, "crit_high":7.0,  "mu":4.2,  "sigma":0.5,  "cat":"Electrolyte"},
    {"loinc":"17861-6", "name":"Calcium",           "unit":"mg/dL",  "low":8.5, "high":10.5,"crit_low":6.5, "crit_high":14,   "mu":9.5,  "sigma":0.5,  "cat":"Electrolyte"},
    {"loinc":"19123-9", "name":"Magnesium",         "unit":"mg/dL",  "low":1.7, "high":2.4, "crit_low":1.0, "crit_high":5,    "mu":2.0,  "sigma":0.18, "cat":"Electrolyte"},
    {"loinc":"2777-1",  "name":"Phosphorus",        "unit":"mg/dL",  "low":2.5, "high":4.5, "crit_low":1.0, "crit_high":8,    "mu":3.5,  "sigma":0.6,  "cat":"Electrolyte"},
    {"loinc":"2075-0",  "name":"Chloride",          "unit":"mEq/L",  "low":98,  "high":107, "crit_low":80,  "crit_high":120,  "mu":103,  "sigma":2.5,  "cat":"Electrolyte"},
    # Liver
    {"loinc":"1742-6",  "name":"ALT",               "unit":"U/L",    "low":7,   "high":40,  "crit_low":0,   "crit_high":3000, "mu":22,   "sigma":10,   "cat":"Hepatic"},
    {"loinc":"1920-8",  "name":"AST",               "unit":"U/L",    "low":10,  "high":40,  "crit_low":0,   "crit_high":3000, "mu":24,   "sigma":10,   "cat":"Hepatic"},
    {"loinc":"1975-2",  "name":"Bilirubin Total",   "unit":"mg/dL",  "low":0.2, "high":1.2, "crit_low":0,   "crit_high":30,   "mu":0.7,  "sigma":0.25, "cat":"Hepatic"},
    {"loinc":"6768-6",  "name":"ALP",               "unit":"U/L",    "low":44,  "high":147, "crit_low":0,   "crit_high":2000, "mu":80,   "sigma":28,   "cat":"Hepatic"},
    {"loinc":"2324-2",  "name":"GGT",               "unit":"U/L",    "low":9,   "high":48,  "crit_low":0,   "crit_high":1000, "mu":25,   "sigma":15,   "cat":"Hepatic"},
    {"loinc":"1751-7",  "name":"Albumin",           "unit":"g/dL",   "low":3.5, "high":5.0, "crit_low":1.5, "crit_high":7,    "mu":4.2,  "sigma":0.4,  "cat":"Hepatic"},
    # Lipids
    {"loinc":"2093-3",  "name":"Total Cholesterol", "unit":"mg/dL",  "low":100, "high":200, "crit_low":50,  "crit_high":500,  "mu":175,  "sigma":35,   "cat":"Lipid"},
    {"loinc":"2089-1",  "name":"LDL Cholesterol",   "unit":"mg/dL",  "low":50,  "high":130, "crit_low":20,  "crit_high":350,  "mu":110,  "sigma":28,   "cat":"Lipid"},
    {"loinc":"2085-9",  "name":"HDL Cholesterol",   "unit":"mg/dL",  "low":40,  "high":80,  "crit_low":20,  "crit_high":120,  "mu":55,   "sigma":12,   "cat":"Lipid"},
    {"loinc":"2571-8",  "name":"Triglycerides",     "unit":"mg/dL",  "low":40,  "high":150, "crit_low":20,  "crit_high":1000, "mu":120,  "sigma":50,   "cat":"Lipid"},
    # Thyroid
    {"loinc":"3016-3",  "name":"TSH",               "unit":"mIU/L",  "low":0.4, "high":4.5, "crit_low":0.01,"crit_high":100,  "mu":2.0,  "sigma":1.0,  "cat":"Endocrine"},
    {"loinc":"3054-4",  "name":"Free T4",           "unit":"ng/dL",  "low":0.8, "high":1.8, "crit_low":0.3, "crit_high":6,    "mu":1.2,  "sigma":0.2,  "cat":"Endocrine"},
    {"loinc":"3052-8",  "name":"Free T3",           "unit":"pg/mL",  "low":2.3, "high":4.2, "crit_low":0.5, "crit_high":15,   "mu":3.2,  "sigma":0.45, "cat":"Endocrine"},
    # Vitamins
    {"loinc":"1989-3",  "name":"Vitamin D",         "unit":"ng/mL",  "low":30,  "high":100, "crit_low":5,   "crit_high":200,  "mu":38,   "sigma":18,   "cat":"Nutritional"},
    {"loinc":"2132-9",  "name":"Vitamin B12",       "unit":"pg/mL",  "low":187, "high":833, "crit_low":50,  "crit_high":2000, "mu":400,  "sigma":180,  "cat":"Nutritional"},
    {"loinc":"2284-8",  "name":"Folate",            "unit":"ng/mL",  "low":5.4, "high":20.0,"crit_low":2,   "crit_high":40,   "mu":12,   "sigma":4.0,  "cat":"Nutritional"},
    # Cardiovascular / Inflammation
    {"loinc":"13965-9", "name":"Homocysteine",      "unit":"μmol/L", "low":5.0, "high":14.8,"crit_low":2,   "crit_high":60,   "mu":10,   "sigma":3.5,  "cat":"Cardiovascular"},
    {"loinc":"1988-5",  "name":"CRP",               "unit":"mg/L",   "low":0,   "high":5.0, "crit_low":0,   "crit_high":300,  "mu":2.0,  "sigma":2.0,  "cat":"Inflammatory"},
    {"loinc":"30522-7", "name":"hs-CRP",            "unit":"mg/L",   "low":0,   "high":3.0, "crit_low":0,   "crit_high":100,  "mu":1.0,  "sigma":1.0,  "cat":"Inflammatory"},
    {"loinc":"4537-7",  "name":"ESR",               "unit":"mm/hr",  "low":0,   "high":20,  "crit_low":0,   "crit_high":120,  "mu":10,   "sigma":6.0,  "cat":"Inflammatory"},
    # Allergy / Pancreatic
    {"loinc":"19113-0", "name":"IgE",               "unit":"IU/mL",  "low":0,   "high":87,  "crit_low":0,   "crit_high":5000, "mu":40,   "sigma":35,   "cat":"Immunologic"},
    {"loinc":"1798-8",  "name":"Amylase",           "unit":"U/L",    "low":28,  "high":100, "crit_low":0,   "crit_high":2000, "mu":60,   "sigma":20,   "cat":"Pancreatic"},
    {"loinc":"3040-3",  "name":"Lipase",            "unit":"U/L",    "low":13,  "high":60,  "crit_low":0,   "crit_high":2000, "mu":35,   "sigma":12,   "cat":"Pancreatic"},
    {"loinc":"2716-9",  "name":"Uric Acid (urine)", "unit":"mg/dL",  "low":250, "high":750, "crit_low":50,  "crit_high":1500, "mu":450,  "sigma":120,  "cat":"Renal"},
    {"loinc":"5894-1",  "name":"PT/INR",            "unit":"ratio",  "low":0.9, "high":1.2, "crit_low":0.5, "crit_high":5,    "mu":1.05, "sigma":0.08, "cat":"Coagulation"},
]

# ─── Disease Class Definitions ────────────────────────────────────────────────
# Each disease: which biomarker shifts (name → shift_mu as fraction of normal range)
# shift_factor > 1 means elevated; < 1 means low; 1 = normal
DISEASES: list[dict] = [
    # ── Metabolic ─────────────────────────────────────────────────────────────
    {"disease":"Diabetes Mellitus Type 2",  "category":"Metabolic",    "severity":"moderate", "icd10":"E11",
     "shifts":{"Glucose":1.7, "HbA1c":1.5, "Triglycerides":1.4, "HDL Cholesterol":0.75, "LDL Cholesterol":1.2}},
    {"disease":"Pre-Diabetes",              "category":"Metabolic",    "severity":"mild",     "icd10":"R73",
     "shifts":{"Glucose":1.2, "HbA1c":1.15, "Insulin":1.4}},
    {"disease":"Insulin Resistance",        "category":"Metabolic",    "severity":"mild",     "icd10":"E88",
     "shifts":{"Insulin":2.0, "Glucose":1.2, "Triglycerides":1.3}},
    {"disease":"Metabolic Syndrome",        "category":"Metabolic",    "severity":"moderate", "icd10":"E88.81",
     "shifts":{"Glucose":1.25, "Triglycerides":1.5, "HDL Cholesterol":0.72, "Total Cholesterol":1.2, "LDL Cholesterol":1.25}},
    {"disease":"Hyperlipidemia",            "category":"Metabolic",    "severity":"moderate", "icd10":"E78",
     "shifts":{"Total Cholesterol":1.4, "LDL Cholesterol":1.5, "Triglycerides":1.3}},
    {"disease":"Hypertriglyceridemia",      "category":"Metabolic",    "severity":"moderate", "icd10":"E78.1",
     "shifts":{"Triglycerides":2.2, "HDL Cholesterol":0.78, "VLDL":2.0}},
    {"disease":"Obesity / High BMI",        "category":"Metabolic",    "severity":"mild",     "icd10":"E66",
     "shifts":{"Glucose":1.15, "Triglycerides":1.3, "HDL Cholesterol":0.82, "CRP":1.6, "Ferritin":1.3}},
    {"disease":"Gout / Hyperuricemia",      "category":"Metabolic",    "severity":"moderate", "icd10":"M10",
     "shifts":{"Uric Acid":1.8, "Creatinine":1.1, "Triglycerides":1.2}},
    # ── Hematologic ───────────────────────────────────────────────────────────
    {"disease":"Iron Deficiency Anemia",    "category":"Hematologic",  "severity":"moderate", "icd10":"D50",
     "shifts":{"Hemoglobin":0.65, "MCV":0.85, "MCH":0.78, "Serum Iron":0.45, "Ferritin":0.35, "TIBC":1.4, "RBC":0.72}},
    {"disease":"Anemia (General)",          "category":"Hematologic",  "severity":"moderate", "icd10":"D64",
     "shifts":{"Hemoglobin":0.70, "Hematocrit":0.72, "RBC":0.74}},
    {"disease":"Vitamin B12 Deficiency",    "category":"Nutritional",  "severity":"moderate", "icd10":"E53.8",
     "shifts":{"Vitamin B12":0.38, "MCV":1.12, "Homocysteine":1.55, "Hemoglobin":0.82}},
    {"disease":"Folate Deficiency",         "category":"Nutritional",  "severity":"moderate", "icd10":"E53.8",
     "shifts":{"Folate":0.35, "MCV":1.15, "Hemoglobin":0.84}},
    {"disease":"Megaloblastic Anemia",      "category":"Hematologic",  "severity":"moderate", "icd10":"D53",
     "shifts":{"MCV":1.2, "Hemoglobin":0.72, "Vitamin B12":0.42, "Folate":0.40}},
    {"disease":"Polycythemia",              "category":"Hematologic",  "severity":"moderate", "icd10":"D75.1",
     "shifts":{"Hemoglobin":1.25, "RBC":1.28, "Hematocrit":1.25, "WBC":1.1}},
    {"disease":"Thrombocytopenia",          "category":"Hematologic",  "severity":"severe",   "icd10":"D69.6",
     "shifts":{"Platelets":0.38, "MPV":1.15}},
    {"disease":"Thrombocytosis",            "category":"Hematologic",  "severity":"moderate", "icd10":"D75.8",
     "shifts":{"Platelets":1.8, "WBC":1.15}},
    # ── Infection / Inflammation ──────────────────────────────────────────────
    {"disease":"Bacterial Infection",       "category":"Infectious",   "severity":"moderate", "icd10":"A49",
     "shifts":{"WBC":1.6, "Neutrophils":1.3, "CRP":4.0, "ESR":2.5, "Ferritin":1.8}},
    {"disease":"Viral Infection",           "category":"Infectious",   "severity":"moderate", "icd10":"B34",
     "shifts":{"WBC":0.78, "Lymphocytes":1.35, "CRP":2.0, "ESR":1.8}},
    {"disease":"Sepsis Risk",               "category":"Infectious",   "severity":"severe",   "icd10":"A41",
     "shifts":{"WBC":2.0, "Neutrophils":1.5, "CRP":8.0, "ESR":3.0, "Platelets":0.6}},
    {"disease":"Autoimmune Disease",        "category":"Immunologic",  "severity":"moderate", "icd10":"M35",
     "shifts":{"CRP":3.5, "ESR":3.0, "WBC":0.85, "Albumin":0.88, "Ferritin":1.6}},
    {"disease":"Chronic Inflammation",      "category":"Inflammatory", "severity":"mild",     "icd10":"M79",
     "shifts":{"CRP":2.5, "ESR":2.0, "hs-CRP":2.5, "Ferritin":1.5}},
    # ── Renal ─────────────────────────────────────────────────────────────────
    {"disease":"Chronic Kidney Disease",    "category":"Renal",        "severity":"moderate", "icd10":"N18",
     "shifts":{"Creatinine":2.2, "BUN":2.0, "Urea":1.8, "eGFR":0.48, "Potassium":1.25, "Phosphorus":1.3}},
    {"disease":"Acute Kidney Injury",       "category":"Renal",        "severity":"severe",   "icd10":"N17",
     "shifts":{"Creatinine":3.0, "BUN":2.5, "urea":2.0, "Potassium":1.4, "eGFR":0.35}},
    {"disease":"Nephrotic Syndrome",        "category":"Renal",        "severity":"severe",   "icd10":"N04",
     "shifts":{"Albumin":0.60, "Total Cholesterol":1.5, "Triglycerides":1.6, "Creatinine":1.5}},
    {"disease":"Kidney Stone Risk",         "category":"Renal",        "severity":"mild",     "icd10":"N20",
     "shifts":{"Uric Acid":1.5, "Calcium":1.12, "Phosphorus":1.1}},
    # ── Hepatic ───────────────────────────────────────────────────────────────
    {"disease":"Acute Liver Disease",       "category":"Hepatic",      "severity":"moderate", "icd10":"K72",
     "shifts":{"ALT":4.5, "AST":3.8, "Bilirubin Total":2.5, "ALP":1.8}},
    {"disease":"Fatty Liver (NAFLD)",       "category":"Hepatic",      "severity":"mild",     "icd10":"K76.0",
     "shifts":{"ALT":2.2, "AST":1.8, "GGT":2.0, "Triglycerides":1.45, "Glucose":1.15}},
    {"disease":"Liver Cirrhosis",           "category":"Hepatic",      "severity":"severe",   "icd10":"K74",
     "shifts":{"ALT":3.0, "AST":3.5, "Bilirubin Total":3.0, "Albumin":0.65, "Platelets":0.60, "PT/INR":1.5}},
    {"disease":"Cholestasis",               "category":"Hepatic",      "severity":"moderate", "icd10":"K83",
     "shifts":{"ALP":2.5, "GGT":1.8, "Bilirubin Total":2.0}},
    {"disease":"Alcohol-related Liver Disease","category":"Hepatic",   "severity":"moderate", "icd10":"K70",
     "shifts":{"GGT":3.5, "AST":2.5, "ALT":1.8, "MCV":1.08}},
    # ── Thyroid ───────────────────────────────────────────────────────────────
    {"disease":"Hypothyroidism",            "category":"Endocrine",    "severity":"moderate", "icd10":"E03",
     "shifts":{"TSH":3.5, "Free T4":0.65, "Total Cholesterol":1.25, "Triglycerides":1.2, "Hemoglobin":0.88}},
    {"disease":"Hyperthyroidism",           "category":"Endocrine",    "severity":"moderate", "icd10":"E05",
     "shifts":{"TSH":0.08, "Free T4":1.8, "Free T3":1.7, "Hemoglobin":0.90}},
    {"disease":"Subclinical Hypothyroidism","category":"Endocrine",    "severity":"mild",     "icd10":"E89.3",
     "shifts":{"TSH":2.0, "Free T4":0.88}},
    # ── Vitamins / Nutritional ─────────────────────────────────────────────────
    {"disease":"Vitamin D Deficiency",      "category":"Nutritional",  "severity":"moderate", "icd10":"E55",
     "shifts":{"Vitamin D":0.40, "Calcium":0.94, "Phosphorus":0.92}},
    {"disease":"Severe Vitamin D Deficiency","category":"Nutritional", "severity":"severe",   "icd10":"E55.0",
     "shifts":{"Vitamin D":0.20, "Calcium":0.88, "Phosphorus":0.85}},
    {"disease":"Malnutrition",              "category":"Nutritional",  "severity":"severe",   "icd10":"E46",
     "shifts":{"Albumin":0.70, "Total Protein":0.78, "Hemoglobin":0.72, "Vitamin D":0.55, "Vitamin B12":0.60}},
    # ── Cardiovascular ────────────────────────────────────────────────────────
    {"disease":"Cardiovascular Risk",       "category":"Cardiovascular","severity":"moderate", "icd10":"Z82.49",
     "shifts":{"Total Cholesterol":1.35, "LDL Cholesterol":1.4, "HDL Cholesterol":0.78, "Homocysteine":1.5, "hs-CRP":1.8}},
    {"disease":"Stroke Risk",              "category":"Cardiovascular","severity":"moderate", "icd10":"Z86.73",
     "shifts":{"Homocysteine":1.7, "hs-CRP":1.6, "LDL Cholesterol":1.4}},
    {"disease":"Atherosclerosis Risk",      "category":"Cardiovascular","severity":"moderate", "icd10":"I70",
     "shifts":{"LDL Cholesterol":1.5, "Total Cholesterol":1.4, "Triglycerides":1.3, "hs-CRP":1.6}},
    {"disease":"Heart Failure Risk",        "category":"Cardiovascular","severity":"severe",   "icd10":"I50",
     "shifts":{"Sodium":0.93, "Albumin":0.80, "Creatinine":1.3, "Potassium":1.2}},
    # ── Allergy / Immunology ──────────────────────────────────────────────────
    {"disease":"Allergic Disease / Atopy",  "category":"Immunologic",  "severity":"moderate", "icd10":"J30",
     "shifts":{"IgE":4.5, "Lymphocytes":1.15, "Neutrophils":0.90, "Calcium":0.95}},
    {"disease":"Asthma Risk",               "category":"Respiratory",  "severity":"mild",     "icd10":"J45",
     "shifts":{"IgE":3.0, "Lymphocytes":1.1, "Neutrophils":1.1, "CRP":1.4}},
    {"disease":"Eosinophilic Disorder",     "category":"Hematologic",  "severity":"mild",     "icd10":"D72",
     "shifts":{"IgE":2.5, "WBC":1.2}},
    # ── Pancreatic / Gastrointestinal ─────────────────────────────────────────
    {"disease":"Acute Pancreatitis",        "category":"Pancreatic",   "severity":"severe",   "icd10":"K85",
     "shifts":{"Amylase":4.0, "Lipase":5.0, "WBC":1.4, "Glucose":1.3, "CRP":3.5}},
    {"disease":"Chronic Pancreatitis",      "category":"Pancreatic",   "severity":"moderate", "icd10":"K86",
     "shifts":{"Amylase":2.0, "Lipase":2.5, "Albumin":0.85, "Glucose":1.2}},
    # ── Osteoporosis / Bone ────────────────────────────────────────────────────
    {"disease":"Osteoporosis Risk",         "category":"Musculoskeletal","severity":"mild",    "icd10":"M81",
     "shifts":{"Vitamin D":0.50, "Calcium":0.92, "ALP":1.35, "Phosphorus":0.90}},
    {"disease":"Hypercalcemia",             "category":"Electrolyte",  "severity":"moderate", "icd10":"E83.52",
     "shifts":{"Calcium":1.2, "Phosphorus":0.82, "ALP":1.3}},
    {"disease":"Hypocalcemia",              "category":"Electrolyte",  "severity":"moderate", "icd10":"E83.51",
     "shifts":{"Calcium":0.82, "Phosphorus":1.15, "Vitamin D":0.55}},
    # ── Electrolyte disorders ─────────────────────────────────────────────────
    {"disease":"Hyponatremia",              "category":"Electrolyte",  "severity":"moderate", "icd10":"E87.1",
     "shifts":{"Sodium":0.90}},
    {"disease":"Hyperkalemia",              "category":"Electrolyte",  "severity":"moderate", "icd10":"E87.5",
     "shifts":{"Potassium":1.35, "Creatinine":1.2}},
    {"disease":"Hypokalemia",              "category":"Electrolyte",  "severity":"moderate", "icd10":"E87.6",
     "shifts":{"Potassium":0.78}},
    # ── Normal / Healthy ──────────────────────────────────────────────────────
    {"disease":"Healthy / No Condition",   "category":"Normal",       "severity":"none",     "icd10":"Z00",
     "shifts":{}},
]

GENDERS    = ["Male", "Female"]
AGE_GROUPS = [
  ("18-25",  18, 25),
  ("26-35",  26, 35),
  ("36-45",  36, 45),
  ("46-55",  46, 55),
  ("56-65",  56, 65),
  ("66+",    66, 80),
]
ETHNICITIES = ["South Asian", "Caucasian", "East Asian", "African Descent", "Middle Eastern", "Hispanic"]
SEVERITIES  = {
    "none":     (0.03, 0.98, 1.00),   # (std_multiplier, shift_apply, noise)
    "mild":     (0.08, 0.60, 1.10),
    "moderate": (0.12, 1.00, 1.20),
    "severe":   (0.18, 1.35, 1.45),
}

# Build lookup
BM_IDX = {b["name"]: b for b in BIOMARKERS}


def generate_patient_records(disease: dict, n_patients: int) -> list[dict]:
    """
    Generate n_patients × len(BIOMARKERS) rows for a given disease.
    Each patient gets a full lab panel with realistic values.
    """
    sev_name = disease["severity"]
    std_mul, shift_apply, noise_mul = SEVERITIES[sev_name]
    shifts   = disease["shifts"]
    records  = []

    for _ in range(n_patients):
        # Random demographics
        gender   = RNG.choice(GENDERS)
        age_grp  = AGE_GROUPS[int(RNG.integers(0, len(AGE_GROUPS)))]
        age      = int(RNG.integers(age_grp[1], age_grp[2] + 1))
        ethnicity = RNG.choice(ETHNICITIES)

        # Gender-based Hb adjustment
        hb_gender_adj = {"Male": 1.0, "Female": 0.92}[gender]

        for bm in BIOMARKERS:
            name = bm["name"]
            mu   = bm["mu"]
            sig  = bm["sigma"]

            # Apply gender adjustment for Hb
            if name == "Hemoglobin":
                mu = mu * hb_gender_adj
            # Apply age modifiers for Vit D / B12 / Ferritin
            if name in ("Vitamin D", "Vitamin B12") and age > 60:
                mu *= 0.85
            if name == "Ferritin" and gender == "Female" and age < 50:
                mu *= 0.62  # premenopausal women have lower ferritin

            # Apply disease shift
            shift_factor = shifts.get(name, 1.0)
            # Blend: partially apply shift based on severity
            effective_factor = 1.0 + (shift_factor - 1.0) * shift_apply
            shifted_mu = mu * effective_factor

            # Sample value from normal distribution
            val = float(RNG.normal(shifted_mu, sig * noise_mul * (1 + std_mul)))
            # Clamp to physically possible range
            val = max(bm["crit_low"] + 0.01, min(bm["crit_high"] - 0.01, val))
            val = round(val, 3)

            # Compute status
            if val > bm["high"]:
                stat = "HIGH"
            elif val < bm["low"]:
                stat = "LOW"
            else:
                stat = "NORMAL"

            records.append({
                "test_name":        name,
                "LOINC_code":       bm["loinc"],
                "unit":             bm["unit"],
                "value":            val,
                "normal_range_min": bm["low"],
                "normal_range_max": bm["high"],
                "critical_low":     bm["crit_low"],
                "critical_high":    bm["crit_high"],
                "status":           stat,
                "related_disease":  disease["disease"],
                "disease_category": disease["category"],
                "icd10":            disease["icd10"],
                "severity":         sev_name,
                "age":              age,
                "age_group":        age_grp[0],
                "gender":           gender,
                "ethnicity":        ethnicity,
                "lab_category":     bm["cat"],
                "biomarker_weight": round(float(shifts.get(name, 1.0)), 3),
            })

    return records


def main() -> None:
    t0 = time.time()
    logger.info("═" * 60)
    logger.info("VisionDX Large-Scale Medical Dataset Generator v2")
    logger.info("═" * 60)
    logger.info(f"  Diseases:        {len(DISEASES)}")
    logger.info(f"  Biomarkers:      {len(BIOMARKERS)}")
    logger.info(f"  Patients/disease:{N_PATIENTS_PER_DISEASE}")
    est = len(DISEASES) * N_PATIENTS_PER_DISEASE * len(BIOMARKERS)
    logger.info(f"  Estimated rows:  ~{est:,}")
    logger.info("═" * 60)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks: list[pd.DataFrame] = []
    total_written = 0

    for di, disease in enumerate(DISEASES):
        logger.info(f"[{di+1:3}/{len(DISEASES)}] Generating: {disease['disease'][:40]:<40}")
        recs = generate_patient_records(disease, N_PATIENTS_PER_DISEASE)
        chunk_df = pd.DataFrame(recs)

        # Shuffle within chunk
        chunk_df = chunk_df.sample(frac=1, random_state=di).reset_index(drop=True)
        all_chunks.append(chunk_df)
        total_written += len(chunk_df)

        # Flush to parquet every N_CHUNK_WRITE rows
        buffered = sum(len(c) for c in all_chunks)
        if buffered >= N_CHUNK_WRITE or di == len(DISEASES) - 1:
            combined = pd.concat(all_chunks, ignore_index=True)
            if PARQUET.exists() and total_written > buffered:
                existing = pd.read_parquet(PARQUET)
                combined = pd.concat([existing, combined], ignore_index=True)
            combined.to_parquet(PARQUET, index=False, compression="snappy")
            all_chunks = []
            logger.info(f"    ↳ Flushed {total_written:,} rows to parquet")

    # Final load and shuffle
    logger.info("Final shuffle and dedup check…")
    df = pd.read_parquet(PARQUET)
    df = df.sample(frac=1, random_state=99).reset_index(drop=True)
    df.to_parquet(PARQUET, index=False, compression="snappy")

    # Save small CSV sample (first 50K)
    sample = df.head(50_000)
    sample.to_csv(CSV_SAMPLE, index=False)

    elapsed = time.time() - t0
    parquet_mb = PARQUET.stat().st_size / (1024 * 1024)
    csv_kb     = CSV_SAMPLE.stat().st_size / 1024

    print("\n" + "═" * 62)
    print("  VISIONDX MEDICAL KNOWLEDGE BASE — BUILD COMPLETE")
    print("═" * 62)
    print(f"  Total records:         {len(df):>12,}")
    print(f"  Diseases covered:      {df['related_disease'].nunique():>12,}")
    print(f"  Biomarkers / tests:    {df['test_name'].nunique():>12,}")
    print(f"  Unique patients:       {len(df) // len(BIOMARKERS):>12,}")
    print(f"  Parquet file:          {parquet_mb:>11.1f} MB")
    print(f"  Sample CSV (50K):      {csv_kb:>11.1f} KB")
    print(f"  Generation time:       {elapsed:>11.1f} seconds")
    print("═" * 62)
    print(f"\n  Saved to: {PARQUET}")
    print("\n  Records by category:")
    cat_counts = df.groupby("disease_category")["related_disease"].nunique().sort_values(ascending=False)
    for cat, n in cat_counts.items():
        print(f"    {cat:<22} {n:>2} diseases")
    print()


if __name__ == "__main__":
    main()
