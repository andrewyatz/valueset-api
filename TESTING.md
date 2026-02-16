# Testing Guide

## Running Tests

The ValueSet API test suite is built on `pytest` and uses a temporary SQLite database for each test run to ensure isolation and reproducibility.

### Run All Tests

```bash
# This will run the entire test suite
poetry run pytest

# With verbose output
poetry run pytest -v
```

### Run Specific Test File

```bash
# Test API endpoints
poetry run pytest tests/test_api.py

# Test CSV ingestion
poetry run pytest tests/test_ingestion.py
```

### Run Specific Test

```bash
poetry run pytest tests/test_api.py::TestHealthEndpoints::test_health_check
```

## Test Coverage

We use `pytest-cov` to track coverage across the application and ingestion pipelines.

```bash
# Generate coverage report
poetry run pytest --cov=app --cov=ingestion --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Structure

```text
tests/
├── conftest.py              # Global fixtures (test DB setup/cleanup)
├── test_models.py           # Pydantic model validation tests
├── test_api.py              # API endpoint integration tests
├── test_ingestion.py        # CSV ingestion pipeline tests
└── fixtures/
    └── appris.csv           # Reference fixture for APPRIS ValueSet
```

## How It Works

### Global Fixtures (`conftest.py`)

The test suite uses several global fixtures to manage the database state:

- **`test_db_path`**: Creates a unique temporary file path for a SQLite database.
- **`test_db_engine`**: Initializes a fresh SQLAlchemy engine, creates the schema (`Base.metadata.create_all`), and overrides the global engine in `app.database`.
- **`test_db_session`**: Provides a scoped SQLAlchemy `Session` for use within tests.

### API Integration Tests

The `client` fixture in `tests/test_api.py` automatically initializes the test database with sample data before each test, allowing you to test endpoints against a known state.

## Writing New Tests

### Unit Tests (Models)

For logic that doesn't require a database, simply import the Pydantic models:

```python
from app.models import ValueSetValue

def test_my_logic():
    val = ValueSetValue(accession="test:1", ...)
    assert val.accession == "test:1"
```

### Integration Tests (API)

To test a new endpoint, use the `client` fixture which provides a FastAPI `TestClient`:

```python
def test_new_endpoint(client):
    response = client.get("/my/new/endpoint")
    assert response.status_code == 200
```

### Ingestion Tests

Use the `temp_db` fixture from `test_ingestion.py` to test parsing logic without affecting the local database:

```python
def test_my_ingestion(temp_db, test_csv_path):
    loader = CSVLoader(db_path=temp_db)
    loader.ingest_csv(test_csv_path)
    # Assert database state...
```

## Debugging

- **Show output**: `poetry run pytest -s` (shows print statements)
- **Stop on fail**: `poetry run pytest -x`
- **Run last failed**: `poetry run pytest --lf`
- **Match names**: `poetry run pytest -k "keyword"`
