"""FastAPI dependencies."""

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session
from app.models import ValueSetValue


def get_db_session() -> Generator[Session, None, None]:
    """Dependency to inject SQLAlchemy session."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_db_session)]


def enrich_term_with_purl(term: ValueSetValue) -> ValueSetValue:
    """
    Enrich a term with pURL if not already present.

    Generates pURL at runtime using configured template.
    """
    if term.pURL is None:
        # Create a new instance with the pURL set properly
        # This ensures Pydantic validates and converts the string to HttpUrl
        term_dict = term.model_dump()
        term_dict["pURL"] = settings.generate_purl_term(term.accession)
        return ValueSetValue(**term_dict)
    return term
