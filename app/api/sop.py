"""SOP generation and retrieval endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.common_models import StandardResponse
from app.models.sop_models import SOPGenerateRequest, SOPResponse, SOPVersionListResponse
from app.repositories.mysql_sop_repo import SOPRepository
from app.services.sop_service import SOPService
from app.utils.db_rows import sop_row_to_dict
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/sop", tags=["SOP"], dependencies=[Depends(require_service_token)])


@router.post("/generate", response_model=StandardResponse[SOPResponse])
async def generate_sop(request: SOPGenerateRequest):
    """Generate a Statement of Purpose using multi-step LLM pipeline.

    Pipeline: outline -> expand -> quality review
    """
    service = SOPService()
    data = await service.generate(request)
    return StandardResponse(success=True, message="SOP generated", data=data)


@router.get("/versions/{sop_id}", response_model=StandardResponse[SOPVersionListResponse])
async def get_sop_versions(sop_id: str):
    """Retrieve all versions of an SOP (parent chain + descendants)."""
    repo = SOPRepository()
    rows = await repo.get_versions(sop_id)
    if not rows:
        raise NotFoundError("SOP")
    versions = [SOPResponse(**sop_row_to_dict(r)) for r in rows]
    payload = SOPVersionListResponse(sop_id=sop_id, versions=versions, total_versions=len(versions))
    return StandardResponse(success=True, message="OK", data=payload)


@router.get("/{sop_id}", response_model=StandardResponse[SOPResponse])
async def get_sop(sop_id: str):
    """Retrieve a generated SOP by ID."""
    repo = SOPRepository()
    row = await repo.get_by_id(sop_id)
    if not row:
        raise NotFoundError("SOP")
    return StandardResponse(success=True, message="OK", data=SOPResponse(**sop_row_to_dict(row)))
