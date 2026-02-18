"""Tests for CSV ingestion."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_term, get_valueset, list_valuesets
from ingestion.csv_loader import CSVLoader


def make_session(db_path: str) -> Session:
    """Create a SQLAlchemy session connected to the given database path."""
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


@pytest.fixture
def test_csv_path() -> Path:
    """Get path to test CSV fixture."""
    return Path(__file__).parent / "fixtures" / "appris.csv"


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create temporary database for testing."""
    # Create temp file to get a unique path, then delete it
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    Path(db_path).unlink()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestCSVLoader:
    """Test CSV loading functionality."""

    def test_load_csv_file(self, test_csv_path: Path, temp_db: str) -> None:
        """Test loading a CSV file."""
        with CSVLoader(db_path=temp_db) as loader:
            loader.ingest_csv(
                csv_path=test_csv_path,
                valueset_accession="appris",
                definition="APPRIS Principal and Alternative isoforms",
                full_definition="A comprehensive classification of principal and alternative isoforms.",
            )

        # Verify data was loaded
        session = make_session(temp_db)
        try:
            valueset = get_valueset(session, "appris", include_deprecated=True)
            assert valueset is not None
            assert valueset.accession == "appris"
            assert len(valueset.values) == 7  # 7 rows in the appris CSV
        finally:
            session.close()

    def test_load_csv_validates_terms(self, test_csv_path: Path, temp_db: str) -> None:
        """Test that loaded terms are properly validated."""
        with CSVLoader(db_path=temp_db) as loader:
            loader.ingest_csv(
                csv_path=test_csv_path,
                valueset_accession="appris",
                definition="Test",
                full_definition="Test",
            )

        # Get a specific term
        session = make_session(temp_db)
        try:
            term = get_term(session, "appris.principal1.1")
            assert term is not None
            assert term.label == "APPRIS P1"
            assert term.value == "apprisp1"
            assert term.deprecated is False
        finally:
            session.close()

    def test_load_csv_handles_optional_fields(self, test_csv_path: Path, temp_db: str) -> None:
        """Test that optional fields are handled correctly."""
        with CSVLoader(db_path=temp_db) as loader:
            loader.ingest_csv(test_csv_path)

        # Check term with default values
        session = make_session(temp_db)
        try:
            term = get_term(session, "appris.principal2.1")
            assert term is not None
            assert term.label == "APPRIS P2"
        finally:
            session.close()

    def test_load_csv_handles_deprecated_terms(self, test_csv_path: Path, temp_db: str) -> None:
        """Test handling of deprecated terms."""
        with CSVLoader(db_path=temp_db) as loader:
            loader.ingest_csv(test_csv_path)

        session = make_session(temp_db)
        try:
            # Get all terms including deprecated
            valueset = get_valueset(session, "appris", include_deprecated=True)
            assert valueset is not None
            all_terms = valueset.values
            assert len(all_terms) == 7

            # Get only active terms
            valueset_active = get_valueset(session, "appris", include_deprecated=False)
            assert valueset_active is not None
            active_terms = valueset_active.values

            # All 7 terms should be active in our updated test data
            assert len(active_terms) == 7
        finally:
            session.close()

    def test_load_invalid_csv(self, temp_db: str) -> None:
        """Test that invalid CSV raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # Write CSV without required columns
            f.write("wrong_column,another_column\n")
            f.write("value1,value2\n")
            invalid_csv = f.name

        try:
            with CSVLoader(db_path=temp_db) as loader:
                with pytest.raises(ValueError, match="missing required columns"):
                    loader.ingest_csv(Path(invalid_csv))
        finally:
            Path(invalid_csv).unlink()

    def test_loader_context_manager(self, temp_db: str) -> None:
        """Test that CSVLoader works as context manager."""
        with CSVLoader(db_path=temp_db) as loader:
            assert loader is not None
        # Engine should be disposed after context exit

    def test_json_field_parsing(self, temp_db: str) -> None:
        """Test parsing of JSON fields from CSV."""
        loader = CSVLoader(db_path=temp_db)

        # Test list parsing
        result = loader.parse_json_field('["url1", "url2"]', "identical_terms")
        assert result == ["url1", "url2"]

        # Test dict parsing
        result = loader.parse_json_field('{"key": "value"}', "additional")
        assert result == {"key": "value"}

        # Test empty/null handling
        result = loader.parse_json_field("", "identical_terms")
        assert result == []

        result = loader.parse_json_field("", "additional")
        assert result == {}

        loader.close()


class TestCSVLoaderDirectory:
    """Test directory ingestion."""

    def test_ingest_directory(self, test_csv_path: Path, temp_db: str) -> None:
        """Test ingesting all CSV files from a directory."""
        fixtures_dir = test_csv_path.parent

        with CSVLoader(db_path=temp_db) as loader:
            loader.ingest_directory(fixtures_dir)

        # Should have loaded at least one ValueSet
        session = make_session(temp_db)
        try:
            valuesets = list_valuesets(session)
            assert len(valuesets) >= 1
        finally:
            session.close()

    def test_ingest_directory_with_yaml_metadata(
        self, test_csv_path: Path, temp_db: str
    ) -> None:
        """Test directory ingestion applies YAML metadata per accession."""
        fixtures_dir = test_csv_path.parent
        yaml_metadata = {
            "appris": {
                "definition": "From YAML: APPRIS definition",
                "full_definition": "From YAML: APPRIS full definition",
            }
        }

        with CSVLoader(db_path=temp_db) as loader:
            loader.ingest_directory(fixtures_dir, yaml_metadata=yaml_metadata)

        session = make_session(temp_db)
        try:
            valuesets = list_valuesets(session)
            appris = next(vs for vs in valuesets if vs.accession == "appris")
            assert appris.definition == "From YAML: APPRIS definition"
            assert appris.full_definition == "From YAML: APPRIS full definition"
        finally:
            session.close()
