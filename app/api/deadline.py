"""Deadline tracking endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.common_models import StandardResponse
from app.models.deadline_models import DeadlineCreateRequest, DeadlineResponse, DeadlineUpdateRequest
from app.services.deadline_service import DeadlineService

router = APIRouter(prefix="/deadlines", tags=["Deadlines"], dependencies=[Depends(require_service_token)])


@router.post("", response_model=StandardResponse[DeadlineResponse])
async def create_deadline(request: DeadlineCreateRequest):
    """Create a new deadline entry."""
    service = DeadlineService()
    data = await service.create(request)
    return StandardResponse(success=True, message="Deadline created", data=data)


@router.get("/{user_id}", response_model=StandardResponse[list[DeadlineResponse]])
async def get_user_deadlines(user_id: str):
    """Retrieve all deadlines for a user, ordered by date."""
    service = DeadlineService()
    data = await service.list_for_user(user_id)
    return StandardResponse(success=True, message="OK", data=data)


@router.put("/{deadline_id}", response_model=StandardResponse[DeadlineResponse])
async def update_deadline(deadline_id: str, update: DeadlineUpdateRequest):
    """Update an existing deadline entry."""
    service = DeadlineService()
    data = await service.update(deadline_id, update)
    return StandardResponse(success=True, message="Deadline updated", data=data)
