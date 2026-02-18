"""Tests for API endpoints."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import insert_valueset
from app.main import app
from app.models import ValueSet, ValueSetValue


@asynccontextmanager
async def empty_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Empty lifespan for tests - don't initialize database."""
    yield


@pytest.fixture
def client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with test database."""
    # Override the lifespan to prevent init_db() on main database
    app.router.lifespan_context = empty_lifespan

    # Insert test data using the test session
    test_valueset = ValueSet(
        accession="test_diseases",
        pURL="https://api.example.com/valuesets/test_diseases",
        definition="Test disease classification",
        full_definition="Comprehensive test disease classification",
        values=[
            ValueSetValue(
                accession="TEST:001",
                valueset="test_diseases",
                label="Test Disease 1",
                value="test_disease_1",
                definition="First test disease",
                full_definition="Full description of first test disease",
                deprecated=False,
            ),
            ValueSetValue(
                accession="TEST:002",
                valueset="test_diseases",
                label="Test Disease 2",
                value="test_disease_2",
                definition="Second test disease",
                full_definition="Full description of second test disease",
                deprecated=True,
                deprecated_to=["TEST:003"],
            ),
        ],
    )

    insert_valueset(test_db_session, test_valueset)
    test_db_session.commit()  # Commit the test data

    # Create test client - it will use the global engine which is now set to test engine
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_service_info(self, client: TestClient) -> None:
        """Test service info endpoint."""
        response = client.get("/service-info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ValueSet API"
        assert "version" in data
        assert "organization" in data


class TestTermEndpoints:
    """Test term-related endpoints."""

    def test_get_term_success(self, client: TestClient) -> None:
        """Test retrieving an existing term."""
        response = client.get("/term/TEST:001")
        assert response.status_code == 200
        data = response.json()
        assert data["accession"] == "TEST:001"
        assert data["label"] == "Test Disease 1"
        assert data["valueset"] == "test_diseases"
        assert data["deprecated"] is False

    def test_get_term_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent term."""
        response = client.get("/term/NONEXISTENT:999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_term_with_purl(self, client: TestClient) -> None:
        """Test that pURL is generated for term."""
        response = client.get("/term/TEST:001")
        assert response.status_code == 200
        data = response.json()
        assert "pURL" in data
        assert data["pURL"] is not None


class TestValueSetEndpoints:
    """Test ValueSet-related endpoints."""

    def test_list_valuesets(self, client: TestClient) -> None:
        """Test listing all ValueSets."""
        response = client.get("/list/valuesets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(vs["accession"] == "test_diseases" for vs in data)

    def test_list_valuesets_contains_count(self, client: TestClient) -> None:
        """Test that ValueSet summaries include term count."""
        response = client.get("/list/valuesets")
        assert response.status_code == 200
        data = response.json()
        test_vs = next(vs for vs in data if vs["accession"] == "test_diseases")
        assert "value_count" in test_vs
        assert test_vs["value_count"] >= 2

    def test_get_valueset_success(self, client: TestClient) -> None:
        """Test retrieving a complete ValueSet."""
        response = client.get("/list/valuesets/test_diseases")
        assert response.status_code == 200
        data = response.json()
        assert data["accession"] == "test_diseases"
        assert "values" in data
        # By default, deprecated terms are excluded
        assert len(data["values"]) == 1

    def test_get_valueset_with_deprecated(self, client: TestClient) -> None:
        """Test retrieving ValueSet with deprecated terms."""
        response = client.get("/list/valuesets/test_diseases?deprecated=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["values"]) == 2
        # Check that deprecated term is included
        assert any(v["deprecated"] is True for v in data["values"])

    def test_get_valueset_without_deprecated(self, client: TestClient) -> None:
        """Test retrieving ValueSet without deprecated terms."""
        response = client.get("/list/valuesets/test_diseases?deprecated=false")
        assert response.status_code == 200
        data = response.json()
        # Only non-deprecated terms
        assert all(v["deprecated"] is False for v in data["values"])

    def test_get_valueset_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent ValueSet."""
        response = client.get("/list/valuesets/nonexistent_valueset")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestRootEndpoint:
    """Test root redirect."""

    def test_root_redirects_to_docs(self, client: TestClient) -> None:
        """Test that root redirects to API documentation."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/browse"


class TestOpenAPI:
    """Test OpenAPI documentation."""

    def test_openapi_schema_exists(self, client: TestClient) -> None:
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/term/{accession}" in schema["paths"]
        assert "/list/valuesets" in schema["paths"]
