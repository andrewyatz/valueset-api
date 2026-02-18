"""CSV ingestion pipeline for ValueSets."""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import insert_valueset
from app.models import ValueSet, ValueSetValue
from app.schema import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVLoader:
    """Load ValueSets from CSV files into the database."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize CSV loader.

        Args:
            db_path: Optional database path override
        """
        path = db_path or settings.database_path
        self._engine = create_engine(
            f"sqlite:///{path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=self._engine)
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine
        )

    def _get_session(self) -> Session:
        """Create a new session on this loader's engine."""
        return self._session_factory()

    def parse_json_field(self, value: Any, field_name: str) -> Any:
        """
        Parse a JSON field from CSV.

        Args:
            value: The raw value from CSV
            field_name: Name of the field for error reporting

        Returns:
            Parsed JSON value or appropriate default
        """
        if value == "" or value is None:
            # Return appropriate default based on field name
            if "terms" in field_name.lower() or "deprecated_to" in field_name.lower():
                return []
            elif "additional" in field_name.lower():
                return {}
            return None

        if isinstance(value, (list, dict)):
            return value

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON for {field_name}: {value}. Error: {e}")
            if "terms" in field_name.lower() or "deprecated_to" in field_name.lower():
                return []
            elif "additional" in field_name.lower():
                return {}
            return None

    def load_valueset_from_csv(
        self, csv_path: Path, valueset_accession: str, valueset_metadata: Dict[str, str]
    ) -> ValueSet:
        """
        Load a ValueSet from a CSV file.

        Args:
            csv_path: Path to CSV file
            valueset_accession: Accession for the ValueSet
            valueset_metadata: Metadata for the ValueSet (definition, full_definition)

        Returns:
            Loaded ValueSet object

        Raises:
            ValueError: If CSV is invalid or required fields are missing
        """
        logger.info(f"Loading ValueSet from {csv_path}")

        # Read CSV using Python's csv module
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}") from e

        if not rows:
            raise ValueError("CSV file is empty")

        # Validate required columns
        required_columns = ["accession", "label", "value", "definition", "full_definition"]
        fieldnames = rows[0].keys() if rows else []
        missing_columns = [col for col in required_columns if col not in fieldnames]
        if missing_columns:
            raise ValueError(f"CSV missing required columns: {missing_columns}")

        # Parse ValueSet values
        values: List[ValueSetValue] = []
        errors: List[str] = []

        for idx, row in enumerate(rows):
            try:
                # Parse optional fields
                identical_terms = self.parse_json_field(
                    row.get("identical_terms", ""), "identical_terms"
                )
                similar_terms = self.parse_json_field(row.get("similar_terms", ""), "similar_terms")
                deprecated_to = self.parse_json_field(row.get("deprecated_to", ""), "deprecated_to")
                additional = self.parse_json_field(row.get("additional", ""), "additional")

                # Handle pURL - it's optional in CSV
                purl = row.get("pURL", "").strip()
                if not purl:
                    purl = None

                # Handle deprecated field
                deprecated_str = row.get("deprecated", "").strip().lower()
                deprecated = deprecated_str in ("true", "1", "yes", "y", "t")

                # Create ValueSetValue
                value = ValueSetValue(
                    accession=str(row["accession"]),
                    valueset=valueset_accession,
                    pURL=purl,
                    label=str(row["label"]),
                    value=str(row["value"]),
                    identical_terms=identical_terms or [],
                    similar_terms=similar_terms or [],
                    definition=str(row["definition"]),
                    full_definition=str(row["full_definition"]),
                    deprecated=deprecated,
                    deprecated_to=deprecated_to or [],
                    additional=additional or {},
                )
                values.append(value)

            except ValidationError as e:
                error_msg = f"Row {idx + 2}: Validation error: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                error_msg = f"Row {idx + 2}: Unexpected error: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        if errors:
            raise ValueError(f"Failed to parse {len(errors)} rows:\n" + "\n".join(errors[:10]))

        logger.info(f"Successfully parsed {len(values)} values")

        # Create ValueSet
        valueset = ValueSet(
            accession=valueset_accession,
            pURL=settings.generate_purl_valueset(valueset_accession),
            definition=valueset_metadata.get("definition", ""),
            full_definition=valueset_metadata.get("full_definition", ""),
            values=values,
        )

        return valueset

    def ingest_csv(
        self,
        csv_path: Path,
        valueset_accession: Optional[str] = None,
        definition: Optional[str] = None,
        full_definition: Optional[str] = None,
    ) -> None:
        """
        Ingest a CSV file into the database.

        Args:
            csv_path: Path to CSV file
            valueset_accession: Optional accession override (defaults to filename)
            definition: Optional short definition
            full_definition: Optional full definition
        """
        # Use filename as accession if not provided
        if valueset_accession is None:
            valueset_accession = csv_path.stem

        # Use defaults if not provided
        if definition is None:
            definition = f"ValueSet: {valueset_accession}"
        if full_definition is None:
            full_definition = f"Full definition for {valueset_accession}"

        metadata = {"definition": definition, "full_definition": full_definition}

        # Load ValueSet from CSV
        valueset = self.load_valueset_from_csv(csv_path, valueset_accession, metadata)

        # Insert into database
        logger.info(f"Inserting ValueSet '{valueset_accession}' into database")
        session = self._get_session()
        try:
            insert_valueset(session, valueset)
            session.commit()
            logger.info(f"Successfully inserted {len(valueset.values)} values")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ingest_directory(
        self, directory: Path, yaml_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Ingest all CSV files from a directory.

        Args:
            directory: Directory containing CSV files
            yaml_metadata: Optional dict of per-accession metadata loaded from YAML
        """
        metadata = yaml_metadata or {}
        csv_files = list(directory.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files in {directory}")

        for csv_file in csv_files:
            accession = csv_file.stem
            dataset_metadata = metadata.get(accession, {})
            try:
                self.ingest_csv(
                    csv_path=csv_file,
                    valueset_accession=accession,
                    definition=dataset_metadata.get("definition"),
                    full_definition=dataset_metadata.get("full_definition"),
                )
            except Exception as e:
                logger.error(f"Failed to ingest {csv_file}: {e}")
                continue

    def close(self) -> None:
        """Dispose of the database engine."""
        self._engine.dispose()

    def __enter__(self) -> "CSVLoader":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
