"""LLMOps tests for fixture PII guard behavior."""

from scripts.check_pii import scan_file


def test_pii_guard_ignores_synthetic_numeric_fixture_ids(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "id": "123456789",
  "program_id": "123456789012",
  "zip_code": "123456789"
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert errors == []
    assert findings == []


def test_pii_guard_still_flags_vn_national_id_in_sensitive_fields(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "student_name": "Jane Example",
  "national_id": "123456789"
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert errors == []
    assert findings == [(4, "VN CCCD/CMND")]
