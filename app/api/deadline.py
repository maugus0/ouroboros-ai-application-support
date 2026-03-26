"""Deadline tracking endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.common_models import StandardResponse
from app.models.deadline_models import DeadlineCreateRequest, DeadlineResponse, DeadlineUpdateRequest

router = APIRouter(prefix="/deadlines", tags=["Deadlines"], dependencies=[Depends(require_service_token)])


@router.get("/{user_id}", response_model=StandardResponse[list[DeadlineResponse]])
async def get_user_deadlines(user_id: str):  # pylint: disable=unused-argument
    """Retrieve all deadlines for a user, ordered by date."""
    return StandardResponse(
        success=False,
        message="Deadline retrieval not yet implemented",
        data=None,
    )


@router.post("/", response_model=StandardResponse[DeadlineResponse])
async def create_deadline(request: DeadlineCreateRequest):  # pylint: disable=unused-argument
    """Create a new deadline entry."""
    return StandardResponse(
        success=False,
        message="Deadline creation not yet implemented",
        data=None,
    )


@router.put("/{deadline_id}", response_model=StandardResponse[DeadlineResponse])
async def update_deadline(deadline_id: str, update: DeadlineUpdateRequest):  # pylint: disable=unused-argument
    """Update an existing deadline entry."""
    return StandardResponse(
        success=False,
        message="Deadline update not yet implemented",
        data=None,
    )
