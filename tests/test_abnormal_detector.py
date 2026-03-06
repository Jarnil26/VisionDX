"""
VisionDX — Unit Tests: Abnormal Detector
"""
import pytest
from visiondx.core.abnormal_detector import (
    AbnormalDetector,
    detect_status,
    parse_reference_range,
    HIGH,
    LOW,
    NORMAL,
)


class TestParseReferenceRange:
    def test_standard_range(self):
        assert parse_reference_range("13-17") == (13.0, 17.0)

    def test_decimal_range(self):
        assert parse_reference_range("0.5-1.5") == (0.5, 1.5)

    def test_upper_bound_only(self):
        low, high = parse_reference_range("<200")
        assert low is None
        assert high == 200.0

    def test_lower_bound_only(self):
        low, high = parse_reference_range(">4.5")
        assert low == 4.5
        assert high is None

    def test_empty_returns_none(self):
        assert parse_reference_range("") == (None, None)
        assert parse_reference_range(None) == (None, None)


class TestDetectStatus:
    def test_normal_in_range(self):
        assert detect_status(14.0, "13-17") == NORMAL

    def test_low_below_range(self):
        assert detect_status(10.0, "13-17") == LOW

    def test_high_above_range(self):
        assert detect_status(18.5, "13-17") == HIGH

    def test_boundary_at_low(self):
        # Exactly at boundary → NORMAL
        assert detect_status(13.0, "13-17") == NORMAL

    def test_boundary_at_high(self):
        assert detect_status(17.0, "13-17") == NORMAL

    def test_no_range_uses_dictionary(self):
        # Hemoglobin 8.0 is LOW (range 12.0-17.5 from dictionary)
        assert detect_status(8.0, None, "Hemoglobin") == LOW

    def test_no_range_no_dict_returns_normal(self):
        assert detect_status(999.0, None, None) == NORMAL


class TestAbnormalDetector:
    def test_detects_low_hemoglobin(self):
        from visiondx.database.schemas import ParsedParameter

        params = [
            ParsedParameter(name="Hemoglobin", value=9.0, reference_range="13-17")
        ]
        detector = AbnormalDetector()
        all_params, abnormal = detector.detect(params)
        assert len(abnormal) == 1
        assert abnormal[0].status == LOW

    def test_detects_high_glucose(self):
        from visiondx.database.schemas import ParsedParameter

        params = [
            ParsedParameter(name="Glucose", value=250.0, reference_range="70-100")
        ]
        detector = AbnormalDetector()
        _, abnormal = detector.detect(params)
        assert len(abnormal) == 1
        assert abnormal[0].status == HIGH

    def test_normal_parameters_not_flagged(self):
        from visiondx.database.schemas import ParsedParameter

        params = [
            ParsedParameter(name="Hemoglobin", value=14.5, reference_range="13-17"),
            ParsedParameter(name="Glucose", value=90.0, reference_range="70-100"),
        ]
        detector = AbnormalDetector()
        _, abnormal = detector.detect(params)
        assert len(abnormal) == 0
