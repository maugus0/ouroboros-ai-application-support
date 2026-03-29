"""Versioned application endpoints (orchestrator-friendly paths)."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.common_models import StandardResponse
from app.models.sop_models import SOPGenerateRequest, SOPResponse
from app.services.sop_service import SOPService

router = APIRouter(
    prefix="/api/v1/applications",
    tags=["Applications v1"],
    dependencies=[Depends(require_service_token)],
)


@router.post("/generate-sop", response_model=StandardResponse[SOPResponse])
async def generate_sop_v1(request: SOPGenerateRequest):
    """Generate a Statement of Purpose (outline → expand → quality review).

    Same pipeline as ``POST /sop/generate``; exposed under the public API prefix.
    """
    service = SOPService()
    data = await service.generate(request)
    return StandardResponse(success=True, message="SOP generated", data=data)
