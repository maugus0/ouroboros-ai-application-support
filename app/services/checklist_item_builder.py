"""Standard application checklist items and program-requirement extraction (rule-based)."""

import re
from typing import Any

# (regex pattern, description, category, priority)
_PROGRAM_REQUIREMENT_PATTERNS: list[tuple[re.Pattern[str], str, str, str]] = [
    (
        re.compile(
            r"\bGRE\b|Graduate\s+Record\s+Exam|GRE\s+General",
            re.IGNORECASE,
        ),
        "Official GRE General scores (send via ETS)",
        "testing",
        "high",
    ),
    (
        re.compile(r"\bGMAT\b|Graduate\s+Management\s+Admission", re.IGNORECASE),
        "Official GMAT scores",
        "testing",
        "high",
    ),
    (
        re.compile(
            r"\bTOEFL\b|\bIELTS\b|\bDuolingo\b|\bPTE\b|English\s+proficiency|language\s+proficiency",
            re.IGNORECASE,
        ),
        "English proficiency test scores (TOEFL / IELTS / equivalent)",
        "testing",
        "high",
    ),
    (
        re.compile(r"\bportfolio\b|work\s+samples?|design\s+portfolio", re.IGNORECASE),
        "Portfolio or work samples (program-specific)",
        "documents",
        "medium",
    ),
    (
        re.compile(r"writing\s+sample|sample\s+of\s+written", re.IGNORECASE),
        "Writing sample",
        "statements",
        "high",
    ),
    (
        re.compile(r"research\s+statement|research\s+proposal", re.IGNORECASE),
        "Research statement or proposal",
        "statements",
        "high",
    ),
    (
        re.compile(r"diversity\s+statement|personal\s+history", re.IGNORECASE),
        "Diversity or personal history statement (if required)",
        "statements",
        "medium",
    ),
    (
        re.compile(r"\bWES\b|credential\s+eval|transcript\s+eval", re.IGNORECASE),
        "Credential evaluation (e.g. WES) for international transcripts",
        "documents",
        "high",
    ),
    (
        re.compile(r"video\s+essay|recorded\s+interview|kira\s+talent", re.IGNORECASE),
        "Video essay or recorded interview (if required)",
        "other",
        "medium",
    ),
    (
        re.compile(r"\bCV\b|\bresume\b|curriculum\s+vitae", re.IGNORECASE),
        "",
        "",
        "",
    ),  # skip — covered by standard items
]


def standard_checklist_items() -> list[dict[str, Any]]:
    """Baseline items for graduate/professional program applications."""
    return [
        {
            "description": "Curriculum vitae (CV) or resume",
            "status": "pending",
            "category": "documents",
            "priority": "high",
        },
        {
            "description": "Official academic transcripts (all institutions attended)",
            "status": "pending",
            "category": "documents",
            "priority": "high",
        },
        {
            "description": "Letters of recommendation (per program count, typically 2–3)",
            "status": "pending",
            "category": "documents",
            "priority": "high",
        },
        {
            "description": "Statement of purpose or personal statement",
            "status": "pending",
            "category": "statements",
            "priority": "high",
        },
        {
            "description": "Application fee payment (if applicable)",
            "status": "pending",
            "category": "fees",
            "priority": "medium",
        },
        {
            "description": "Government-issued ID or passport (if required by the program)",
            "status": "pending",
            "category": "identity",
            "priority": "low",
        },
    ]


def extract_program_specific_items(program_requirements: str) -> list[dict[str, Any]]:
    """Derive extra checklist rows from free-text program requirements (web scrape / portal text)."""
    if not (program_requirements or "").strip():
        return []

    text = program_requirements.strip()
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    for pattern, description, category, priority in _PROGRAM_REQUIREMENT_PATTERNS:
        if not description:
            continue
        if pattern.search(text):
            key = description.lower()
            if key not in seen:
                seen.add(key)
                out.append(
                    {
                        "description": description,
                        "status": "pending",
                        "category": category,
                        "priority": priority,
                    }
                )
    return out


def merge_standard_and_program_items(program_requirements: str | None) -> list[dict[str, Any]]:
    """Standard items plus program-specific lines; de-duplicate by normalized description."""
    base = standard_checklist_items()
    extra = extract_program_specific_items(program_requirements or "")

    seen_norm: set[str] = {_normalize_desc(i["description"]) for i in base}
    merged = list(base)
    for item in extra:
        norm = _normalize_desc(item["description"])
        if norm not in seen_norm:
            seen_norm.add(norm)
            merged.append(item)
    return merged


def _normalize_desc(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def build_default_checklist_items(
    program_requirements: str | None,
    target_program: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Standard + text-derived + structured hints, de-duplicated."""
    merged = merge_standard_and_program_items(program_requirements or "")
    seen_norm = {_normalize_desc(i["description"]) for i in merged}
    for item in items_from_target_program_hints(target_program or {}):
        norm = _normalize_desc(item["description"])
        if norm not in seen_norm:
            seen_norm.add(norm)
            merged.append(item)
    return merged


def items_from_target_program_hints(target_program: dict[str, Any]) -> list[dict[str, Any]]:
    """Optional structured flags from orchestrator (e.g. requires_gre)."""
    if not target_program:
        return []
    out: list[dict[str, Any]] = []
    if target_program.get("requires_gre") is True:
        out.append(
            {
                "description": "Official GRE General scores (send via ETS)",
                "status": "pending",
                "category": "testing",
                "priority": "high",
            }
        )
    if target_program.get("requires_gmat") is True:
        out.append(
            {
                "description": "Official GMAT scores",
                "status": "pending",
                "category": "testing",
                "priority": "high",
            }
        )
    if target_program.get("requires_english_test") is True:
        out.append(
            {
                "description": "English proficiency test scores (TOEFL / IELTS / equivalent)",
                "status": "pending",
                "category": "testing",
                "priority": "high",
            }
        )
    return out
