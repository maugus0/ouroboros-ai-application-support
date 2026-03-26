"""SOP generation and retrieval endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.common_models import StandardResponse
from app.models.sop_models import SOPGenerateRequest, SOPResponse, SOPVersionListResponse

router = APIRouter(prefix="/sop", tags=["SOP"], dependencies=[Depends(require_service_token)])


@router.post("/generate", response_model=StandardResponse[SOPResponse])
async def generate_sop(request: SOPGenerateRequest):  # pylint: disable=unused-argument
    """Generate a Statement of Purpose using multi-step LLM pipeline.

    Pipeline: outline -> expand -> quality review
    """
    return StandardResponse(
        success=False,
        message="SOP generation not yet implemented",
        data=None,
    )


@router.get("/{sop_id}", response_model=StandardResponse[SOPResponse])
async def get_sop(sop_id: str):  # pylint: disable=unused-argument
    """Retrieve a generated SOP by ID."""
    return StandardResponse(
        success=False,
        message="SOP retrieval not yet implemented",
        data=None,
    )


@router.get("/versions/{sop_id}", response_model=StandardResponse[SOPVersionListResponse])
async def get_sop_versions(sop_id: str):  # pylint: disable=unused-argument
    """Retrieve all versions of an SOP."""
    return StandardResponse(
        success=False,
        message="SOP version history not yet implemented",
        data=None,
    )
