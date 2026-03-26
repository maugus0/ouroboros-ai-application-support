"""Tests for SOP repository version-tree queries."""

import pytest

from app.repositories.mysql_sop_repo import SOPRepository


@pytest.mark.asyncio
async def test_get_versions_includes_sibling_branches_under_shared_root():
    """Starting from a middle node, descendants of the root (e.g. siblings) must be included."""
    repo = SOPRepository()

    rows_by_id = {
        "mid": {"id": "mid", "parent_sop_id": "root", "version": 2, "created_at": None},
        "root": {"id": "root", "parent_sop_id": None, "version": 1, "created_at": None},
    }

    async def fake_one(_q: str, params: tuple) -> dict | None:
        return rows_by_id.get(params[0])

    children_by_parent = {
        "root": [
            {"id": "mid", "parent_sop_id": "root", "version": 2, "created_at": None},
            {"id": "sib", "parent_sop_id": "root", "version": 2, "created_at": None},
        ],
        "mid": [],
        "sib": [],
    }

    async def fake_query(_q: str, params: tuple) -> list:
        return children_by_parent.get(params[0], [])

    repo.execute_one = fake_one  # type: ignore[method-assign]
    repo.execute_query = fake_query  # type: ignore[method-assign]

    out = await repo.get_versions("mid")
    ids = {r["id"] for r in out}
    assert ids == {"root", "mid", "sib"}
