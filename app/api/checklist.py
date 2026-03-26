"""Application checklist endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.checklist_models import ChecklistCreateRequest, ChecklistItemUpdate, ChecklistResponse
from app.models.common_models import StandardResponse
from app.services.checklist_service import ChecklistService

router = APIRouter(prefix="/checklists", tags=["Checklists"], dependencies=[Depends(require_service_token)])


@router.post("", response_model=StandardResponse[ChecklistResponse])
async def create_checklist(body: ChecklistCreateRequest):
    """Create a new application checklist."""
    service = ChecklistService()
    data = await service.create_checklist(body)
    return StandardResponse(success=True, message="Checklist created", data=data)


@router.get("/{user_id}", response_model=StandardResponse[list[ChecklistResponse]])
async def get_user_checklists(user_id: str):
    """Retrieve all checklists for a user."""
    service = ChecklistService()
    data = await service.list_for_user(user_id)
    return StandardResponse(success=True, message="OK", data=data)


@router.put("/{checklist_id}/items/{item_id}", response_model=StandardResponse[ChecklistResponse])
async def update_checklist_item(checklist_id: str, item_id: str, update: ChecklistItemUpdate):
    """Update status of a single checklist item."""
    service = ChecklistService()
    data = await service.update_item(checklist_id, item_id, update.status)
    return StandardResponse(success=True, message="Checklist updated", data=data)
