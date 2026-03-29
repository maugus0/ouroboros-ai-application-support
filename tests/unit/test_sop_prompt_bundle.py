"""SOP prompt bundle versioning."""

from app.llm.sop_prompt_bundle import (
    SOP_EXPANSION_PROMPT_FILE,
    SOP_OUTLINE_PROMPT_FILE,
    SOP_PROMPT_BUNDLE_ID,
    SOP_QUALITY_REVIEW_PROMPT_FILE,
)


def test_bundle_points_at_versioned_files():
    assert SOP_PROMPT_BUNDLE_ID == "sop_bundle_v2"
    assert SOP_OUTLINE_PROMPT_FILE.endswith("_v2.json")
    assert SOP_EXPANSION_PROMPT_FILE.endswith("_v2.json")
    assert SOP_QUALITY_REVIEW_PROMPT_FILE.endswith("_v2.json")
