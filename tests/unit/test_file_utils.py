"""Tests for file utility helpers."""

from app.utils import file_utils


def test_validate_file_extension():
    assert file_utils.validate_file_extension("cv.pdf") is True
    assert file_utils.validate_file_extension("x.exe") is False


def test_get_mime_type():
    assert file_utils.get_mime_type("a.docx") == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
