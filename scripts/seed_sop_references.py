"""Seed example SOP references for retrieval-assisted generation."""

import json
import sys
import uuid
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import settings

load_dotenv(ROOT_DIR / ".env")

SAMPLE_REFERENCES = [
    {
        "field_of_study": "Computer Science",
        "degree_level": "master",
        "program_type": "research",
        "quality_rating": "excellent",
        "notes": "Strong research narrative with clear connection between past work and future goals",
        "content": (
            "This is a placeholder for a sample SOP reference. "
            "Replace with actual high-quality SOP examples for your retrieval system. "
            "The content should demonstrate strong academic writing, clear motivation, "
            "and specific alignment with a research program."
        ),
    },
    {
        "field_of_study": "Computer Science",
        "degree_level": "master",
        "program_type": "coursework",
        "quality_rating": "good",
        "notes": "Good balance of academic and industry experience",
        "content": (
            "This is a placeholder for a sample SOP reference. "
            "Replace with actual high-quality SOP examples for your retrieval system. "
            "The content should showcase practical experience alongside academic preparation."
        ),
    },
]


def seed():
    conn = mysql.connector.connect(
        host=settings.get_db_host(),
        port=settings.get_db_port(),
        database=settings.get_db_name(),
        user=settings.get_db_user(),
        password=settings.get_db_password(),
        charset="utf8mb4",
    )
    cursor = conn.cursor()

    for ref in SAMPLE_REFERENCES:
        ref_id = str(uuid.uuid4())
        word_count = len(ref["content"].split())
        cursor.execute(
            """
            INSERT INTO sop_references
            (id, content, word_count, field_of_study, degree_level, program_type, quality_rating, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ref_id,
                ref["content"],
                word_count,
                ref["field_of_study"],
                ref["degree_level"],
                ref["program_type"],
                ref["quality_rating"],
                ref["notes"],
            ),
        )
        print(f"  Seeded reference: {ref['field_of_study']} / {ref['degree_level']} ({ref_id})")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\nSeeded {len(SAMPLE_REFERENCES)} SOP references.")


if __name__ == "__main__":
    seed()
