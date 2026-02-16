"""Router for ValueSet-related endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, Query, status

from app.config import settings
from app.database import get_valueset as db_get_valueset
from app.database import list_valuesets as db_list_valuesets
from app.dependencies import SessionDep, enrich_term_with_purl
from app.models import ValueSet, ValueSetSummary

router = APIRouter(prefix="/list", tags=["ValueSets"])


@router.get(
    "/valuesets",
    response_model=List[ValueSetSummary],
    summary="List all ValueSets",
    description="Retrieve metadata for all available ValueSets (without term lists)",
    responses={
        200: {
            "description": "List of all ValueSets",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "accession": "diabetes_types",
                            "pURL": "https://api.example.com/valuesets/diabetes_types",
                            "definition": "Classification of diabetes mellitus types",
                            "full_definition": "Comprehensive classification...",
                            "value_count": 5,
                        }
                    ]
                }
            },
        }
    },
)
async def list_valuesets(session: SessionDep) -> List[ValueSetSummary]:
    """
    List all available ValueSets.

    Returns metadata only (accession, pURL, definitions, term count)
    without the full list of terms. Use /list/valuesets/{namespace} to
    get complete ValueSet with all terms.

    Args:
        session: Database session dependency

    Returns:
        List of ValueSetSummary objects
    """
    return db_list_valuesets(session)


@router.get(
    "/valuesets/{namespace}",
    response_model=ValueSet,
    summary="Get a complete ValueSet",
    description="Retrieve a ValueSet with all its terms by namespace",
    responses={
        200: {
            "description": "Complete ValueSet with all terms",
            "content": {
                "application/json": {
                    "example": {
                        "accession": "diabetes_types",
                        "pURL": "https://api.example.com/valuesets/diabetes_types",
                        "definition": "Classification of diabetes mellitus types",
                        "full_definition": "Comprehensive classification...",
                        "values": [
                            {
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
                        ],
                    }
                }
            },
        },
        404: {"description": "ValueSet not found"},
    },
)
async def get_valueset(
    namespace: str,
    session: SessionDep,
    deprecated: bool = Query(
        default=False,
        description="Include deprecated terms in the response",
    ),
) -> ValueSet:
    """
    Get a complete ValueSet with all its terms.

    Args:
        namespace: ValueSet namespace/accession identifier
        deprecated: Whether to include deprecated terms (default: False)
        session: Database session dependency

    Returns:
        Complete ValueSet object with all terms

    Raises:
        HTTPException: 404 if ValueSet not found
    """
    valueset = db_get_valueset(session, namespace, include_deprecated=deprecated)

    if valueset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ValueSet with namespace '{namespace}' not found",
        )

    # Enrich all terms with pURLs if not present
    valueset.values = [enrich_term_with_purl(term) for term in valueset.values]

    # Ensure ValueSet pURL is set - recreate object to ensure proper validation
    if not valueset.pURL or str(valueset.pURL) == "":
        valueset_dict = valueset.model_dump()
        valueset_dict["pURL"] = settings.generate_purl_valueset(valueset.accession)
        valueset = ValueSet(**valueset_dict)

    return valueset
