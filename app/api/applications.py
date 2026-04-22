"""Versioned application endpoints (orchestrator-friendly paths)."""

from fastapi import APIRouter, Depends, Query

from app.middleware.service_auth import require_service_token
from app.models.checklist_models import ChecklistCreateRequest, ChecklistItemUpdate, ChecklistResponse
from app.models.common_models import StandardResponse
from app.models.cover_letter_models import CoverLetterGenerateRequest, CoverLetterResponse
from app.models.deadline_models import DeadlineSyncRequest, DeadlineSyncResponse, DeadlineTimelineEntry
from app.models.sop_models import SOPGenerateRequest, SOPResponse
from app.services.checklist_service import ChecklistService
from app.services.cover_letter_service import CoverLetterService
from app.services.deadline_service import DeadlineService
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


@router.post("/generate-cover-letter", response_model=StandardResponse[CoverLetterResponse])
async def generate_cover_letter_v1(request: CoverLetterGenerateRequest):
    """Generate a cover letter under the versioned orchestrator-facing API prefix."""
    service = CoverLetterService()
    data = await service.generate(request)
    return StandardResponse(success=True, message="Cover letter generated", data=data)


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


@router.get("/deadlines/{user_id}", response_model=StandardResponse[list[DeadlineTimelineEntry]])
async def list_application_deadlines_v1(
    user_id: str,
    approaching_days: int = Query(30, ge=1, le=366, description="Highlight window for upcoming items"),
):
    """List deadlines for a user: chronological order, passed vs upcoming, 30-day highlight window."""
    service = DeadlineService()
    data = await service.list_timeline_for_user(user_id, approaching_days=approaching_days)
    return StandardResponse(success=True, message="OK", data=data)


@router.post("/deadlines/sync", response_model=StandardResponse[DeadlineSyncResponse])
async def sync_application_deadlines_v1(body: DeadlineSyncRequest):
    """Extract deadlines from program and scholarship payloads and persist (skip duplicates)."""
    service = DeadlineService()
    data = await service.sync_from_sources(body.user_id, body.programs, body.scholarships)
    return StandardResponse(success=True, message="Deadlines synced", data=data)
