"""Tests for the ingest-csv CLI."""

import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_valueset, list_valuesets
from ingestion.cli import main


def make_session(db_path: str) -> Session:
    """Create a session connected to the given SQLite database path."""
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


@pytest.fixture
def test_csv_path() -> Path:
    """Path to the APPRIS test fixture CSV."""
    return Path(__file__).parent / "fixtures" / "appris.csv"


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Temporary SQLite database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    Path(db_path).unlink()
    yield db_path
    Path(db_path).unlink(missing_ok=True)


class TestCLISingleFile:
    """Tests for single-file ingestion via CLI."""

    def test_ingest_single_file(
        self, test_csv_path: Path, temp_db: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Basic single-file ingestion stores data in the database."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "ingest-csv",
                str(test_csv_path),
                "--accession", "appris",
                "--definition", "APPRIS isoforms",
                "--full-definition", "Full APPRIS isoform classification",
                "--db-path", temp_db,
            ],
        )
        main()

        session = make_session(temp_db)
        try:
            vs = get_valueset(session, "appris", include_deprecated=True)
            assert vs is not None
            assert vs.accession == "appris"
            assert vs.definition == "APPRIS isoforms"
            assert vs.full_definition == "Full APPRIS isoform classification"
            assert len(vs.values) == 7
        finally:
            session.close()

    def test_accession_defaults_to_filename(
        self, test_csv_path: Path, temp_db: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When --accession is omitted the stem of the filename is used."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["ingest-csv", str(test_csv_path), "--db-path", temp_db],
        )
        main()

        session = make_session(temp_db)
        try:
            # Filename stem is "appris"
            vs = get_valueset(session, "appris", include_deprecated=True)
            assert vs is not None
        finally:
            session.close()

    def test_file_not_found_exits(self, temp_db: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI exits with code 1 when the CSV file does not exist."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["ingest-csv", "/nonexistent/path/file.csv", "--db-path", temp_db],
        )
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


class TestCLIYAMLMetadata:
    """Tests for YAML metadata loading."""

    def test_yaml_metadata_applied(
        self, test_csv_path: Path, temp_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Metadata from a YAML file is applied to the ingested ValueSet."""
        metadata = {
            "appris": {
                "definition": "YAML definition",
                "full_definition": "YAML full definition",
            }
        }
        yaml_file = tmp_path / "metadata.yaml"
        yaml_file.write_text(yaml.dump(metadata))

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "ingest-csv",
                str(test_csv_path),
                "--accession", "appris",
                "--metadata", str(yaml_file),
                "--db-path", temp_db,
            ],
        )
        main()

        session = make_session(temp_db)
        try:
            vs = get_valueset(session, "appris", include_deprecated=True)
            assert vs is not None
            assert vs.definition == "YAML definition"
            assert vs.full_definition == "YAML full definition"
        finally:
            session.close()

    def test_cli_arg_takes_precedence_over_yaml(
        self, test_csv_path: Path, temp_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A CLI --definition argument overrides the value from the YAML file."""
        metadata = {"appris": {"definition": "YAML definition", "full_definition": "YAML full"}}
        yaml_file = tmp_path / "metadata.yaml"
        yaml_file.write_text(yaml.dump(metadata))

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "ingest-csv",
                str(test_csv_path),
                "--accession", "appris",
                "--definition", "CLI definition",
                "--metadata", str(yaml_file),
                "--db-path", temp_db,
            ],
        )
        main()

        session = make_session(temp_db)
        try:
            vs = get_valueset(session, "appris", include_deprecated=True)
            assert vs is not None
            assert vs.definition == "CLI definition"
            # full_definition not overridden by CLI, so YAML value is used
            assert vs.full_definition == "YAML full"
        finally:
            session.close()

    def test_missing_yaml_file_exits(
        self, test_csv_path: Path, temp_db: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI exits with code 1 when the YAML metadata file does not exist."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "ingest-csv",
                str(test_csv_path),
                "--metadata", "/nonexistent/metadata.yaml",
                "--db-path", temp_db,
            ],
        )
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


class TestCLIDirectory:
    """Tests for directory ingestion via CLI."""

    def test_ingest_directory(
        self, test_csv_path: Path, temp_db: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Directory ingestion loads all CSV files found."""
        fixtures_dir = test_csv_path.parent
        monkeypatch.setattr(
            sys,
            "argv",
            ["ingest-csv", "--directory", str(fixtures_dir), "--db-path", temp_db],
        )
        main()

        session = make_session(temp_db)
        try:
            valuesets = list_valuesets(session)
            assert len(valuesets) >= 1
            assert any(vs.accession == "appris" for vs in valuesets)
        finally:
            session.close()

    def test_directory_not_found_exits(
        self, temp_db: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI exits with code 1 when the directory does not exist."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["ingest-csv", "--directory", "/nonexistent/dir", "--db-path", temp_db],
        )
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
