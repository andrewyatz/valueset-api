"""Router for term-related endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.database import get_term as db_get_term
from app.dependencies import SessionDep, enrich_term_with_purl
from app.models import ValueSetValue

router = APIRouter(prefix="/term", tags=["Terms"])


@router.get(
    "/{accession}",
    response_model=ValueSetValue,
    summary="Get a term by accession",
    description="Retrieve a single term using its fully name-spaced unique identifier",
    responses={
        200: {
            "description": "Term found and returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "accession": "SNOMED:73211009",
                        "valueset": "diabetes_types",
                        "pURL": "https://api.example.com/terms/SNOMED:73211009",
                        "label": "Diabetes mellitus",
                        "value": "diabetes_mellitus",
                        "identical_terms": [],
                        "similar_terms": [],
                        "definition": "A metabolic disorder",
                        "full_definition": "Detailed description...",
                        "deprecated": False,
                        "deprecated_to": [],
                        "additional": {},
                    }
                }
            },
        },
        404: {"description": "Term not found"},
    },
)
async def get_term(accession: str, session: SessionDep) -> ValueSetValue:
    """
    Get a specific term by its accession.

    Args:
        accession: Fully name-spaced unique identifier (e.g., 'SNOMED:73211009')
        session: Database session dependency

    Returns:
        ValueSetValue object with all term details

    Raises:
        HTTPException: 404 if term not found
    """
    term = db_get_term(session, accession)

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Term with accession '{accession}' not found",
        )

    return enrich_term_with_purl(term)
