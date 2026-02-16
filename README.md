# ValueSet API

An API for managing controlled vocabularies.

## Overview

ValueSet API provides a standardized way to manage and serve controlled vocabularies (ontologies) for semantic annotation.

## Quick Start

### 1. Installation

```bash
# Install dependencies with Poetry
poetry install

# Or using pip
pip install -e .
```

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Key settings:
| Setting | Default | Description |
|---|---|---|
| `DATABASE_PATH` | `valueset.db` | Path to the SQLite database file |
| `ENABLE_DOCS` | `True` | Enable Swagger UI at `/docs` |
| `ENABLE_REDOC` | `True` | Enable ReDoc UI at `/redoc` |
| `ENABLE_BROWSE` | `True` | Enable ValueSet Browser at `/browse` |
| `PURL_BASE_URL` | `https://api.example.com` | Base URL for generated pURLs |
```

### 3. Ingest Sample Data

```bash
# Ingest the sample CSV file
poetry run ingest-csv tests/fixtures/appris.csv \
  --accession appris \
  --definition "Classification of APPRIS" \
  --full-definition "Classifications from the APPRIS data set"
```

### 4. Run the API Server

```bash
# Development mode (with auto-reload)
poetry run uvicorn app.main:app --reload

# Production mode
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Once live you can use the browse value sets endpoint to inspect the available value sets and contents

### 5. Access the API

- **Browse Value Sets**: http://localhost:8000/browse
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Terms

- `GET /term/{accession}` - Retrieve a single term by its accession
  ```bash
  curl http://localhost:8000/term/appris.principal1.1
  ```

### ValueSets

- `GET /list/valuesets` - List all ValueSets (metadata only)
  ```bash
  curl http://localhost:8000/list/valuesets
  ```

- `GET /list/valuesets/{namespace}` - Get complete ValueSet with all terms
  ```bash
  # Exclude deprecated terms (default)
  curl http://localhost:8000/list/valuesets/appris
  
  # Include deprecated terms
  curl http://localhost:8000/list/valuesets/appris?deprecated=true
  ```

### Health & Monitoring

- `GET /health` - Health check for monitoring
- `GET /service-info` - GA4GH-compliant service information

## Data Model

### ValueSet Schema

```json
{
  "accession": "appris",
  "pURL": "https://api.example.com/valuesets/appris",
  "definition": "Classification of APPRIS",
  "full_definition": "Classification...",
  "values": [...]
}
```

### ValueSetValue Schema

```json
{
  "accession": "appris.principal1.1",
  "valueset": "appris",
  "pURL": "https://api.example.com/terms/appris.principal1.1",
  "label": "APPRIS P1",
  "value": "apprisp1",
  "identical_terms": [],
  "similar_terms": [],
  "definition": "",
  "full_definition": "Detailed description...",
  "deprecated": false,
  "deprecated_to": [],
  "additional": {}
}
```

## CSV Format

Create ValueSets in CSV with these columns:

| Column | Required | Type | Description |
|--------|----------|------|-------------|
| `accession` | ✅ | string | Unique identifier (e.g., "appris.principal1.1") |
| `label` | ✅ | string | Human-readable display name |
| `value` | ✅ | string | Machine-readable value |
| `definition` | ✅ | string | Short description |
| `full_definition` | ✅ | string | Comprehensive description |
| `identical_terms` | ❌ | JSON array | URIs of identical terms |
| `similar_terms` | ❌ | JSON array | URIs of similar terms |
| `deprecated` | ❌ | boolean | Is term deprecated? |
| `deprecated_to` | ❌ | JSON array | Replacement term accessions |
| `additional` | ❌ | JSON object | Custom attributes |
| `pURL` | ❌ | URL | Permanent URL (auto-generated if omitted) |

### Example CSV

```csv
accession,label,value,identical_terms,similar_terms,definition,full_definition,deprecated,deprecated_to,additional
appris.principal1.1,APPRIS P1,apprisp1,,,Transcript model containing a protein isoform classified as PRINCIPAL:1 by APPRIS. ,Transcript(s) expected to code for the main functional protein isoform based solely on the core modules in the APPRIS. Multiple PRINCIPAL:1 transcripts can be called in a gene due to alterative splicing within UTRs. ,false,,
appris.principal2.1,APPRIS P2,apprisp2,,,Transcript model containing a protein isoform classified as PRINCIPAL:2 by APPRIS. ,"When the APPRIS modules cannot clearly select a single protein-coding isoform for a PRINCIPAL:1 transcript out of a pool of multiple candidates, a PRINCIPAL:2 model may instead be selected. This is model containing a protein isoform with a raw TRIFID score that is substantially higher than that for all other candidate models. ",false,,
```

## CSV Ingestion

### Manual Ingestion

```bash
# Ingest a single CSV file
poetry run ingest-csv path/to/valueset.csv
```

### YAML Metadata Ingestion
Instead of providing metadata via CLI flags, you can use a YAML file to manage metadata for one or more ValueSets.

1. Create a `metadata.yml` file:
```yaml
appris:
  definition: "APPRIS Transcript Classifications"
  full_definition: |
    Classifications of transcript models based on core modules 
    in the APPRIS dataset.
```

2. Ingest using the `--metadata` (or `-m`) flag:
```bash
poetry run ingest-csv tests/fixtures/appris.csv --metadata metadata.yml
```

Precedence order for metadata:
1. Direct CLI flags (`--definition`, etc.)
2. YAML file entries
3. Hardcoded defaults (e.g., filename-based accession)

### Bulk Ingestion
Ingest all CSV files in a directory:
```bash
ingest-csv --directory path/to/valuesets/
```
If a metadata file is provided with `--directory`, it will be used to look up metadata for each CSV file (matching by filename).

```bash
# With custom metadata
poetry run ingest-csv path/to/valueset.csv \
  --accession my_valueset \
  --definition "Short description" \
  --full-definition "Long description"

# Ingest all CSVs from a directory
poetry run ingest-csv --directory path/to/valuesets/

# Use custom database path
poetry run ingest-csv path/to/valueset.csv --db-path /data/valueset.db
```

### Automated Ingestion (CI/CD)

1. Export CSV from Google Sheets
2. Create pull request with CSV file in `valuesets/` directory
3. Merge to `main` branch
4. GitHub Actions automatically:
   - Validates and ingests CSV
   - Builds database
   - Creates Docker image with embedded database

## Docker

### Build Image

```bash
docker build -t valueset-api:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e PURL_BASE_URL=https://api.example.com \
  valueset-api:latest
```

### Docker Compose (Development)

```bash
docker-compose up
```

## Testing

### Run All Tests

```bash
poetry run pytest
```

### Run with Coverage

```bash
poetry run pytest --cov=app --cov=ingestion --cov-report=html
```

### Run Specific Tests

```bash
# Test models
poetry run pytest tests/test_models.py

# Test API endpoints
poetry run pytest tests/test_api.py

# Test CSV ingestion
poetry run pytest tests/test_ingestion.py
```

## Code Quality

### Linting

```bash
# Format code with Black
poetry run black app/ ingestion/ tests/

# Sort imports with isort
poetry run isort app/ ingestion/ tests/

# Lint with Ruff
poetry run ruff check app/ ingestion/ tests/

# Type check with mypy
poetry run mypy app/ ingestion/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## Monitoring

### Health Checks

The `/health` endpoint is used for external monitoring systems

