"""Database layer using SQLAlchemy ORM for ValueSet storage."""

from typing import List, Optional

from pydantic import HttpUrl
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import ValueSet, ValueSetSummary, ValueSetValue
from app.schema import Base, ValueSetORM, ValueSetValueORM

# Global engine and session factory (will be initialized on first use)
_engine = None
_SessionLocal = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{settings.database_path}",
            connect_args={"check_same_thread": False},
            echo=settings.debug,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def init_db() -> None:
    """Initialize database and create all tables."""
    Base.metadata.create_all(bind=get_engine())


def get_session() -> Session:
    """Get a new database session."""
    SessionLocal = get_session_factory()
    return SessionLocal()


def get_term(session: Session, accession: str) -> Optional[ValueSetValue]:
    """
    Retrieve a single term by accession.

    Args:
        session: SQLAlchemy session
        accession: Term accession to retrieve

    Returns:
        ValueSetValue if found, None otherwise
    """
    stmt = select(ValueSetValueORM).where(ValueSetValueORM.accession == accession)
    result = session.execute(stmt).scalar_one_or_none()

    if not result:
        return None

    return _orm_to_valueset_value(result)


def list_valuesets(session: Session) -> List[ValueSetSummary]:
    """
    List all available ValueSets (metadata only).

    Args:
        session: SQLAlchemy session

    Returns:
        List of ValueSetSummary objects
    """
    stmt = select(ValueSetORM).order_by(ValueSetORM.accession)
    results = session.execute(stmt).scalars().all()

    # Fetch all term counts in a single query instead of lazy-loading per ValueSet
    count_stmt = select(
        ValueSetValueORM.valueset,
        func.count(ValueSetValueORM.accession).label("count"),
    ).group_by(ValueSetValueORM.valueset)
    counts = {row.valueset: row.count for row in session.execute(count_stmt)}

    summaries = []
    for vs in results:
        summaries.append(
            ValueSetSummary(
                accession=vs.accession,
                pURL=HttpUrl(vs.purl),
                definition=vs.definition,
                full_definition=vs.full_definition,
                value_count=counts.get(vs.accession, 0),
            )
        )

    return summaries


def get_valueset(
    session: Session, namespace: str, include_deprecated: bool = False
) -> Optional[ValueSet]:
    """
    Get a complete ValueSet with all its terms.

    Args:
        session: SQLAlchemy session
        namespace: ValueSet accession/namespace
        include_deprecated: Whether to include deprecated terms

    Returns:
        ValueSet if found, None otherwise
    """
    # Get ValueSet with all values
    stmt = select(ValueSetORM).where(ValueSetORM.accession == namespace)
    vs = session.execute(stmt).scalar_one_or_none()

    if not vs:
        return None

    # Filter values based on deprecated flag
    if include_deprecated:
        values = [_orm_to_valueset_value(v) for v in vs.values]
    else:
        values = [_orm_to_valueset_value(v) for v in vs.values if v.deprecated == 0]

    # Sort by label
    values.sort(key=lambda x: x.label)

    return ValueSet(
        accession=vs.accession,
        pURL=HttpUrl(vs.purl),
        definition=vs.definition,
        full_definition=vs.full_definition,
        values=values,
    )


def insert_valueset(session: Session, valueset: ValueSet) -> None:
    """
    Insert a ValueSet and its terms.

    Args:
        session: SQLAlchemy session
        valueset: ValueSet to insert
    """
    # Check if valueset already exists
    existing = session.get(ValueSetORM, valueset.accession)
    if existing:
        # Delete existing to replace
        session.delete(existing)
        session.flush()

    # Create new ValueSet ORM object
    vs_orm = ValueSetORM(
        accession=valueset.accession,
        purl=str(valueset.pURL),
        definition=valueset.definition,
        full_definition=valueset.full_definition,
    )

    # Create ValueSetValue ORM objects
    for value in valueset.values:
        value_orm = ValueSetValueORM(
            accession=value.accession,
            valueset=value.valueset,
            purl=str(value.pURL) if value.pURL else None,
            label=value.label,
            value=value.value,
            definition=value.definition,
            full_definition=value.full_definition,
            deprecated=1 if value.deprecated else 0,
        )

        # Set JSON fields using helper methods
        value_orm.set_identical_terms([str(url) for url in value.identical_terms])
        value_orm.set_similar_terms([str(url) for url in value.similar_terms])
        value_orm.set_deprecated_to(value.deprecated_to)
        value_orm.set_additional(value.additional)

        vs_orm.values.append(value_orm)

    session.add(vs_orm)


def health_check(session: Session) -> bool:
    """
    Check if database is accessible.

    Args:
        session: SQLAlchemy session

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        session.execute(select(1))
        return True
    except Exception:
        return False


def _orm_to_valueset_value(orm: ValueSetValueORM) -> ValueSetValue:
    """
    Convert ORM model to Pydantic model.

    Args:
        orm: ValueSetValueORM instance

    Returns:
        ValueSetValue Pydantic model
    """
    return ValueSetValue(
        accession=orm.accession,
        valueset=orm.valueset,
        pURL=HttpUrl(orm.purl) if orm.purl else None,
        label=orm.label,
        value=orm.value,
        identical_terms=[HttpUrl(url) for url in orm.get_identical_terms()],
        similar_terms=[HttpUrl(url) for url in orm.get_similar_terms()],
        definition=orm.definition,
        full_definition=orm.full_definition,
        deprecated=bool(orm.deprecated),
        deprecated_to=orm.get_deprecated_to(),
        additional=orm.get_additional(),
    )
