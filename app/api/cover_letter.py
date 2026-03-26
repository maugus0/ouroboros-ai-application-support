"""Cover letter generation and retrieval endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.common_models import StandardResponse
from app.models.cover_letter_models import CoverLetterGenerateRequest, CoverLetterResponse

router = APIRouter(prefix="/cover-letters", tags=["Cover Letters"], dependencies=[Depends(require_service_token)])


@router.post("/generate", response_model=StandardResponse[CoverLetterResponse])
async def generate_cover_letter(request: CoverLetterGenerateRequest):  # pylint: disable=unused-argument
    """Generate a cover letter tailored to target program/scholarship."""
    return StandardResponse(
        success=False,
        message="Cover letter generation not yet implemented",
        data=None,
    )


@router.get("/{letter_id}", response_model=StandardResponse[CoverLetterResponse])
async def get_cover_letter(letter_id: str):  # pylint: disable=unused-argument
    """Retrieve a generated cover letter by ID."""
    return StandardResponse(
        success=False,
        message="Cover letter retrieval not yet implemented",
        data=None,
    )
