"""Cover letter generation and retrieval endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.common_models import StandardResponse
from app.models.cover_letter_models import CoverLetterGenerateRequest, CoverLetterResponse
from app.repositories.mysql_cover_letter_repo import CoverLetterRepository
from app.services.cover_letter_service import CoverLetterService
from app.utils.db_rows import cover_letter_row_to_dict
from app.utils.exceptions import NotFoundError

router = APIRouter(
    prefix="/cover-letters",
    tags=["Cover Letters"],
    dependencies=[Depends(require_service_token)],
)


@router.post("/generate", response_model=StandardResponse[CoverLetterResponse])
async def generate_cover_letter(request: CoverLetterGenerateRequest):
    """Generate a cover letter tailored to target program/scholarship."""
    service = CoverLetterService()
    data = await service.generate(request)
    return StandardResponse(success=True, message="Cover letter generated", data=data)


@router.get("/{letter_id}", response_model=StandardResponse[CoverLetterResponse])
async def get_cover_letter(letter_id: str):
    """Retrieve a generated cover letter by ID."""
    repo = CoverLetterRepository()
    row = await repo.get_by_id(letter_id)
    if not row:
        raise NotFoundError("Cover letter")
    return StandardResponse(success=True, message="OK", data=CoverLetterResponse(**cover_letter_row_to_dict(row)))
