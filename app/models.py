"""Pydantic models for ValueSet API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ValueSetValue(BaseModel):
    """
    Individual term/value within a ValueSet.

    Represents a single concept with its semantic annotations and relationships.
    """

    accession: str = Field(
        ...,
        description="Fully name-spaced unique identifier for this term",
        examples=["SNOMED:123456789"],
    )
    valueset: str = Field(..., description="ValueSet namespace this term belongs to")
    pURL: Optional[HttpUrl] = Field(
        None, description="Permanent URL for this term (generated at runtime if not provided)"
    )
    label: str = Field(..., description="Human-readable display name")
    value: str = Field(..., description="Actual value of the term")
    identical_terms: List[HttpUrl] = Field(
        default_factory=list,
        description="URIs of ontologically identical terms from other systems",
    )
    similar_terms: List[HttpUrl] = Field(
        default_factory=list, description="URIs of semantically similar terms"
    )
    definition: str = Field(..., description="Short succinct description of the term")
    full_definition: str = Field(..., description="Comprehensive description and usage notes")
    deprecated: bool = Field(
        default=False, description="Whether this term is still active or has been deprecated"
    )
    deprecated_to: List[str] = Field(
        default_factory=list,
        description="Accessions of terms that replace this deprecated term",
    )
    additional: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom attributes (non-standardized, extensible)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "accession": "SNOMED:73211009",
                    "valueset": "diabetes_types",
                    "pURL": "https://api.example.com/terms/SNOMED:73211009",
                    "label": "Diabetes mellitus",
                    "value": "diabetes_mellitus",
                    "identical_terms": ["http://purl.bioontology.org/ontology/SNOMEDCT/73211009"],
                    "similar_terms": ["http://purl.obolibrary.org/obo/MONDO_0005015"],
                    "definition": "A metabolic disorder characterized by high blood sugar",
                    "full_definition": "Diabetes mellitus is a group of metabolic disorders...",
                    "deprecated": False,
                    "deprecated_to": [],
                    "additional": {"icd10": "E11", "severity": "chronic"},
                }
            ]
        }
    }


class ValueSet(BaseModel):
    """
    A controlled vocabulary/ontology containing related terms.

    ValueSets group semantically related terms for use in data annotation.
    """

    accession: str = Field(
        ..., description="Unique identifier for this ValueSet", examples=["diabetes_types"]
    )
    pURL: HttpUrl = Field(
        ...,
        description="Permanent URL for this ValueSet",
        examples=["https://api.example.com/valuesets/diabetes_types"],
    )
    definition: str = Field(..., description="Succinct definition and scope of this ValueSet")
    full_definition: str = Field(..., description="Comprehensive description of the ValueSet")
    values: List[ValueSetValue] = Field(
        default_factory=list, description="Terms contained in this ValueSet"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "accession": "diabetes_types",
                    "pURL": "https://api.example.com/valuesets/diabetes_types",
                    "definition": "Classification of diabetes mellitus types",
                    "full_definition": "A comprehensive classification...",
                    "values": [],
                }
            ]
        }
    }


class ValueSetSummary(BaseModel):
    """Summary of a ValueSet without the full list of values."""

    accession: str = Field(..., description="Unique identifier for this ValueSet")
    pURL: HttpUrl = Field(..., description="Permanent URL for this ValueSet")
    definition: str = Field(..., description="Succinct definition")
    full_definition: str = Field(..., description="Comprehensive description")
    value_count: int = Field(..., description="Number of terms in this ValueSet")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", examples=["healthy"])


class ServiceInfo(BaseModel):
    """GA4GH-compliant service information."""

    id: str = Field(..., description="Unique service identifier")
    name: str = Field(default="ValueSet API")
    type_: Dict[str, str] = Field(
        default={"group": "org.ga4gh", "artifact": "valueset", "version": "1.0.0"},
        alias="type",
    )
    description: str = Field(
        default="Healthcare Ontology & Terminology Management System - ValueSet API"
    )
    organization: Dict[str, str] = Field(
        default={"name": "Your Organization", "url": "https://example.com"}
    )
    version: str = Field(..., description="API version")
    environment: str = Field(
        default="production", examples=["development", "staging", "production"]
    )

    model_config = {"populate_by_name": True}
