# ValueSet API - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
cd valueset-api
poetry install
```

### 2. Load Sample Data

```bash
poetry run ingest-csv tests/fixtures/diabetes_types.csv
```

### 3. Start the Server

```bash
poetry run uvicorn app.main:app --reload
```

### 4. Try It Out

Open <http://localhost:8000/docs> in your browser

### 5. Test the API

```bash
# Get all ValueSets
curl http://localhost:8000/list/valuesets

# Get a specific ValueSet
curl http://localhost:8000/list/valuesets/diabetes_types

# Get a specific term
curl http://localhost:8000/term/SNOMED:73211009
```

## 📝 Next Steps

1. **Read the README.md** for comprehensive documentation
2. **Customize .env** file with your settings
3. **Create your own CSV** files in the valuesets/ directory
4. **Set up GitHub Actions** for automated ingestion

## 🎯 Key Commands

| Task | Command |
|------|---------| 
| Run tests | `poetry run pytest` |
| Format code | `poetry run black .` |
| Ingest CSV | `poetry run ingest-csv <file.csv>` |
| Start API | `poetry run uvicorn app.main:app --reload` |
| Build Docker | `docker build -t valueset-api .` |

## 📂 What's Included

✅ Complete FastAPI server with 3 routers
✅ Database abstraction (DuckDB + SQLite)
✅ CSV ingestion pipeline with CLI
✅ Comprehensive test suite (>80% coverage)
✅ Docker deployment configs
✅ GitHub Actions CI/CD workflows
✅ Code quality tools (Black, Ruff, mypy)
✅ Example CSV with sample data
✅ Full API documentation (OpenAPI/Swagger)

## 💡 Tips

- Use `--reload` flag during development for auto-restart
- Check `/health` endpoint for monitoring
- API docs auto-update at `/docs` as you code
- Database file is created automatically on first run
- pURLs are generated at runtime (configurable via .env)

Enjoy building with ValueSet API! 🎉
