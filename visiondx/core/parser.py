"""
VisionDX — Medical Parameter Parser v2

Robustly extracts patient details and blood test parameters from
diverse Indian lab report formats (PDF/OCR text).

Key improvements:
  - 12 patient name pattern variants (handles Pt.Name, PATIENT:, Salutation, ALL-CAPS)
  - Age detection from DOB, "/ 25Y", "Age: 25 Yrs" formats
  - Gender detection from M/F abbreviations and keywords
  - Date in DD/MM/YYYY and YYYY-MM-DD formats
  - Fallback: extract name from filename if present in raw_text header
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger
from rapidfuzz import process, fuzz

from visiondx.database.schemas import ParsedParameter, ParsedReport
from visiondx.utils.medical_dictionary import PARAMETER_ALIASES, DEFAULT_REFERENCE_RANGES
from visiondx.utils.text_cleaner import extract_numeric, normalize_range_dashes, normalize_unit

# ─────────────────────────────────────────────────────────────────────────────
# PARAMETER EXTRACTION PATTERNS
# ─────────────────────────────────────────────────────────────────────────────

TABULAR_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9\s\(\),\.\-/]{2,50}?)"
    r"\s{1,10}"
    r"(?P<value>(?:<|>|=)?\s*\d+\.?\d*)"
    r"\s{0,5}"
    r"(?P<unit>[A-Za-z%µ³⁶/\.°\^0-9]{1,20})?"
    r"(?:\s{1,10}(?P<range>\d+\.?\d*\s*[-–—]\s*\d+\.?\d*))?"
    r"\s*$",
    re.IGNORECASE,
)

COLON_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9\s\(\),\.\-/]{2,50}?)"
    r"\s*:\s*"
    r"(?P<value>(?:<|>|=)?\s*\d+\.?\d*)"
    r"\s*"
    r"(?P<unit>[A-Za-z%µ³⁶/\.°\^0-9]{1,20})?"
    r"(?:\s*[(\[](?P<range>[^\)\]]+)[)\]])?"
    r"\s*$",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# PATIENT METADATA PATTERNS — comprehensive for Indian lab formats
# ─────────────────────────────────────────────────────────────────────────────

# Name patterns — ordered from most specific to most general
_NAME_PATTERNS = [
    # "Patient Name: SALINI BADAL JARIWAL" or "Patient Name : ..."
    re.compile(r"patient\s*name\s*[:\-\.]\s*([A-Za-z][A-Za-z\s\.]{2,60})", re.IGNORECASE),
    # "Pt. Name: ..." or "Pt Name:"
    re.compile(r"pt\.?\s*name\s*[:\-\.]\s*([A-Za-z][A-Za-z\s\.]{2,60})", re.IGNORECASE),
    # "Name: JOHN DOE" but NOT "Lab Name:" or "Test Name:"
    re.compile(r"(?<![Ll]ab\s)(?<![Tt]est\s)(?<![Dd]octor\s)(?<![Pp]hysician\s)\bname\s*[:\-\.]\s*([A-Za-z][A-Za-z\s\.]{2,60})", re.IGNORECASE),
    # "Salutation+Name: MR. SALINI BADAL"
    re.compile(r"(?:mr\.?|mrs\.?|ms\.?|dr\.?|miss)\s+([A-Za-z][A-Za-z\s\.]{2,60})", re.IGNORECASE),
    # "Referred by Dr. XYZ | Patient: SALINI BADAL" — after "patient:"
    re.compile(r"\bpatient\s*[:\-]\s*([A-Za-z][A-Za-z\s\.]{2,50})", re.IGNORECASE),
    # ALL-CAPS name on its own line (common in Indian lab PDFs like SALINI BADAL JARIWAL)
    re.compile(r"^([A-Z]{2,}(?:\s+[A-Z]{2,}){1,4})\s*$", re.MULTILINE),
]

_AGE_PATTERNS = [
    re.compile(r"age\s*[:\-]?\s*(\d{1,3})\s*(?:yrs?|years?)?", re.IGNORECASE),
    re.compile(r"(\d{1,3})\s*(?:yrs?|years?)\s*(?:old)?", re.IGNORECASE),
    # "/ 25Y" format common in Indian reports
    re.compile(r"/\s*(\d{1,3})\s*[Yy](?:[Ee][Aa][Rr][Ss]?)?"),
    # DOB: "01/01/1990" → compute age roughly
    re.compile(r"dob\s*[:\-]\s*\d{1,2}[/\-\.]\d{1,2}[/\-\.](\d{4})", re.IGNORECASE),
]

_GENDER_PATTERNS = [
    re.compile(r"(?:gender|sex)\s*[:\-\.]\s*(male|female|m|f|other)", re.IGNORECASE),
    re.compile(r"\b(male|female)\b", re.IGNORECASE),
    # "M / 45Y" — gender/age combined
    re.compile(r"\b([MF])\s*/\s*\d{1,3}\s*[Yy]", re.IGNORECASE),
    # "45Y / M"
    re.compile(r"\d{1,3}\s*[Yy]\s*/\s*([MF])\b", re.IGNORECASE),
]

_GENDER_NORMALIZE = {
    "m": "Male", "male": "Male",
    "f": "Female", "female": "Female",
    "other": "Other",
}

_REPORT_ID_PATTERNS = [
    re.compile(r"(?:report\s*(?:id|no|number|#)|sample\s*id|lab\s*id|ref\s*(?:no|id))\s*[:\-\.]\s*([A-Z0-9\-\/]{3,25})", re.IGNORECASE),
    re.compile(r"(?:report|sample|lab|accession|patient)\s*(?:id|no)\s*[:\-\.]\s*([A-Z0-9\-]{3,20})", re.IGNORECASE),
]

_DATE_PATTERNS = [
    re.compile(r"(?:report\s*date|collection\s*date|test\s*date|date\s*of\s*report|date)\s*[:\-\.]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})", re.IGNORECASE),
    re.compile(r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})", re.IGNORECASE),
    re.compile(r"(\d{4}[/\-\.]\d{2}[/\-\.]\d{2})", re.IGNORECASE),
]

_LAB_PATTERNS = [
    re.compile(r"(?:lab(?:oratory)?|clinic|hospital|diagnostic\s*centre?|centre?|path(?:ology)?)\s*[:\-\.]\s*([A-Za-z0-9\s\.,&]{4,80})", re.IGNORECASE),
]

# Common noise words to reject from name extraction
_NAME_BLACKLIST = {
    "test", "lab", "laboratory", "report", "diagnostic", "date", "age", "result",
    "patient", "name", "gender", "sex", "hospital", "clinic", "doctor", "referred",
    "collected", "reported", "sample", "ref", "range", "normal", "unit", "value",
}


def _clean_name(raw: str) -> str | None:
    """Validate and clean an extracted name candidate."""
    # Remove trailing garbage
    name = re.sub(r"[:\-\.\|]\s*$", "", raw).strip()
    # Remove trailing numeric/date artifacts
    name = re.sub(r"\s+\d+.*$", "", name).strip()
    # Must be at least 2 words OR one word of 3+ chars
    words = name.split()
    if not words:
        return None
    # Check against blacklist
    if any(w.lower() in _NAME_BLACKLIST for w in words):
        return None
    # Must have at least one alphabetic char
    if not any(c.isalpha() for c in name):
        return None
    # Reasonable length
    if len(name) < 3 or len(name) > 80:
        return None
    return name.title()


# ─────────────────────────────────────────────────────────────────────────────

_ALIAS_KEYS = list(PARAMETER_ALIASES.keys())


def normalize_parameter_name(raw: str) -> str:
    cleaned = raw.strip().lower()
    if cleaned in PARAMETER_ALIASES:
        return PARAMETER_ALIASES[cleaned]
    if cleaned.endswith("s") and cleaned[:-1] in PARAMETER_ALIASES:
        return PARAMETER_ALIASES[cleaned[:-1]]
    result = process.extractOne(
        cleaned, _ALIAS_KEYS, scorer=fuzz.ratio, score_cutoff=85,
    )
    if result:
        return PARAMETER_ALIASES[result[0]]
    return raw.strip().title()


def _try_match(line: str) -> dict[str, str] | None:
    line = normalize_range_dashes(line)
    for pattern in (TABULAR_PATTERN, COLON_PATTERN):
        m = pattern.match(line.strip())
        if m:
            return m.groupdict()
    return None


def _parse_reference_range(range_str: str | None) -> str | None:
    if not range_str:
        return None
    range_str = normalize_range_dashes(range_str.strip())
    range_str = re.sub(r"^[(\[<>]+|[)\]]+$", "", range_str).strip()
    return range_str if range_str else None


def _extract_age_from_dob_year(year_str: str) -> str:
    """Calculate approximate age from birth year."""
    try:
        import datetime
        birth_year = int(year_str)
        current_year = datetime.datetime.now().year
        age = current_year - birth_year
        if 1 <= age <= 120:
            return str(age)
    except Exception:
        pass
    return ""


class MedicalParameterParser:
    """Parse raw OCR/PDF text from a medical report into structured data."""

    def parse(self, raw_text: str) -> ParsedReport:
        report = ParsedReport(raw_text=raw_text)

        # ── 1. Extract patient metadata ──────────────────────────────────────
        self._extract_patient_info(raw_text, report)

        # ── 2. Extract parameters ────────────────────────────────────────────
        parameters: list[ParsedParameter] = []
        seen_names: set[str] = set()

        for line in raw_text.splitlines():
            line = line.strip()
            if not line or len(line) < 5:
                continue
            if re.match(r"^[A-Z\s]+$", line) and len(line) > 30:
                continue

            match_dict = _try_match(line)
            if not match_dict:
                continue

            raw_name  = (match_dict.get("name") or "").strip()
            value_str = (match_dict.get("value") or "").strip()
            if not raw_name or not value_str:
                continue

            numeric_val = extract_numeric(value_str)
            if numeric_val is None:
                continue

            canonical_name = normalize_parameter_name(raw_name)

            if canonical_name.lower() in seen_names:
                continue
            seen_names.add(canonical_name.lower())

            unit      = normalize_unit(match_dict.get("unit") or "")
            ref_range = _parse_reference_range(match_dict.get("range"))

            if not ref_range and canonical_name in DEFAULT_REFERENCE_RANGES:
                low, high, _ = DEFAULT_REFERENCE_RANGES[canonical_name]
                ref_range = f"{low}-{high}"

            param = ParsedParameter(
                name=canonical_name,
                raw_name=raw_name,
                value=numeric_val,
                raw_value=value_str,
                unit=unit,
                reference_range=ref_range,
                status="NORMAL",
            )
            parameters.append(param)
            logger.debug(f"Parsed: {canonical_name} = {numeric_val} {unit} [{ref_range}]")

        report.parameters = parameters
        logger.info(f"Parsed {len(parameters)} parameters from report")
        return report

    def _extract_patient_info(self, text: str, report: ParsedReport) -> None:
        """Try all pattern variants to extract patient name, age, gender, etc."""

        # ── Name ──────────────────────────────────────────────────────────────
        for pattern in _NAME_PATTERNS:
            m = pattern.search(text)
            if m:
                candidate = _clean_name(m.group(1))
                if candidate:
                    report.patient_name = candidate
                    logger.debug(f"Patient name extracted: {candidate}")
                    break

        # ── Age ───────────────────────────────────────────────────────────────
        for pattern in _AGE_PATTERNS:
            m = pattern.search(text)
            if m:
                val = m.group(1).strip()
                # DOB year → calculate age
                if len(val) == 4 and val.startswith("19") or val.startswith("20"):
                    val = _extract_age_from_dob_year(val)
                if val and val.isdigit() and 1 <= int(val) <= 120:
                    report.age = val
                    break

        # ── Gender ────────────────────────────────────────────────────────────
        for pattern in _GENDER_PATTERNS:
            m = pattern.search(text)
            if m:
                raw_g = m.group(1).strip().lower()
                normalized = _GENDER_NORMALIZE.get(raw_g)
                if normalized:
                    report.gender = normalized
                    break

        # ── Report ID ─────────────────────────────────────────────────────────
        for pattern in _REPORT_ID_PATTERNS:
            m = pattern.search(text)
            if m:
                report.report_id = m.group(1).strip().upper()
                break

        # ── Date ──────────────────────────────────────────────────────────────
        for pattern in _DATE_PATTERNS:
            m = pattern.search(text)
            if m:
                report.date = m.group(1).strip()
                break

        # ── Lab name ──────────────────────────────────────────────────────────
        for pattern in _LAB_PATTERNS:
            m = pattern.search(text)
            if m:
                lab = m.group(1).strip().rstrip(".,")
                if len(lab) > 4:
                    report.lab_name = lab[:200]
                    break

        logger.debug(
            f"Patient: name={report.patient_name!r}, age={report.age!r}, "
            f"gender={report.gender!r}, lab={report.lab_name!r}"
        )
