"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models import HealthResponse, ServiceInfo, ValueSet, ValueSetSummary, ValueSetValue


class TestValueSetValue:
    """Test ValueSetValue model."""

    def test_valid_valueset_value(self) -> None:
        """Test creating a valid ValueSetValue."""
        value = ValueSetValue(
            accession="SNOMED:73211009",
            valueset="diabetes_types",
            label="Diabetes mellitus",
            value="diabetes_mellitus",
            definition="A metabolic disorder",
            full_definition="Detailed description of diabetes mellitus",
        )
        assert value.accession == "SNOMED:73211009"
        assert value.valueset == "diabetes_types"
        assert value.deprecated is False
        assert value.identical_terms == []
        assert value.similar_terms == []
        assert value.deprecated_to == []
        assert value.additional == {}

    def test_valueset_value_with_all_fields(self) -> None:
        """Test ValueSetValue with all optional fields."""
        value = ValueSetValue(
            accession="SNOMED:73211009",
            valueset="diabetes_types",
            pURL="https://api.example.com/terms/SNOMED:73211009",
            label="Diabetes mellitus",
            value="diabetes_mellitus",
            identical_terms=["http://example.com/term1"],
            similar_terms=["http://example.com/term2"],
            definition="Short def",
            full_definition="Full def",
            deprecated=True,
            deprecated_to=["SNOMED:12345"],
            additional={"icd10": "E11"},
        )
        assert value.deprecated is True
        assert len(value.identical_terms) == 1
        assert value.additional["icd10"] == "E11"

    def test_valueset_value_missing_required_fields(self) -> None:
        """Test that missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            ValueSetValue(  # type: ignore[call-arg]
                accession="SNOMED:73211009",
                # Missing valueset, label, value, definition, full_definition
            )


class TestValueSet:
    """Test ValueSet model."""

    def test_valid_valueset(self) -> None:
        """Test creating a valid ValueSet."""
        valueset = ValueSet(
            accession="diabetes_types",
            pURL="https://api.example.com/valuesets/diabetes_types",
            definition="Classification of diabetes types",
            full_definition="Comprehensive classification of diabetes mellitus types",
        )
        assert valueset.accession == "diabetes_types"
        assert valueset.values == []

    def test_valueset_with_values(self) -> None:
        """Test ValueSet containing values."""
        value1 = ValueSetValue(
            accession="SNOMED:1",
            valueset="test",
            label="Label 1",
            value="value1",
            definition="Def 1",
            full_definition="Full def 1",
        )
        value2 = ValueSetValue(
            accession="SNOMED:2",
            valueset="test",
            label="Label 2",
            value="value2",
            definition="Def 2",
            full_definition="Full def 2",
        )

        valueset = ValueSet(
            accession="test",
            pURL="https://api.example.com/valuesets/test",
            definition="Test",
            full_definition="Test",
            values=[value1, value2],
        )
        assert len(valueset.values) == 2
        assert valueset.values[0].accession == "SNOMED:1"


class TestValueSetSummary:
    """Test ValueSetSummary model."""

    def test_valid_summary(self) -> None:
        """Test creating a valid ValueSetSummary."""
        summary = ValueSetSummary(
            accession="diabetes_types",
            pURL="https://api.example.com/valuesets/diabetes_types",
            definition="Short def",
            full_definition="Full def",
            value_count=5,
        )
        assert summary.accession == "diabetes_types"
        assert summary.value_count == 5


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_health_response(self) -> None:
        """Test HealthResponse model."""
        response = HealthResponse(status="healthy")
        assert response.status == "healthy"


class TestServiceInfo:
    """Test ServiceInfo model."""

    def test_service_info(self) -> None:
        """Test ServiceInfo model."""
        info = ServiceInfo(
            id="org.example.valueset",
            version="1.0.0",
        )
        assert info.id == "org.example.valueset"
        assert info.name == "ValueSet API"
        assert info.version == "1.0.0"
