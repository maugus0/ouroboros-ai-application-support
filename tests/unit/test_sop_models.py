"""SOP request model validation."""

import pytest
from pydantic import ValidationError

from app.models.sop_models import SOPGenerateRequest


def test_sop_generate_requires_program_context():
    with pytest.raises(ValidationError, match="program_id or target_program"):
        SOPGenerateRequest(user_id="user-1")


def test_sop_generate_accepts_program_id_only():
    req = SOPGenerateRequest(user_id="user-1", program_id="prog-42")
    assert req.program_id == "prog-42"


def test_sop_generate_accepts_target_program_identifiers():
    for key in ("field_of_study", "university_name", "program_name"):
        req = SOPGenerateRequest(user_id="user-1", target_program={key: "  x  "})
        assert str(req.target_program[key]).strip() == "x"


def test_whitespace_program_id_counts_as_missing():
    with pytest.raises(ValidationError):
        SOPGenerateRequest(user_id="user-1", program_id="   ", target_program={})
