"""Versioned application endpoints (orchestrator-friendly paths)."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.checklist_models import ChecklistCreateRequest, ChecklistItemUpdate, ChecklistResponse
from app.models.common_models import StandardResponse
from app.models.sop_models import SOPGenerateRequest, SOPResponse
from app.services.checklist_service import ChecklistService
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


@router.post("/checklist", response_model=StandardResponse[ChecklistResponse])
async def create_application_checklist_v1(body: ChecklistCreateRequest):
    """Create an application checklist (standard items + optional program-specific rows)."""
    service = ChecklistService()
    data = await service.create_checklist(body)
    return StandardResponse(success=True, message="Checklist created", data=data)


@router.get("/checklist/{user_id}", response_model=StandardResponse[list[ChecklistResponse]])
async def list_application_checklists_v1(user_id: str):
    """List all application checklists for a user."""
    service = ChecklistService()
    data = await service.list_for_user(user_id)
    return StandardResponse(success=True, message="OK", data=data)


@router.put(
    "/checklist/{checklist_id}/item/{item_id}",
    response_model=StandardResponse[ChecklistResponse],
)
async def update_application_checklist_item_v1(
    checklist_id: str,
    item_id: str,
    update: ChecklistItemUpdate,
):
    """Update a single checklist item status (pending / in_progress / completed)."""
    service = ChecklistService()
    data = await service.update_item(checklist_id, item_id, update.status)
    return StandardResponse(success=True, message="Checklist updated", data=data)
