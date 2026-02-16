"""Pytest configuration for running tests with SQLite."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.schema import Base


@pytest.fixture(scope="function")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file path."""
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Delete the file so SQLite can create it fresh
    Path(db_path).unlink()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)
    Path(f"{db_path}-shm").unlink(missing_ok=True)


@pytest.fixture(scope="function")
def test_db_engine(test_db_path: str) -> Generator[Engine, None, None]:
    """Create a test database engine with file-based SQLite."""
    # Create file-based SQLite database for testing
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},  # Allow multi-threaded access
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Override the global engine and session factory in app.database
    import app.database as db_module

    original_engine = db_module._engine
    original_session_local = db_module._SessionLocal

    # Create session factory for test engine
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Set the global engine and session factory to use test database
    db_module._engine = engine
    db_module._SessionLocal = TestSessionLocal

    yield engine

    # Cleanup - restore original engine and session factory first
    db_module._engine = original_engine
    db_module._SessionLocal = original_session_local

    # Then dispose of test engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine: Engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    # Create session from the test engine
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestSessionLocal()

    yield session

    # Cleanup
    session.close()
