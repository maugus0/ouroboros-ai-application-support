"""Fixtures for LLM tests."""

from pathlib import Path

import pytest

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@pytest.fixture
def mock_sop_context() -> dict:
    """Provides a realistic mock context for SOP generation prompts."""
    return {
        "student_name": "Jane Doe",
        "target_program": "Master of Science in Computer Science",
        "university": "Stanford University",
        "degree_level": "master",
        "field_of_study": "Computer Science",
        "research_interests": "Artificial Intelligence, Machine Learning",
        "relevant_experience": "Software Engineer at Tech Corp for 2 years.",
        "academic_achievements": "Graduated Top 1% from Undergrad.",
        "career_goals": "Become an AI researcher and contribute to safe AI.",
    }


@pytest.fixture
def mock_cover_letter_context() -> dict:
    """Provides a realistic mock context for cover letter generation prompts."""
    return {
        "student_name": "John Smith",
        "target_position": "Software Engineering Intern",
        "company_name": "Google",
        "skills": "Python, Java, React",
        "relevant_experience": "Built a scalable web app during hackathon.",
        "career_goals": "Gain experience in large-scale distributed systems.",
    }


@pytest.fixture
def all_prompt_files() -> list[Path]:
    """Returns a list of all prompt JSON files in the prompts directory."""
    return list(PROMPTS_DIR.glob("*.json"))
