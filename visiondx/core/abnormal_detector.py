"""
VisionDX — Abnormal Value Detector

Compares extracted blood test parameter values against reference ranges.
Supports range formats:
  - "13-17"       (range)
  - "13 - 17"     (range with spaces)
  - "<200"        (upper bound only)
  - ">4.5"        (lower bound only)
  - "0.5-1.5"     (decimal range)

Returns status: NORMAL | LOW | HIGH
"""
from __future__ import annotations

import re

from loguru import logger

from visiondx.database.schemas import ParsedParameter
from visiondx.utils.medical_dictionary import DEFAULT_REFERENCE_RANGES
from visiondx.utils.text_cleaner import normalize_range_dashes

# Status constants
NORMAL = "NORMAL"
LOW = "LOW"
HIGH = "HIGH"

# Status → display color mapping
STATUS_COLORS: dict[str, str] = {
    NORMAL: "#22c55e",   # green
    LOW:    "#3b82f6",   # blue
    HIGH:   "#ef4444",   # red
}


def parse_reference_range(
    range_str: str,
) -> tuple[float | None, float | None]:
    """
    Parse a reference range string into (low, high) floats.
    Returns (None, None) if parsing fails.

    Examples:
      "13-17"   → (13.0, 17.0)
      "< 200"   → (None, 200.0)
      ">4.5"    → (4.5, None)
      "0.5-1.5" → (0.5, 1.5)
    """
    if not range_str:
        return None, None

    range_str = normalize_range_dashes(range_str.strip())

    # Format: "< 200" or "<=200" → upper bound only
    m = re.match(r"^[<＜]\s*=?\s*(\d+\.?\d*)$", range_str)
    if m:
        return None, float(m.group(1))

    # Format: ">4.5" or ">=4.5" → lower bound only
    m = re.match(r"^[>＞]\s*=?\s*(\d+\.?\d*)$", range_str)
    if m:
        return float(m.group(1)), None

    # Format: "low-high"
    m = re.match(r"^(\d+\.?\d*)\s*-\s*(\d+\.?\d*)$", range_str)
    if m:
        return float(m.group(1)), float(m.group(2))

    # Format: "low – high" with Unicode dashes (already normalized above)
    # Try generic split
    parts = re.split(r"\s*-\s*", range_str)
    if len(parts) == 2:
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            pass

    logger.debug(f"Could not parse reference range: '{range_str}'")
    return None, None


def detect_status(
    value: float,
    range_str: str | None,
    canonical_name: str | None = None,
) -> str:
    """
    Determine whether a parameter value is NORMAL, LOW, or HIGH.
    Falls back to DEFAULT_REFERENCE_RANGES if range_str is empty.
    """
    # Try provided range first
    low, high = (None, None)
    if range_str:
        low, high = parse_reference_range(range_str)

    # Fall back to dictionary
    if low is None and high is None and canonical_name:
        if canonical_name in DEFAULT_REFERENCE_RANGES:
            low, high, _ = DEFAULT_REFERENCE_RANGES[canonical_name]

    if low is None and high is None:
        return NORMAL  # Can't determine — assume normal

    if low is not None and value < low:
        return LOW
    if high is not None and value > high:
        return HIGH
    return NORMAL


class AbnormalDetector:
    """
    Detect abnormal parameters in a parsed report.
    Mutates the `status` field of each ParsedParameter in place.
    Returns list of abnormal parameters.
    """

    def detect(
        self, parameters: list[ParsedParameter]
    ) -> tuple[list[ParsedParameter], list[ParsedParameter]]:
        """
        Classify all parameters. Returns (all_parameters, abnormal_parameters).
        """
        abnormal: list[ParsedParameter] = []
        for param in parameters:
            if param.value is None:
                param.status = NORMAL
                continue
            status = detect_status(
                param.value,
                param.reference_range,
                param.name,
            )
            param.status = status
            if status != NORMAL:
                abnormal.append(param)
                logger.info(
                    f"ABNORMAL: {param.name} = {param.value} {param.unit} "
                    f"[range: {param.reference_range}] → {status}"
                )

        logger.info(
            f"Detection complete: {len(abnormal)} abnormal / {len(parameters)} total"
        )
        return parameters, abnormal
