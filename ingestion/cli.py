"""Command-line interface for CSV ingestion."""

import argparse
import logging
import sys
from pathlib import Path

from ingestion.csv_loader import CSVLoader

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest ValueSet CSV files into database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a single CSV file
  ingest-csv path/to/valueset.csv

  # Ingest with custom metadata
  ingest-csv path/to/valueset.csv --accession my_valueset --definition "Short description"

  # Ingest all CSVs from a directory
  ingest-csv --directory path/to/valuesets/

  # Use custom database path
  ingest-csv path/to/valueset.csv --db-path /data/valueset.db
        """,
    )

    # Input arguments
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("csv_file", nargs="?", type=Path, help="Path to CSV file to ingest")
    input_group.add_argument(
        "--directory",
        "-d",
        type=Path,
        help="Directory containing CSV files to ingest",
    )

    # ValueSet metadata
    parser.add_argument(
        "--accession",
        "-a",
        type=str,
        help="ValueSet accession (defaults to filename without extension)",
    )
    parser.add_argument("--definition", type=str, help="Short definition of the ValueSet")
    parser.add_argument("--full-definition", type=str, help="Full definition of the ValueSet")
    parser.add_argument(
        "--metadata",
        "-m",
        type=Path,
        help="Path to YAML file containing ValueSet metadata",
    )

    # Database configuration
    parser.add_argument(
        "--db-path",
        type=str,
        help="Database file path (defaults to valueset.db)",
    )

    # Other options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load YAML metadata if provided
    yaml_metadata = {}
    if args.metadata:
        if not args.metadata.exists():
            logger.error(f"Metadata file not found: {args.metadata}")
            sys.exit(1)
        try:
            import yaml

            with open(args.metadata) as f:
                yaml_metadata = yaml.safe_load(f) or {}
            logger.info(f"Loaded metadata for {len(yaml_metadata)} ValueSets from {args.metadata}")
        except Exception as e:
            logger.error(f"Failed to load YAML metadata: {e}")
            sys.exit(1)

    # Validate inputs
    if args.csv_file:
        if not args.csv_file.exists():
            logger.error(f"CSV file not found: {args.csv_file}")
            sys.exit(1)
        if not args.csv_file.is_file():
            logger.error(f"Path is not a file: {args.csv_file}")
            sys.exit(1)

    if args.directory:
        if not args.directory.exists():
            logger.error(f"Directory not found: {args.directory}")
            sys.exit(1)
        if not args.directory.is_dir():
            logger.error(f"Path is not a directory: {args.directory}")
            sys.exit(1)

    # Create loader
    try:
        with CSVLoader(db_path=args.db_path) as loader:
            if args.csv_file:
                # Ingest single file
                accession = args.accession or args.csv_file.stem
                
                # Fetch metadata from YAML if available
                dataset_metadata = yaml_metadata.get(accession, {})
                
                # Precedence: CLI Arg > YAML File > Hardcoded Default
                definition = (
                    args.definition 
                    or dataset_metadata.get("definition") 
                    or f"ValueSet: {accession}"
                )
                full_definition = (
                    args.full_definition 
                    or dataset_metadata.get("full_definition") 
                    or f"Full definition for {accession}"
                )

                logger.info(f"Ingesting CSV file: {args.csv_file} (accession: {accession})")
                loader.ingest_csv(
                    csv_path=args.csv_file,
                    valueset_accession=accession,
                    definition=definition,
                    full_definition=full_definition,
                )
                logger.info("Successfully ingested CSV file")

            elif args.directory:
                # Ingest directory
                logger.info(f"Ingesting all CSV files from: {args.directory}")
                loader.ingest_directory(args.directory, yaml_metadata=yaml_metadata)
                logger.info("Successfully ingested CSV files from directory")

    except Exception as e:
        logger.error(f"✗ Ingestion failed: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
