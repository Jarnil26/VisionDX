"""
VisionDX — Text Cleaning Utilities
"""
import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Full pipeline clean: unicode normalize → strip control chars →
    normalise whitespace → fix OCR ligature artifacts.
    """
    # Normalize unicode (accents, special chars)
    text = unicodedata.normalize("NFKD", text)
    # Replace curly quotes and dashes with ASCII equivalents
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    # Remove non-printable control characters except newline and tab
    text = "".join(c for c in text if c.isprintable() or c in "\n\t")
    # Collapse multiple spaces/tabs on the same line
    lines = [re.sub(r"[ \t]{2,}", " ", line) for line in text.splitlines()]
    # Remove completely empty lines (keep single blank lines)
    cleaned_lines: list[str] = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if not prev_blank:
                cleaned_lines.append("")
            prev_blank = True
        else:
            cleaned_lines.append(stripped)
            prev_blank = False
    return "\n".join(cleaned_lines).strip()


def normalize_range_dashes(text: str) -> str:
    """
    Normalize en-dash / em-dash / multiple hyphens in ranges to a single hyphen.
    Example: '13–17' → '13-17', '13 — 17' → '13-17'
    """
    # Replace various dash types
    text = re.sub(r"[\u2013\u2014\u2212]", "-", text)
    # Collapse '13 - 17' → '13-17'
    text = re.sub(r"(\d)\s*-\s*(\d)", r"\1-\2", text)
    return text


def remove_headers_footers(text: str, header_lines: int = 3, footer_lines: int = 2) -> str:
    """Strip likely header/footer lines from each page block."""
    lines = text.splitlines()
    if len(lines) <= header_lines + footer_lines:
        return text
    return "\n".join(lines[header_lines: len(lines) - footer_lines])


def extract_numeric(value_str: str) -> float | None:
    """
    Extract the first numeric value from a string.
    Handles: '10.2', '< 5.0', '> 100', '10 - 17', '.5'
    """
    match = re.search(r"[-+]?\d*\.?\d+", value_str.replace(",", "."))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def normalize_unit(unit: str) -> str:
    """Normalize unit strings to a standard form."""
    unit = unit.strip()
    # Common normalizations
    replacements = {
        "g/dl": "g/dL",
        "mg/dl": "mg/dL",
        "u/l": "U/L",
        "iu/l": "IU/L",
        "mmol/l": "mmol/L",
        "meq/l": "mEq/L",
        "10^3/ul": "10³/µL",
        "10^6/ul": "10⁶/µL",
        "thou/ul": "10³/µL",
        "mill/ul": "10⁶/µL",
        "microgram/dl": "µg/dL",
        "ng/ml": "ng/mL",
        "pg/ml": "pg/mL",
        "miu/l": "mIU/L",
        "miu/ml": "mIU/mL",
    }
    return replacements.get(unit.lower(), unit)
