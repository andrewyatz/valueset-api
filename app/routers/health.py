"""Router for health and service info endpoints."""

from fastapi import APIRouter, Response, status

from app.config import settings
from app.database import health_check as db_health_check
from app.dependencies import SessionDep
from app.models import HealthResponse, ServiceInfo

router = APIRouter(tags=["Health & Monitoring"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API and database are accessible",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {"application/json": {"example": {"status": "healthy"}}},
        },
        503: {"description": "Service is unhealthy"},
    },
)
async def health_check(session: SessionDep, response: Response) -> HealthResponse:
    """
    Health check endpoint for monitoring.

    Verifies that:
    - The API server is running
    - The database is accessible

    Used for:
    - External monitoring systems

    Args:
        session: Database session dependency
        response: FastAPI response object to set status code

    Returns:
        HealthResponse with status and database backend info
    """
    db_healthy = db_health_check(session)

    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unhealthy")

    return HealthResponse(status="healthy")


@router.get(
    "/service-info",
    response_model=ServiceInfo,
    summary="Service information",
    description="GA4GH-compliant service information endpoint",
    responses={
        200: {
            "description": "Service information",
            "content": {
                "application/json": {
                    "example": {
                        "id": "org.example.valueset",
                        "name": "ValueSet API",
                        "type": {
                            "group": "org.ga4gh",
                            "artifact": "valueset",
                            "version": "1.0.0",
                        },
                        "description": "Healthcare Ontology & Terminology Management System",
                        "organization": {"name": "Your Organization", "url": "https://example.com"},
                        "version": "0.1.0",
                        "environment": "production",
                    }
                }
            },
        }
    },
)
async def service_info() -> ServiceInfo:
    """
    GA4GH-compliant service information endpoint.

    Returns metadata about this service following the GA4GH
    Service Info specification.

    See: https://github.com/ga4gh-discovery/ga4gh-service-info

    Returns:
        ServiceInfo object with service metadata
    """
    return ServiceInfo(
        id=settings.service_id,
        name=settings.app_name,
        description=settings.app_description,
        organization={
            "name": settings.organization_name,
            "url": settings.organization_url,
        },
        version=settings.app_version,
        environment=settings.environment,
    )
