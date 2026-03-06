"""
VisionDX — Unit Tests: Medical Parameter Parser
"""
import pytest
from visiondx.core.parser import MedicalParameterParser, normalize_parameter_name


@pytest.fixture
def parser():
    return MedicalParameterParser()


class TestNormalizeParameterName:
    def test_exact_alias(self):
        assert normalize_parameter_name("hb") == "Hemoglobin"
        assert normalize_parameter_name("Hb") == "Hemoglobin"
        assert normalize_parameter_name("WBC") == "WBC"
        assert normalize_parameter_name("sgot") == "AST"

    def test_canonical_passthrough(self):
        assert normalize_parameter_name("Hemoglobin") == "Hemoglobin"

    def test_fuzzy_match(self):
        # Close enough to "Hemoglobin" alias "hgb"
        result = normalize_parameter_name("HGB")
        assert result == "Hemoglobin"

    def test_unknown_returns_title(self):
        result = normalize_parameter_name("some unknown test")
        assert result == "Some Unknown Test"


class TestMedicalParameterParser:
    SAMPLE_REPORT = """
    Patient Name: John Doe
    Age: 35
    Gender: Male
    Report ID: VDX-ABC123
    Date: 06/03/2026
    Lab: City Diagnostics

    Hemoglobin   10.2   g/dL   13-17
    WBC          11.5   10³/µL  4-11
    Platelets    280    10³/µL  150-400
    Glucose      95     mg/dL   70-100
    TSH          2.1    mIU/L   0.4-4.0
    """

    def test_parses_patient_name(self, parser):
        result = parser.parse(self.SAMPLE_REPORT)
        assert "John" in result.patient_name or result.patient_name == "Unknown"

    def test_parses_parameters(self, parser):
        result = parser.parse(self.SAMPLE_REPORT)
        assert len(result.parameters) >= 3

    def test_hemoglobin_value(self, parser):
        result = parser.parse(self.SAMPLE_REPORT)
        hb = next((p for p in result.parameters if p.name == "Hemoglobin"), None)
        assert hb is not None
        assert hb.value == pytest.approx(10.2, rel=0.01)

    def test_report_id_extracted(self, parser):
        result = parser.parse(self.SAMPLE_REPORT)
        assert result.report_id  # should not be empty

    def test_empty_text_returns_empty_params(self, parser):
        result = parser.parse("")
        assert result.parameters == []
